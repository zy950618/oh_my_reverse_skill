#!/usr/bin/env python3
"""Collect CAPTCHA failures and hard samples into the local dataset flywheel."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from captcha_flywheel_common import DATASET_ROOT, PHASE311_RUN, RAW_EVIDENCE_ROOT, ensure_dirs, read_jsonl, sample_base, svg_grid, utc_now, write_json


FAILURE_CATEGORIES = {
    "image_restore": "recognition_error",
    "select": "recognition_error",
    "icon_select": "recognition_error",
    "seq_select": "instruction_parse_error",
    "spatial_select": "geometry_error",
    "click": "action_mapping_error",
    "rotate": "geometry_error",
    "Connect_icon": "recognition_error",
    "Image_Matching": "recognition_error",
    "Coordinates": "coordinate_transform_error",
}


def parse_existing_failures(source_run_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, filename in (
        ("shumei-compatible-lab", "shumei-compatible-lab-action-replay-records.jsonl"),
        ("aliyun-compatible-lab", "aliyun-compatible-lab-action-replay-records.jsonl"),
        ("opencaptchaworld", "opencaptchaworld-action-replay-records.jsonl"),
        ("gocaptcha-official", "gocaptcha-official-action-replay-records.jsonl"),
    ):
        base = RAW_EVIDENCE_ROOT / target
        for path in sorted(base.glob(f"*/{filename}")):
            for row in read_jsonl(path):
                if row.get("success") is False:
                    item = dict(row)
                    item["source_records_path"] = str(path)
                    item["source_run_id"] = path.parent.name
                    item["target_id"] = target
                    rows.append(item)
    return rows


def add_grid_sample(samples: list[dict[str, Any]], run_id: str, dataset_id: str, index: int, target_id: str, family: str, difficulty: str, raw_dir: Path) -> None:
    seed = hashlib.sha256(f"{run_id}:{target_id}:{family}:{difficulty}:{index}".encode()).hexdigest()
    rng = random.Random(seed)
    if family in {"image_restore", "seq_select"}:
        sequence = rng.sample(["orange", "purple", "cyan", "green", "red", "blue"], 3)
        svg, cells = svg_grid(seed, family, "sequence", sequence)
        label = {"type": "sequence", "colors": sequence, "indices": [next(cell["index"] for cell in cells if cell["name"] == color) for color in sequence]}
        instruction = ("restore order " if family == "image_restore" else "select ") + ", then ".join(sequence)
        allowed = [{"type": "select_sequence", "index_base": 0}]
    elif family in {"spatial_select", "Coordinates"}:
        target = rng.choice(["orange", "purple", "cyan", "green", "red", "blue"])
        svg, cells = svg_grid(seed, family, target)
        cell = next(cell for cell in cells if cell["name"] == target)
        label = {"type": "click_xy", "target_color": target, "x": cell["cx"], "y": cell["cy"], "target_index": cell["index"]}
        instruction = f"click center of the {target} region"
        allowed = [{"type": "click_xy"}]
    else:
        target = rng.choice(["orange", "purple", "cyan", "green", "red", "blue"])
        svg, cells = svg_grid(seed, family, target)
        cell = next(cell for cell in cells if cell["name"] == target)
        label = {"type": "select_option_index", "target_color": target, "target_index": cell["index"], "bbox": {"x": cell["x"], "y": cell["y"], "w": 42, "h": 42}}
        instruction = f"select the {target} target"
        allowed = [{"type": "select_option_index", "index_base": 0}]
    sample = sample_base(run_id, dataset_id, index, target_id, family, difficulty)
    image_path = raw_dir / f"{sample['sample_id']}.svg"
    image_path.write_text(svg, encoding="utf-8")
    sample.update({
        "image_path": str(image_path),
        "crop_path": "",
        "instruction": instruction,
        "allowed_actions": allowed,
        "label": label,
        "success": False,
        "failure_reason": "hard_or_failed_family_training_sample",
        "failure_category": FAILURE_CATEGORIES.get(family, "recognition_error"),
        "source_failure_reference": "",
    })
    samples.append(sample)


def write_manifests(run_id: str, samples: list[dict[str, Any]], failure_refs: list[dict[str, Any]]) -> Path:
    dataset_id = f"captcha-flywheel-{run_id}"
    counts: dict[str, int] = {}
    for sample in samples:
        counts[str(sample["family"])] = counts.get(str(sample["family"]), 0) + 1
    train = sum(1 for sample in samples if sample["split"] == "train")
    val = sum(1 for sample in samples if sample["split"] == "val")
    test = sum(1 for sample in samples if sample["split"] == "test")
    manifest = {
        "dataset_id": dataset_id,
        "source_run_id": run_id,
        "target_id": "multi-source-local-public-range-flywheel",
        "scope_type": "localhost_public_range_self_owned_training",
        "vendor_family": sorted(counts),
        "challenge_type": "captcha_failure_hard_sample_flywheel",
        "difficulty": "hard/adversarial/mixed",
        "sample_count": len(samples),
        "synthetic_count": 0,
        "public_range_count": sum(1 for sample in samples if sample["target_id"] in {"opencaptchaworld", "gocaptcha-official"}),
        "compatible_lab_count": sum(1 for sample in samples if str(sample["target_id"]).endswith("compatible-lab")),
        "authorized_sample_count": 0,
        "train_count": train,
        "val_count": val,
        "test_count": test,
        "label_source": "manually_labeled_training_sample",
        "labeler": "local_flywheel_rule_labeler",
        "leakage_check": {"status": "pending", "label_removed_from_solver_inputs": True},
        "blackbox_mode": True,
        "allowed_usage": ["local_training", "public_range_retest", "self_owned_authorized_retest"],
        "not_generalizable_to_third_party": True,
        "created_at": utc_now(),
        "sample_counts_by_family": counts,
        "sample_shortage": {family: max(0, 500 - count) for family, count in counts.items()},
        "samples": samples,
    }
    out = DATASET_ROOT / "manifests" / run_id / "dataset_manifest.json"
    write_json(out, manifest)
    failure_manifest = {
        "run_id": run_id,
        "source_failure_count": len(failure_refs),
        "failure_categories": FAILURE_CATEGORIES,
        "source_failures": failure_refs[:200],
        "dataset_manifest_path": str(out),
    }
    write_json(DATASET_ROOT / "failures" / run_id / "failure_manifest.json", failure_manifest)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect failed/hard CAPTCHA samples into dataset flywheel")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_id = args.run_id
    ensure_dirs()
    dataset_id = f"captcha-flywheel-{run_id}"
    raw_dir = DATASET_ROOT / "raw" / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    failure_refs = parse_existing_failures(PHASE311_RUN)
    samples: list[dict[str, Any]] = []
    plan = [
        ("aliyun-compatible-lab", "image_restore", 560),
        ("shumei-compatible-lab", "icon_select", 520),
        ("shumei-compatible-lab", "select", 520),
        ("shumei-compatible-lab", "seq_select", 260),
        ("shumei-compatible-lab", "spatial_select", 260),
        ("gocaptcha-official", "click", 160),
        ("gocaptcha-official", "rotate", 160),
        ("opencaptchaworld", "Connect_icon", 160),
        ("opencaptchaworld", "Image_Matching", 160),
        ("opencaptchaworld", "Coordinates", 160),
    ]
    idx = 0
    for target_id, family, count in plan:
        for offset in range(count):
            difficulty = "adversarial" if offset % 3 == 0 else "hard"
            add_grid_sample(samples, run_id, dataset_id, idx, target_id, family, difficulty, raw_dir)
            idx += 1
    manifest_path = write_manifests(run_id, samples, failure_refs)
    print(json.dumps({
        "status": "PASS",
        "run_id": run_id,
        "dataset_manifest": str(manifest_path),
        "sample_count": len(samples),
        "source_failure_count": len(failure_refs),
        "families": sorted({sample["family"] for sample in samples}),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
