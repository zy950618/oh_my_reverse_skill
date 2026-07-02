#!/usr/bin/env python3
"""Self-owned vendor trial adapter.

The tool never fabricates Shumei/Aliyun credentials. Missing local private
configuration is a valid BLOCKED result with explicit next user input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {
    "shumei": ["organization_id", "app_id", "scene_id", "test_domain", "allowed_host", "server_verify_endpoint", "rate_limit", "stop_condition", "evidence_redaction"],
    "aliyun": ["scene_id", "captcha_config", "test_domain", "allowed_host", "client_integration", "server_verify_endpoint", "business_data_assertions", "evidence_redaction"],
}


def read_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def redact_config(config: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in config.items():
        if any(token in key.lower() for token in ("secret", "accesskey", "access_key", "token", "password")):
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def blocked(target: str, run_id: str, config_path: Path, missing: list[str], reason: str) -> dict[str, Any]:
    status = "CONFIG_MISSING" if not config_path.is_file() else ("CONFIG_INVALID" if reason.startswith("config") else "BLOCKED_AUTH_REQUIRED")
    return {
        "schema_version": "vendor-trial-adapter/v1",
        "run_id": run_id,
        "target": target,
        "status": status,
        "blocked_status": "BLOCKED_AUTH_REQUIRED",
        "execution_status": "BLOCKED",
        "capability_status": "memory_only",
        "blocked_reason": reason,
        "missing_self_owned_credentials": not config_path.is_file(),
        "missing_scene_id": "scene_id" in missing,
        "missing_allowed_host": "allowed_host" in missing,
        "missing_fields": missing,
        "next_required_user_input": {
            "config_path": str(config_path),
            "required_fields": REQUIRED[target],
            "note": "Provide a self-owned trial config outside source control. Do not commit secrets.",
        },
        "no_fake_credentials_used": True,
        "official_trial_not_run": True,
        "compatible_lab_not_used_as_substitute": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run self-owned Shumei/Aliyun trial diagnostics or emit BLOCKED")
    parser.add_argument("--target", required=True, choices=["shumei", "aliyun"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", help="private local config JSON path; do not commit")
    args = parser.parse_args()
    target = args.target
    config_path = Path(args.config) if args.config else ROOT / "configs" / "vendor_trial.local.yaml"
    out = ROOT / "public-range-evidence" / "raw" / "vendor-trial-adapter" / args.run_id / f"{target}.json"
    if not config_path.is_file():
        report = blocked(target, args.run_id, config_path, REQUIRED[target], "missing self-owned trial config")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    try:
        config = read_json(config_path)
    except Exception as exc:
        report = blocked(target, args.run_id, config_path, REQUIRED[target], f"config parse failed: {exc!r}")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if not isinstance(config, dict):
        report = blocked(target, args.run_id, config_path, REQUIRED[target], "config is not a JSON object")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    target_config = config.get(target, config)
    if not isinstance(target_config, dict):
        report = blocked(target, args.run_id, config_path, REQUIRED[target], f"config section {target} is missing")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if target_config.get("enabled") is not True:
        report = blocked(target, args.run_id, config_path, REQUIRED[target], "self-owned trial is disabled or authorization not confirmed")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    missing = [field for field in REQUIRED[target] if not target_config.get(field)]
    if missing:
        report = blocked(target, args.run_id, config_path, missing, "self-owned trial config is incomplete")
        write_json(out, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    report = {
        "schema_version": "vendor-trial-adapter/v1",
        "run_id": args.run_id,
        "target": target,
        "status": "TRIAL_RUN_FAIL",
        "execution_status": "STRUCTURE_ONLY",
        "capability_status": "memory_only",
        "config_path": str(config_path),
        "config_redacted": redact_config(target_config),
        "no_fake_credentials_used": True,
        "next_step": "Provider-specific live official trial execution is blocked until the adapter is connected to the configured self-owned integration endpoint.",
        "trial_run_pass_possible_status": "TRIAL_RUN_PASS",
        "trial_run_fail_reason": "live official provider request is not implemented without provider-specific signed integration code",
    }
    write_json(out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
