from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "authorized-live-tests" / "authorized-live-targets.local.yaml"


def main() -> int:
    payload = {
        "tool": "run_authorized_readonly_probe",
        "status": "DRY_RUN",
        "network_performed": False,
        "mutation_performed": False,
        "reason": "private authorized_readonly config is required before any live query",
        "local_config_present": LOCAL_CONFIG.exists(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
