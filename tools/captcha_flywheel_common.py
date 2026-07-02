#!/usr/bin/env python3
"""Shared helpers for the local CAPTCHA dataset flywheel."""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = ROOT / "datasets" / "captcha_flywheel"
PUBLIC_ROOT = ROOT / "public-range-evidence"
RAW_EVIDENCE_ROOT = PUBLIC_ROOT / "raw"
PHASE311_RUN = "run-20260630-173000-phase3-11-type-matrix"
ALLOWED_SOLVER_SOURCE = {
    "type": "locally_trained_model",
    "model_id": "",
    "local_only": True,
    "external_api_used": False,
    "third_party_solver_used": False,
    "label_leakage": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def run_dir(run_id: str) -> Path:
    return DATASET_ROOT / "manifests" / run_id


def ensure_dirs() -> None:
    for name in ("raw", "crops", "labels", "manifests", "splits", "models", "predictions", "failures", "evals", "exports"):
        (DATASET_ROOT / name).mkdir(parents=True, exist_ok=True)


def deterministic_split(sample_id: str) -> str:
    bucket = int(hashlib.sha256(sample_id.encode()).hexdigest()[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "val"
    return "test"


def svg_grid(seed: str, family: str, target: str, sequence: list[str] | None = None) -> tuple[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    colors = [("orange", "#f08c00"), ("purple", "#7048e8"), ("cyan", "#0b7285"), ("green", "#2f9e44"), ("red", "#d64545"), ("blue", "#2b6cb0")]
    rng.shuffle(colors)
    cells: list[dict[str, Any]] = []
    body = ["<svg xmlns='http://www.w3.org/2000/svg' width='300' height='135'>", "<rect width='300' height='135' fill='#f8fafc'/>"]
    for idx, (name, color) in enumerate(colors):
        x = 16 + (idx % 3) * 88 + rng.randint(-4, 4)
        y = 28 + (idx // 3) * 54 + rng.randint(-4, 4)
        body.append(f"<rect data-name='{name}' x='{x}' y='{y}' width='42' height='42' fill='{color}'/>")
        body.append(f"<text x='{x+15}' y='{y+54}' font-size='10'>{idx}</text>")
        cells.append({"index": idx, "name": name, "x": x, "y": y, "cx": x + 21, "cy": y + 21, "color": color})
    prompt = ",".join(sequence or [target])
    body.append(f"<text x='8' y='14' font-size='10'>{family}: {prompt}; local_training_sample</text></svg>")
    return "".join(body), cells


def sample_base(run_id: str, dataset_id: str, index: int, target_id: str, family: str, difficulty: str) -> dict[str, Any]:
    sample_id = f"{dataset_id}-{target_id}-{family}-{difficulty}-{index:04d}".replace("/", "_")
    return {
        "sample_id": sample_id,
        "challenge_instance_id": hashlib.sha256(sample_id.encode()).hexdigest()[:16],
        "source_run_id": run_id,
        "target_id": target_id,
        "family": family,
        "difficulty": difficulty,
        "instruction": "",
        "allowed_actions": [],
        "label": {},
        "label_source": "manually_labeled_training_sample",
        "prediction": None,
        "feedback_state": "training_sample",
        "action_trace": [],
        "success": False,
        "failure_reason": "",
        "split": deterministic_split(sample_id),
        "leakage_sensitive_fields_removed": True,
        "solver_source": dict(ALLOWED_SOLVER_SOURCE),
    }
