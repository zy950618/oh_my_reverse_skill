from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_TRUE = [
    "no_playwright_runtime",
    "no_puppeteer_runtime",
    "no_camoufox_runtime",
    "no_browser_profile_dependency",
    "no_manual_cookie_copy",
    "node_or_v8_or_quickjs_or_python_sign_generation",
    "replay_diff_report_exists",
    "docker_headless_ready",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def load_report(root: Path) -> dict:
    report = root / "validation_report.json"
    if not report.exists():
        raise FileNotFoundError(f"missing {report}")
    return json.loads(report.read_text(encoding="utf-8"))


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.exists():
        return [f"missing lab root: {root}"]
    try:
        data = load_report(root)
    except Exception as exc:
        return [str(exc)]

    for key in REQUIRED_TRUE:
        if data.get(key) is not True:
            errors.append(f"{key} must be true")

    if data.get("final_business_flow") not in {"pure_api_only", "local_order_flow_lab"}:
        errors.append("final_business_flow must be pure_api_only or local_order_flow_lab")

    if "airline-lab-order-flow" in root.as_posix():
        required_dirs = ["mock_server", "fastapi_adapter", "fixtures", "replay", "reports", "sdk_examples"]
        for directory in required_dirs:
            if not (root / directory).exists():
                errors.append(f"missing airline lab directory: {directory}")
        required_steps = {
            "search flight",
            "select flight",
            "quote price",
            "passenger validate",
            "create draft order",
            "confirm test order",
            "cancel test order",
            "replay",
            "diff",
            "report",
        }
        observed_steps = set(data.get("order_flow_steps", []))
        missing_steps = sorted(required_steps - observed_steps)
        if missing_steps:
            errors.append(f"missing order_flow_steps: {', '.join(missing_steps)}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return fail("usage: python tools/validate_pure_api_delivery.py <lab-root>")
    root = Path(argv[1])
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: pure API delivery gate passed for {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
