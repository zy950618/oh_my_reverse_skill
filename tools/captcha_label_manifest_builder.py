#!/usr/bin/env python3
"""Build label manifest for CAPTCHA flywheel samples."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from captcha_flywheel_common import DATASET_ROOT, read_json, write_json, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CAPTCHA flywheel label manifest")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    manifest_path = DATASET_ROOT / "manifests" / args.run_id / "dataset_manifest.json"
    manifest = read_json(manifest_path)
    labels = []
    for sample in manifest.get("samples", []):
        labels.append({
            "sample_id": sample["sample_id"],
            "family": sample["family"],
            "difficulty": sample["difficulty"],
            "label": sample["label"],
            "label_source": sample["label_source"],
            "labeler": "local_flywheel_rule_labeler",
            "solver_may_read_label": False,
            "leakage_sensitive_fields_removed": sample.get("leakage_sensitive_fields_removed") is True,
        })
    payload = {
        "run_id": args.run_id,
        "dataset_id": manifest["dataset_id"],
        "created_at": utc_now(),
        "label_count": len(labels),
        "label_source": "manually_labeled_training_sample",
        "labeler": "local_flywheel_rule_labeler",
        "forbidden_solver_sources": [
            "third_party_captcha_solving_platform",
            "remote_solver_api",
            "paid_human_solver_service",
            "leaked_answer_field",
            "dom_answer",
            "query_expected",
            "server_expected",
            "provider_internal_token",
            "copied_browser_token",
            "copied_clearance_cookie",
        ],
        "allowed_solver_sources": [
            "local_open_source_model",
            "locally_trained_model",
            "image_only_solver",
            "screenshot_crop",
            "instruction_text",
            "allowed_action_schema",
            "public_range_dataset",
            "synthetic_dataset",
            "self_owned_authorized_dataset",
            "manually_labeled_training_sample",
        ],
        "labels": labels,
    }
    out = DATASET_ROOT / "labels" / args.run_id / "label_manifest.json"
    write_json(out, payload)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "label_manifest": str(out), "label_count": len(labels)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
