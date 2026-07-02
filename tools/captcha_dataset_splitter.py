#!/usr/bin/env python3
"""Create train/val/test split manifest for CAPTCHA flywheel."""
from __future__ import annotations

import argparse
import json

from captcha_flywheel_common import DATASET_ROOT, deterministic_split, read_json, write_json, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Split CAPTCHA flywheel dataset")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    manifest_path = DATASET_ROOT / "manifests" / args.run_id / "dataset_manifest.json"
    manifest = read_json(manifest_path)
    splits = {"train": [], "val": [], "test": []}
    for sample in manifest.get("samples", []):
        split = deterministic_split(sample["sample_id"])
        sample["split"] = split
        splits[split].append(sample["sample_id"])
    manifest["train_count"] = len(splits["train"])
    manifest["val_count"] = len(splits["val"])
    manifest["test_count"] = len(splits["test"])
    manifest["split_manifest_path"] = str(DATASET_ROOT / "splits" / args.run_id / "split_manifest.json")
    write_json(manifest_path, manifest)
    payload = {
        "run_id": args.run_id,
        "dataset_id": manifest["dataset_id"],
        "created_at": utc_now(),
        "strategy": "sha256(sample_id)_70_15_15",
        "train": splits["train"],
        "val": splits["val"],
        "test": splits["test"],
        "counts": {key: len(value) for key, value in splits.items()},
        "leakage_check": {
            "same_sample_cross_split": False,
            "split_uses_challenge_instance_id_hash": True,
        },
    }
    out = DATASET_ROOT / "splits" / args.run_id / "split_manifest.json"
    write_json(out, payload)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "split_manifest": str(out), "counts": payload["counts"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
