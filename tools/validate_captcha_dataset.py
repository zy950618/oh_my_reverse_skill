#!/usr/bin/env python3
"""Validate a CAPTCHA dataset manifest and its sample label files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ALLOWED_LICENSE_SCOPES = {"authorized_public_lab", "local_synthetic", "owned_target"}
ALLOWED_SPLITS = {"train", "validation", "test"}
SENSITIVE_KEYS = {"token", "cookie", "password", "secret", "session_id"}
DEFAULT_MANIFEST = Path("public-range-evidence/captcha-model-lab/manifests/dataset_manifest.json")


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail(f"{path} root must be an object")
    return data


def contains_sensitive_key(value: object, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            lower_key = key.lower()
            if lower_key in SENSITIVE_KEYS or lower_key.endswith("_token"):
                return f"{path}.{key}"
            found = contains_sensitive_key(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = contains_sensitive_key(child, f"{path}[{index}]")
            if found:
                return found
    return None


def require_dict(data: dict, key: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        fail(f"{key} must be an object")
    return value


def require_list(data: dict, key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key} must be a non-empty list")
    return value


def resolve(base: Path, relative: str) -> Path:
    return (base.parent / relative).resolve()


def validate_label(label_path: Path, sample: dict) -> None:
    label = load_json(label_path)
    if label.get("sample_id") != sample.get("sample_id"):
        fail(f"{label_path} sample_id does not match manifest sample")
    if label.get("challenge_type") != sample.get("challenge_type"):
        fail(f"{label_path} challenge_type does not match manifest sample")
    if label.get("provider") != sample.get("provider"):
        fail(f"{label_path} provider does not match manifest sample")
    if not isinstance(label.get("actions"), list) or not label["actions"]:
        fail(f"{label_path} requires non-empty actions")
    protocol = require_dict(label, "label_protocol")
    review = require_dict(protocol, "review")
    labelers = review.get("labelers")
    if not isinstance(labelers, int) or labelers < 1:
        fail(f"{label_path} label_protocol.review.labelers must be a positive integer")


def validate_manifest(path: Path) -> None:
    manifest = load_json(path)
    if manifest.get("manifest_type") != "captcha_dataset":
        fail("manifest_type must be captcha_dataset")
    if not manifest.get("dataset_id"):
        fail("dataset_id is required")
    if manifest.get("license_scope") not in ALLOWED_LICENSE_SCOPES:
        fail("license_scope is not allowed")
    if contains_sensitive_key(manifest):
        fail("dataset manifest contains sensitive key material")

    splits = require_dict(manifest, "splits")
    samples = require_list(manifest, "samples")
    counts: Counter[str] = Counter()
    sample_ids: set[str] = set()
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            fail(f"samples[{index}] must be an object")
        for key in ("sample_id", "split", "provider", "challenge_type", "image_path", "label_path"):
            if not sample.get(key):
                fail(f"samples[{index}].{key} is required")
        if sample["split"] not in ALLOWED_SPLITS:
            fail(f"samples[{index}].split is unsupported")
        if sample["sample_id"] in sample_ids:
            fail(f"duplicate sample_id {sample['sample_id']!r}")
        sample_ids.add(sample["sample_id"])
        counts[sample["split"]] += 1

        provenance = require_dict(sample, "provenance")
        for key in ("source", "authorization", "redaction"):
            if not provenance.get(key):
                fail(f"samples[{index}].provenance.{key} is required")

        image_path = resolve(path, sample["image_path"])
        label_path = resolve(path, sample["label_path"])
        if not image_path.is_file():
            fail(f"image path does not exist: {image_path}")
        if not label_path.is_file():
            fail(f"label path does not exist: {label_path}")
        validate_label(label_path, sample)

    for split, expected in splits.items():
        if split not in ALLOWED_SPLITS:
            fail(f"splits contains unsupported split {split!r}")
        if counts[split] != expected:
            fail(f"splits.{split} expected {expected}, observed {counts[split]}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        validate_manifest(args.manifest)
    except Exception as exc:
        print(f"FAIL {args.manifest}: {exc}", file=sys.stderr)
        return 1
    print(f"PASS {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
