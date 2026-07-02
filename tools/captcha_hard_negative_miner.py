#!/usr/bin/env python3
"""Mine hard negative counts from CAPTCHA flywheel predictions."""
from __future__ import annotations

import argparse
import json

from captcha_flywheel_common import DATASET_ROOT, read_json, write_json, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine CAPTCHA hard negatives")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    manifest = read_json(DATASET_ROOT / "manifests" / args.run_id / "dataset_manifest.json")
    counts: dict[str, int] = {}
    for sample in manifest.get("samples", []):
        if sample.get("difficulty") in {"hard", "adversarial"}:
            counts[str(sample.get("family"))] = counts.get(str(sample.get("family")), 0) + 1
    out_payload = {"run_id": args.run_id, "created_at": utc_now(), "hard_negative_counts": counts, "next_sampling_targets": sorted([k for k, v in counts.items() if v < 500])}
    out = DATASET_ROOT / "evals" / args.run_id / "hard_negative_mining.json"
    write_json(out, out_payload)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "report": str(out), "hard_negative_counts": counts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
