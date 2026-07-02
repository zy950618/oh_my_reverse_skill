#!/usr/bin/env python3
"""Train a local text CAPTCHA OCR model and compare it with the baseline."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent.parent
RAW_VISION = ROOT / "public-range-evidence" / "raw" / "captcha-vision-lab"
RAW_TRAIN = ROOT / "public-range-evidence" / "raw" / "captcha-model-training"
TEXT_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
VECTOR_SIZE = (24, 32)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_cmd(command: list[str]) -> dict[str, Any]:
    started = utc_now()
    result = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "started_at": started,
        "ended_at": utc_now(),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def ensure_dataset(run_id: str, count: int, adversarial_count: int, seed: int) -> Path:
    manifest = RAW_VISION / run_id / "dataset-manifest.json"
    if manifest.is_file():
        return manifest
    cmd = [
        sys.executable,
        "tools/captcha_vision_dataset_generator.py",
        "--run-id",
        run_id,
        "--count",
        str(count),
        "--adversarial-count",
        str(adversarial_count),
        "--types",
        "text-captcha",
        "slider-captcha",
        "rotate-captcha",
        "click-captcha",
        "multi-image-select",
        "--difficulties",
        "easy",
        "medium",
        "hard",
        "adversarial",
        "--seed",
        str(seed),
    ]
    result = run_cmd(cmd)
    if result["exit_code"] != 0:
        raise SystemExit(result["stderr"] or result["stdout"])
    return manifest


def crop_region(image: Image.Image, char_index: int) -> Image.Image:
    usable_width = 190
    start_x = 8
    cell = usable_width // 5
    return image.crop((start_x + char_index * cell, 8, start_x + (char_index + 1) * cell + 6, 70))


def vectorize(image: Image.Image) -> list[float]:
    gray = ImageOps.grayscale(image).resize(VECTOR_SIZE)
    values = []
    for y in range(VECTOR_SIZE[1]):
        for x in range(VECTOR_SIZE[0]):
            values.append(1.0 - (gray.getpixel((x, y)) / 255.0))
    return values


def add_vec(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def div_vec(a: list[float], value: float) -> list[float]:
    return [x / value for x in a]


def dist(a: list[float], b: list[float]) -> float:
    return sum((x - y) * (x - y) for x, y in zip(a, b))


def split_samples(manifest: dict[str, Any], challenge_type: str = "text-captcha") -> dict[str, list[dict[str, Any]]]:
    splits = {"train": [], "val": [], "test": []}
    for sample in manifest.get("samples", []):
        if sample.get("challenge_type") != challenge_type:
            continue
        split = sample.get("split")
        if split in splits:
            splits[split].append(sample)
    return splits


def train_centroids(samples: list[dict[str, Any]], limit: int | None = None) -> dict[str, Any]:
    sums = {ch: [0.0] * (VECTOR_SIZE[0] * VECTOR_SIZE[1]) for ch in TEXT_CHARS}
    counts = {ch: 0 for ch in TEXT_CHARS}
    selected = samples[:limit] if limit is not None else samples
    for sample in selected:
        image = Image.open(sample["image_path"]).convert("RGB")
        answer = str(sample["answer"])
        for index, ch in enumerate(answer[:5]):
            vec = vectorize(crop_region(image, index))
            sums[ch] = add_vec(sums[ch], vec)
            counts[ch] += 1
    centroids = {
        ch: div_vec(sums[ch], counts[ch]) if counts[ch] else sums[ch]
        for ch in TEXT_CHARS
    }
    return {"centroids": centroids, "counts": counts, "vector_size": list(VECTOR_SIZE)}


def predict_text(image_path: str, model: dict[str, Any]) -> tuple[str, float]:
    image = Image.open(image_path).convert("RGB")
    centroids = model["centroids"]
    output = ""
    margins: list[float] = []
    for index in range(5):
        vec = vectorize(crop_region(image, index))
        ranked = sorted((dist(vec, centroids[ch]), ch) for ch in TEXT_CHARS)
        best, second = ranked[0], ranked[1]
        output += best[1]
        margins.append(max(0.0, second[0] - best[0]))
    confidence = min(1.0, sum(margins) / len(margins) / 8.0) if margins else 0.0
    return output, confidence


def text_accuracy(samples: list[dict[str, Any]], model: dict[str, Any]) -> dict[str, Any]:
    total_chars = correct_chars = correct_seq = 0
    for sample in samples:
        pred, _ = predict_text(sample["image_path"], model)
        answer = str(sample["answer"])
        total_chars += len(answer)
        correct_chars += sum(1 for a, p in zip(answer, pred) if a == p)
        correct_seq += 1 if answer == pred else 0
    return {
        "sample_count": len(samples),
        "char_accuracy": correct_chars / total_chars if total_chars else 0.0,
        "sequence_accuracy": correct_seq / len(samples) if samples else 0.0,
    }


def make_trained_predictions(manifest: dict[str, Any], baseline: dict[str, Any], model: dict[str, Any], output: Path) -> dict[str, Any]:
    by_sample = {item["sample_id"]: item for item in baseline.get("predictions", [])}
    predictions = []
    for sample in manifest.get("samples", []):
        base = dict(by_sample.get(sample["sample_id"], {}))
        if sample.get("challenge_type") == "text-captcha":
            pred, confidence = predict_text(sample["image_path"], model)
            base.update({
                "sample_id": sample["sample_id"],
                "image_path": sample["image_path"],
                "label_path": sample["label_path"],
                "challenge_type": "text-captcha",
                "difficulty": sample["difficulty"],
                "split": sample.get("split"),
                "prediction": pred,
                "confidence": confidence,
                "solver": "trained_centroid_text_ocr",
                "solver_input_sources": ["challenge_image"],
                "label_read_for_prediction": False,
                "dom_read_for_prediction": False,
                "query_param_read_for_prediction": False,
                "metadata_answer_read_for_prediction": False,
                "model_checkpoint_used": str(model["checkpoint_path"]),
            })
        predictions.append(base)
    payload = {
        "run_id": manifest["run_id"],
        "generated_at": utc_now(),
        "manifest_path": str(RAW_VISION / manifest["run_id"] / "dataset-manifest.json"),
        "prediction_count": len(predictions),
        "leakage_claim": {
            "solver_input_sources": ["challenge_image"],
            "label_read_for_prediction": False,
            "dom_read_for_prediction": False,
            "query_param_read_for_prediction": False,
            "metadata_answer_read_for_prediction": False,
        },
        "model_checkpoint_path": str(model["checkpoint_path"]),
        "predictions": predictions,
    }
    write_json(output, payload)
    return payload


def diff_failures(manifest: dict[str, Any], baseline_predictions: dict[str, Any], trained_predictions: dict[str, Any]) -> dict[str, Any]:
    labels = {sample["sample_id"]: sample for sample in manifest.get("samples", []) if sample.get("challenge_type") == "text-captcha"}
    baseline = {item["sample_id"]: item for item in baseline_predictions.get("predictions", []) if item.get("challenge_type") == "text-captcha"}
    trained = {item["sample_id"]: item for item in trained_predictions.get("predictions", []) if item.get("challenge_type") == "text-captcha"}
    improved = []
    regressed = []
    still_failed = []
    for sample_id, sample in labels.items():
        expected = str(sample["answer"])
        before = str(baseline.get(sample_id, {}).get("prediction", ""))
        after = str(trained.get(sample_id, {}).get("prediction", ""))
        before_err = sum(1 for a, p in zip(expected, before) if a != p) + abs(len(expected) - len(before))
        after_err = sum(1 for a, p in zip(expected, after) if a != p) + abs(len(expected) - len(after))
        row = {
            "sample_id": sample_id,
            "difficulty": sample.get("difficulty"),
            "split": sample.get("split"),
            "expected": expected,
            "baseline_prediction": before,
            "trained_prediction": after,
            "baseline_char_errors": before_err,
            "trained_char_errors": after_err,
            "image_path": sample.get("image_path"),
        }
        if after_err < before_err:
            improved.append(row)
        elif after_err > before_err:
            regressed.append(row)
        elif after_err:
            still_failed.append(row)
    return {
        "improved_count": len(improved),
        "regressed_count": len(regressed),
        "still_failed_count": len(still_failed),
        "improved_samples": improved[:40],
        "regressed_samples": regressed[:40],
        "still_failed_samples": still_failed[:40],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train local CAPTCHA text OCR model")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--adversarial-count", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260630)
    args = parser.parse_args()

    run_id = args.run_id
    train_dir = RAW_TRAIN / run_id
    train_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = ensure_dataset(run_id, args.count, args.adversarial_count, args.seed)
    manifest = read_json(manifest_path)

    baseline_predictions_path = RAW_VISION / run_id / "baseline-predictions.json"
    if not baseline_predictions_path.is_file():
        result = run_cmd([sys.executable, "tools/captcha_vision_baseline_solver.py", "--manifest", str(manifest_path)])
        if result["exit_code"] != 0:
            raise SystemExit(result["stderr"] or result["stdout"])
    baseline_predictions = read_json(baseline_predictions_path)
    baseline_metrics_path = train_dir / "baseline-benchmark-metrics.json"
    run_cmd([
        sys.executable,
        "tools/captcha_vision_benchmark.py",
        "--predictions",
        str(baseline_predictions_path),
        "--output",
        str(baseline_metrics_path),
        "--require-threshold-report",
    ])
    baseline_metrics = read_json(baseline_metrics_path)

    splits = split_samples(manifest)
    split_manifest = {
        "run_id": run_id,
        "challenge_type": "text-captcha",
        "train": [sample["sample_id"] for sample in splits["train"]],
        "val": [sample["sample_id"] for sample in splits["val"]],
        "test": [sample["sample_id"] for sample in splits["test"]],
        "counts": {key: len(value) for key, value in splits.items()},
    }
    write_json(train_dir / "split-manifest.json", split_manifest)

    model_config = {
        "model_type": "centroid_glyph_classifier",
        "target": "text-captcha",
        "charset": TEXT_CHARS,
        "vector_size": list(VECTOR_SIZE),
        "input_source": "fixed image regions from challenge image",
        "supervision_source": "train split labels only",
        "forbidden_inference_sources": ["label_path", "metadata answer", "DOM answer", "query expected"],
    }
    write_json(train_dir / "model-config.json", model_config)

    train_samples = splits["train"]
    training_log = []
    model = {}
    for epoch in range(1, 6):
        limit = max(1, math.ceil(len(train_samples) * epoch / 5))
        model = train_centroids(train_samples, limit)
        training_log.append({
            "epoch": epoch,
            "train_samples_seen": limit,
            "train_metrics": text_accuracy(train_samples[:limit], model),
            "val_metrics": text_accuracy(splits["val"], model),
        })
    checkpoint = train_dir / "checkpoints" / "text-ocr-centroid.json"
    model["checkpoint_path"] = str(checkpoint)
    checkpoint_payload = {
        "run_id": run_id,
        "trained_at": utc_now(),
        "model_config_path": str(train_dir / "model-config.json"),
        "model": model,
    }
    write_json(checkpoint, checkpoint_payload)

    trained_predictions_path = RAW_VISION / run_id / "trained-predictions.json"
    trained_predictions = make_trained_predictions(manifest, baseline_predictions, model, trained_predictions_path)
    trained_metrics_path = RAW_VISION / run_id / "benchmark-metrics.json"
    result = run_cmd([
        sys.executable,
        "tools/captcha_vision_benchmark.py",
        "--predictions",
        str(trained_predictions_path),
        "--output",
        str(trained_metrics_path),
        "--require-threshold-report",
    ])
    if result["exit_code"] != 0:
        raise SystemExit(result["stderr"] or result["stdout"])
    trained_metrics = read_json(trained_metrics_path)

    before_after = diff_failures(manifest, baseline_predictions, trained_predictions)
    write_json(train_dir / "failure-before-after.json", before_after)
    training_log_path = train_dir / "training-log.jsonl"
    training_log_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in training_log) + "\n", encoding="utf-8")

    baseline_text = baseline_metrics.get("metrics", {}).get("text-captcha", {})
    trained_text = trained_metrics.get("metrics", {}).get("text-captcha", {})
    comparison = {
        "baseline_metrics_path": str(baseline_metrics_path),
        "trained_metrics_path": str(trained_metrics_path),
        "baseline_text_char_accuracy": baseline_text.get("char_accuracy", 0),
        "trained_text_char_accuracy": trained_text.get("char_accuracy", 0),
        "char_accuracy_delta": trained_text.get("char_accuracy", 0) - baseline_text.get("char_accuracy", 0),
        "baseline_text_sequence_accuracy": baseline_text.get("sequence_accuracy", 0),
        "trained_text_sequence_accuracy": trained_text.get("sequence_accuracy", 0),
        "sequence_accuracy_delta": trained_text.get("sequence_accuracy", 0) - baseline_text.get("sequence_accuracy", 0),
        "improved": trained_text.get("char_accuracy", 0) > baseline_text.get("char_accuracy", 0),
    }
    write_json(train_dir / "baseline-comparison.json", comparison)

    model_eval = {
        "run_id": run_id,
        "model_id": f"{run_id}-text-ocr-centroid",
        "trained": True,
        "model_type": "centroid_glyph_classifier",
        "dataset_manifest_path": str(manifest_path),
        "split_manifest_path": str(train_dir / "split-manifest.json"),
        "model_config_path": str(train_dir / "model-config.json"),
        "checkpoint_path": str(checkpoint),
        "training_log_path": str(training_log_path),
        "validation_metrics": training_log[-1]["val_metrics"],
        "test_metrics": text_accuracy(splits["test"], model),
        "trained_benchmark_metrics_path": str(trained_metrics_path),
        "baseline_comparison": comparison,
        "failure_before_after_path": str(train_dir / "failure-before-after.json"),
        "status": "training_improved" if comparison["improved"] else "training_needed",
        "capability_status": "training_improved" if comparison["improved"] else "training_needed",
    }
    write_json(train_dir / "model-eval.json", model_eval)
    registry_entry = {
        "model_id": model_eval["model_id"],
        "run_id": run_id,
        "checkpoint_path": str(checkpoint),
        "model_type": model_eval["model_type"],
        "status": model_eval["status"],
        "registered_at": utc_now(),
        "promotion_boundary": "local solver improvement only; public action replay and leakage audit still gate promotion",
    }
    write_json(train_dir / "model-registry-entry.json", registry_entry)
    print(json.dumps({
        "status": "PASS",
        "run_id": run_id,
        "trained": True,
        "checkpoint_path": str(checkpoint),
        "model_eval_path": str(train_dir / "model-eval.json"),
        "char_accuracy_delta": comparison["char_accuracy_delta"],
        "model_status": model_eval["status"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
