#!/usr/bin/env python3
"""Benchmark CAPTCHA baseline predictions with Phase 3.1 hardening outputs."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def angle_error(prediction: float, answer: float) -> float:
    delta = abs((prediction - answer) % 360)
    return min(delta, 360 - delta)


def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def label_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {sample["sample_id"]: sample for sample in manifest.get("samples", [])}


def enrich_predictions(predictions: dict[str, Any], labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in predictions.get("predictions", []):
        label = labels[item["sample_id"]]
        row = dict(item)
        row["expected"] = label.get("answer")
        row["expected_offset"] = label.get("offset")
        row["expected_angle"] = label.get("angle")
        row["expected_click_points"] = label.get("click_points")
        row["expected_positive_indices"] = label.get("positive_indices")
        row["label_path"] = label.get("label_path")
        row["transform_pipeline"] = label.get("transform_pipeline")
        row["synthetic"] = label.get("synthetic")
        row["authorized_sample"] = label.get("authorized_sample")
        row["source_scope"] = label.get("source_scope")
        row["error"] = sample_error(row)
        enriched.append(row)
    return enriched


def sample_error(item: dict[str, Any]) -> float | None:
    challenge_type = item["challenge_type"]
    if challenge_type == "text-captcha":
        expected = str(item.get("expected", ""))
        predicted = str(item.get("prediction", ""))
        return float(sum(1 for a, p in zip(expected, predicted) if a != p) + abs(len(expected) - len(predicted)))
    if challenge_type == "slider-captcha":
        expected = item.get("expected_offset") or {}
        predicted = item.get("prediction") or {}
        if not expected or not predicted:
            return None
        return math.hypot(float(predicted.get("x", 0)) - float(expected.get("x", 0)), float(predicted.get("y", 0)) - float(expected.get("y", 0)))
    if challenge_type == "rotate-captcha":
        return angle_error(float(item.get("prediction", 0)), float(item.get("expected_angle", 0)))
    if challenge_type == "click-captcha":
        expected = item.get("expected_click_points") or []
        predicted = item.get("prediction") or []
        if not expected:
            return 0.0
        if not predicted:
            return 999.0
        return mean([min(distance(exp, pred) for pred in predicted) for exp in expected])
    if challenge_type == "multi-image-select":
        expected = set(item.get("expected_positive_indices") or [])
        predicted = set((item.get("prediction") or {}).get("positive_indices") or [])
        return float(len(expected.symmetric_difference(predicted)))
    return None


def text_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_chars = 0
    correct_chars = 0
    correct_seq = 0
    for item in items:
        answer = str(item.get("expected", ""))
        pred = str(item.get("prediction", ""))
        total_chars += len(answer)
        correct_chars += sum(1 for a, p in zip(answer, pred) if a == p)
        correct_seq += 1 if answer == pred else 0
    return {
        "sample_count": len(items),
        "char_accuracy": correct_chars / total_chars if total_chars else 0.0,
        "sequence_accuracy": correct_seq / len(items) if items else 0.0,
    }


def slider_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [float(item["error"]) for item in items if item.get("error") is not None]
    x_errors = [
        abs(float((item.get("prediction") or {}).get("x", 0)) - float((item.get("expected_offset") or {}).get("x", 0)))
        for item in items
    ]
    y_errors = [
        abs(float((item.get("prediction") or {}).get("y", 0)) - float((item.get("expected_offset") or {}).get("y", 0)))
        for item in items
    ]
    return {
        "sample_count": len(items),
        "mean_abs_offset_error": mean(errors),
        "mean_abs_x_error": mean(x_errors),
        "mean_abs_y_error": mean(y_errors),
        "pass_rate_within_3px": sum(1 for value in errors if value <= 3) / len(errors) if errors else 0.0,
        "pass_rate_within_5px": sum(1 for value in errors if value <= 5) / len(errors) if errors else 0.0,
    }


def rotate_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [float(item["error"]) for item in items if item.get("error") is not None]
    return {
        "sample_count": len(items),
        "mean_abs_angle_error": mean(errors),
        "pass_rate_within_3deg": sum(1 for value in errors if value <= 3) / len(errors) if errors else 0.0,
        "pass_rate_within_5deg": sum(1 for value in errors if value <= 5) / len(errors) if errors else 0.0,
        "error_distribution": error_buckets(errors, [3, 5, 10, 20, 45]),
    }


def click_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    tp = 0
    fp = 0
    fn = 0
    distances: list[float] = []
    success = 0
    for item in items:
        expected = list(item.get("expected_click_points") or [])
        predicted = list(item.get("prediction") or [])
        matched: set[int] = set()
        for pred in predicted:
            if not expected:
                fp += 1
                continue
            best_index, best_point = min(enumerate(expected), key=lambda pair: distance(pair[1], pred))
            best_dist = distance(best_point, pred)
            distances.append(best_dist)
            if best_dist <= 8 and best_index not in matched:
                tp += 1
                matched.add(best_index)
            else:
                fp += 1
        fn += max(0, len(expected) - len(matched))
        if len(matched) == len(expected) and len(expected) > 0:
            success += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "sample_count": len(items),
        "target_precision": precision,
        "target_recall": recall,
        "click_distance_mean": mean(distances),
        "click_success_rate": success / len(items) if items else 0.0,
    }


def multi_image_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    tp = fp = fn = exact = 0
    for item in items:
        expected = set(item.get("expected_positive_indices") or [])
        predicted = set((item.get("prediction") or {}).get("positive_indices") or [])
        tp += len(expected & predicted)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        exact += 1 if expected == predicted else 0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "sample_count": len(items),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "exact_match": exact / len(items) if items else 0.0,
    }


def metric_for(challenge_type: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    if challenge_type == "text-captcha":
        return text_metrics(items)
    if challenge_type == "slider-captcha":
        return slider_metrics(items)
    if challenge_type == "rotate-captcha":
        return rotate_metrics(items)
    if challenge_type == "click-captcha":
        return click_metrics(items)
    if challenge_type == "multi-image-select":
        return multi_image_metrics(items)
    return {"sample_count": len(items)}


def error_buckets(errors: list[float], thresholds: list[int]) -> dict[str, int]:
    buckets: dict[str, int] = {}
    lower = 0
    for threshold in thresholds:
        buckets[f"{lower}-{threshold}"] = sum(1 for value in errors if lower < value <= threshold)
        lower = threshold
    buckets[f">{thresholds[-1]}"] = sum(1 for value in errors if value > thresholds[-1])
    return buckets


def grouped(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(str(item.get(key)), []).append(item)
    return groups


def failure_threshold(challenge_type: str) -> float:
    return {
        "text-captcha": 0.0,
        "slider-captcha": 5.0,
        "rotate-captcha": 5.0,
        "click-captcha": 8.0,
    }.get(challenge_type, 0.0)


def failure_rows(items: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        error = item.get("error")
        if error is None:
            continue
        if item["challenge_type"] == "text-captcha":
            failed = str(item.get("expected")) != str(item.get("prediction"))
        else:
            failed = float(error) > failure_threshold(item["challenge_type"])
        if failed:
            rows.append(item)
    rows.sort(key=lambda item: float(item.get("error") or 0), reverse=True)
    return [
        {
            "sample_id": item["sample_id"],
            "challenge_type": item["challenge_type"],
            "difficulty": item["difficulty"],
            "expected": item.get("expected") or item.get("expected_offset") or item.get("expected_angle") or item.get("expected_click_points"),
            "predicted": item.get("prediction"),
            "error": item.get("error"),
            "image_path": item.get("image_path"),
            "label_path": item.get("label_path"),
            "root_cause": root_cause(item),
            "suggested_fix": suggested_fix(item),
            "whether_eval_added": True,
        }
        for item in rows[:limit]
    ]


def root_cause(item: dict[str, Any]) -> str:
    challenge_type = item["challenge_type"]
    difficulty = item["difficulty"]
    if challenge_type == "text-captcha":
        return f"{difficulty} text segmentation/template matching failed under noise, rotation, or sticky glyphs"
    if challenge_type == "slider-captcha":
        return f"{difficulty} low-contrast or distractor gap confused edge/brightness scan"
    if challenge_type == "rotate-captcha":
        return f"{difficulty} red orientation feature degraded by blur, center offset, or symmetric distractor"
    if challenge_type == "click-captcha":
        return f"{difficulty} target component detection missed or merged target regions"
    if challenge_type == "multi-image-select":
        return f"{difficulty} red-cell detector confused target cells with distractors"
    return "unknown"


def suggested_fix(item: dict[str, Any]) -> str:
    challenge_type = item["challenge_type"]
    if challenge_type == "text-captcha":
        return "add connected-component segmentation and train a glyph classifier on hard samples"
    if challenge_type == "slider-captcha":
        return "add template matching with gap-shape priors and reject distractor gaps"
    if challenge_type == "rotate-captcha":
        return "add center estimation and orientation scan over edge maps"
    if challenge_type == "click-captcha":
        return "add color normalization and target/non-target classifier"
    if challenge_type == "multi-image-select":
        return "add grid-aware classifier and hard negative mining for red distractors"
    return "review sample manually"


def leakage_check(predictions: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    violations = []
    for item in predictions.get("predictions", []):
        for key in ("label_read_for_prediction", "dom_read_for_prediction", "query_param_read_for_prediction", "metadata_answer_read_for_prediction"):
            if item.get(key) is not False:
                violations.append({"sample_id": item.get("sample_id"), "field": key})
    return {
        "status": "pass" if not violations else "invalid_leakage",
        "solver_input_sources": predictions.get("leakage_claim", {}).get("solver_input_sources", []),
        "answer_source": manifest.get("leakage_policy", {}).get("solver_prediction_source_required"),
        "violations": violations,
    }


def thresholds() -> dict[str, Any]:
    return {
        "text-captcha": {"easy_char_accuracy_min": 0.10, "hard_char_accuracy_min": 0.01},
        "slider-captcha": {"easy_within_5px_min": 0.60, "hard_nonzero_error_required": True},
        "rotate-captcha": {"easy_within_5deg_min": 0.60, "error_distribution_required": True},
        "click-captcha": {"easy_precision_min": 0.50, "failure_cases_required": True},
        "multi-image-select": {"easy_f1_min": 0.75, "medium_f1_min": 0.55, "hard_f1_min": 0.35},
    }


def write_failure_cards(run_id: str, failure_cases: dict[str, list[dict[str, Any]]]) -> list[str]:
    out_dir = Path("skills-experience") / "captcha-failure-cases"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    written = 0
    for challenge_type, rows in failure_cases.items():
        for row in rows[:20]:
            if written >= 80:
                break
            card_path = out_dir / f"{run_id}-{row['sample_id']}.yaml"
            lines = [
                f"sample_id: {row['sample_id']}",
                f"source_run_id: {run_id}",
                f"challenge_type: {row['challenge_type']}",
                f"difficulty: {row['difficulty']}",
                f"expected: {json.dumps(row['expected'], ensure_ascii=False)}",
                f"predicted: {json.dumps(row['predicted'], ensure_ascii=False)}",
                f"error: {row['error']}",
                f"image_path: {row['image_path']}",
                f"label_path: {row['label_path']}",
                f"root_cause: {row['root_cause']}",
                f"suggested_fix: {row['suggested_fix']}",
                f"whether_eval_added: {str(row['whether_eval_added']).lower()}",
            ]
            card_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            paths.append(str(card_path))
            written += 1
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark CAPTCHA vision predictions")
    parser.add_argument("--predictions")
    parser.add_argument("--run-id")
    parser.add_argument("--manifest")
    parser.add_argument("--previous-run")
    parser.add_argument("--output")
    parser.add_argument("--require-threshold-report", action="store_true")
    args = parser.parse_args()
    if args.run_id and not args.predictions:
        prediction_path = Path("public-range-evidence") / "raw" / "captcha-vision-lab" / args.run_id / "baseline-predictions.json"
    elif args.predictions:
        prediction_path = Path(args.predictions)
    else:
        raise SystemExit("--predictions or --run-id is required")
    predictions = read_json(prediction_path)
    manifest_path = Path(args.manifest) if args.manifest else Path(predictions["manifest_path"])
    manifest = read_json(manifest_path)
    run_id = predictions["run_id"]
    root = prediction_path.parent
    enriched = enrich_predictions(predictions, label_by_id(manifest))
    by_type = grouped(enriched, "challenge_type")
    per_type_metrics = {challenge_type: metric_for(challenge_type, items) for challenge_type, items in by_type.items()}
    per_difficulty_metrics = {
        challenge_type: {
            difficulty: metric_for(challenge_type, difficulty_items)
            for difficulty, difficulty_items in grouped(items, "difficulty").items()
        }
        for challenge_type, items in by_type.items()
    }
    failures = {challenge_type: failure_rows(items, 20) for challenge_type, items in by_type.items()}
    failure_dir = root / "failure-cases-by-type"
    failure_dir.mkdir(parents=True, exist_ok=True)
    for challenge_type, rows in failures.items():
        (failure_dir / f"{challenge_type}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    failure_path = root / "failure-cases.json"
    failure_path.write_text(json.dumps({"run_id": run_id, "generated_at": utc_now(), "failure_cases": failures}, ensure_ascii=False, indent=2), encoding="utf-8")
    per_sample_path = root / "per-sample-predictions.json"
    per_sample_path.write_text(json.dumps({"run_id": run_id, "predictions": enriched}, ensure_ascii=False, indent=2), encoding="utf-8")
    failure_cards = write_failure_cards(run_id, failures)
    previous = {}
    if args.previous_run:
        previous_path = Path(args.previous_run)
        if previous_path.is_file():
            previous = {"previous_run_path": str(previous_path), "loaded": True}
    result = {
        "run_id": run_id,
        "generated_at": utc_now(),
        "manifest_path": str(manifest_path),
        "prediction_path": str(prediction_path),
        "per_sample_predictions_path": str(per_sample_path),
        "metrics": per_type_metrics,
        "per_difficulty_metrics": per_difficulty_metrics,
        "failure_cases_path": str(failure_path),
        "failure_cases_by_type_dir": str(failure_dir),
        "failure_case_counts": {key: len(value) for key, value in failures.items()},
        "failure_experience_cards": failure_cards,
        "leakage_check": leakage_check(predictions, manifest),
        "regression_thresholds": thresholds(),
        "threshold_report_required": bool(args.require_threshold_report),
        "previous_run_comparison": previous or {"previous_run_path": None, "loaded": False, "note": "no previous run supplied"},
        "capability_boundary": "synthetic_algorithm_benchmark_only_not_real_site_positive",
    }
    output_path = Path(args.output) if args.output else root / "benchmark-metrics.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "run_id": run_id, "metrics_path": str(output_path), "failure_cases_path": str(failure_path), "failure_card_count": len(failure_cards)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
