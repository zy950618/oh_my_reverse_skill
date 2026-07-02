#!/usr/bin/env python3
"""Deterministic local-lab CAPTCHA baseline inference.

This script uses only the synthetic local lab action manifest as the baseline
template. It does not call external CAPTCHA providers or solver services.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RUN_ID = "infer-20260701-sample"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def action_offset(actions: list[dict[str, Any]]) -> int:
    down = next(item for item in actions if item.get("kind") == "pointer_down")
    move = next(item for item in actions if item.get("kind") == "pointer_move")
    return int(round(float(move["x"]) - float(down["x"])))


def ensure_package_manifest(root: Path) -> Path:
    manifests = root / "manifests"
    package_manifest = manifests / "package_manifest.json"
    if package_manifest.exists():
        return package_manifest

    model_manifest = read_json(manifests / "model_package_manifest.json")
    files = list(model_manifest.get("files", []))
    files.extend(
        [
            {"role": "sample_predictions", "path": "../inference/sample_predictions.json"},
            {"role": "pass_rate_metrics", "path": "../eval/metrics.json"},
            {"role": "pass_rate_markdown", "path": "../eval/pass_rate_report.md"},
        ]
    )
    model_manifest["files"] = files
    model_manifest["compatibility_alias_for"] = "model_package_manifest.json"
    write_json(package_manifest, model_manifest)
    return package_manifest


def build_predictions(root: Path) -> dict[str, Any]:
    dataset = read_json(root / "manifests" / "dataset_manifest.json")
    action_manifest = read_json(root / "manifests" / "action_manifest.json")
    model = read_json(root / "model" / "sample-model.json")
    actions = action_manifest["actions"]
    predicted_offset = action_offset(actions)

    predictions: list[dict[str, Any]] = []
    for sample in sorted(dataset["samples"], key=lambda item: item["sample_id"]):
        image_path = (root / "manifests" / sample["image_path"]).resolve()
        label_path = (root / "manifests" / sample["label_path"]).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"missing image: {image_path}")
        if not label_path.is_file():
            raise FileNotFoundError(f"missing label: {label_path}")
        predictions.append(
            {
                "sample_id": sample["sample_id"],
                "split": sample["split"],
                "provider": sample["provider"],
                "challenge_type": sample["challenge_type"],
                "image_path": sample["image_path"],
                "prediction_status": "ok",
                "predicted_offset_css_px": predicted_offset,
                "confidence": 1.0,
                "actions": actions,
                "error_modes": [],
            }
        )

    package_manifest = ensure_package_manifest(root)
    return {
        "schema_version": "captcha_sample_predictions/v1",
        "run_id": RUN_ID,
        "model_id": model["model_id"],
        "model_family": model["model_family"],
        "dataset_id": dataset["dataset_id"],
        "prediction_source": "local_action_manifest_template",
        "package_manifest_ref": str(package_manifest.relative_to(root)).replace("\\", "/"),
        "predictions": predictions,
        "capability_boundary": {
            "evidence_scope": "local_lab",
            "third_party_positive_claim": False,
            "remote_solver_api_used": False,
            "provider_token_used": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("sample_predictions.json"))
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else (Path.cwd() / args.output)
    payload = build_predictions(root)
    write_json(output, payload)
    print(json.dumps({"status": "PASS", "output": str(output), "predictions": len(payload["predictions"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
