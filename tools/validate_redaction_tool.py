from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "authorized-live-tests" / "redaction-fixtures"
WORK = ROOT / ".ci-out" / "redaction-validator"
TOOL = ROOT / "tools" / "redact_live_evidence.py"
REQUIRED_FIXTURES = [
    FIXTURES / "sample-live-report.json",
    FIXTURES / "sample-live-report.md",
    FIXTURES / "sample-live-report.yaml",
]


def run_tool(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "status": "FAIL",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {"status": "FAIL", "stdout": completed.stdout, "error": str(exc)}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def validate() -> dict[str, object]:
    failures: list[str] = []
    for fixture in REQUIRED_FIXTURES:
        if not fixture.is_file():
            failures.append(f"missing fixture {fixture.relative_to(ROOT).as_posix()}")

    before = {fixture: read(fixture) for fixture in REQUIRED_FIXTURES if fixture.is_file()}

    file_payload = run_tool(str(REQUIRED_FIXTURES[0]), "--dry-run")
    if file_payload.get("status") != "PASS" or file_payload.get("scanned_files") != 1:
        failures.append("file input did not pass")

    dir_payload = run_tool(str(FIXTURES), "--dry-run")
    if dir_payload.get("status") != "PASS" or int(dir_payload.get("scanned_files", 0)) < 3:
        failures.append("directory dry-run did not scan fixtures")
    if int(dir_payload.get("findings_count", 0)) <= 0:
        failures.append("directory dry-run did not report findings")

    output_dir = WORK / "redacted-output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_payload = run_tool(str(FIXTURES), "--output", str(output_dir))
    if output_payload.get("status") != "PASS":
        failures.append("output directory run failed")
    for fixture in REQUIRED_FIXTURES:
        output_file = output_dir / fixture.name
        if not output_file.is_file():
            failures.append(f"missing redacted output {output_file.relative_to(ROOT).as_posix()}")
            continue
        text = read(output_file)
        if "<REDACTED>" not in text:
            failures.append(f"output missing redaction marker {output_file.relative_to(ROOT).as_posix()}")
        for raw_value in ("SESSION_FAKE_VALUE", "FAKE_TOKEN", "ORDER_FAKE_123", "fake@example.com", "+10000000000"):
            if raw_value in text:
                failures.append(f"raw fixture value was not redacted in {output_file.relative_to(ROOT).as_posix()}")

    after = {fixture: read(fixture) for fixture in REQUIRED_FIXTURES if fixture.is_file()}
    if before != after:
        failures.append("raw fixtures were overwritten")

    binary_dir = WORK / "binary-input"
    if binary_dir.exists():
        shutil.rmtree(binary_dir)
    binary_dir.mkdir(parents=True, exist_ok=True)
    binary_file = binary_dir / "sample.har"
    binary_file.write_bytes(b"\x00\x01cookie: SESSION_FAKE_VALUE")
    binary_payload = run_tool(str(binary_dir), "--dry-run")
    binary_skipped = any(item.get("reason") == "binary_file" for item in binary_payload.get("skipped", []))
    if not binary_skipped:
        failures.append("binary supported-suffix file was not skipped as binary_file")

    payload = {
        "tool": "validate_redaction_tool",
        "status": "PASS" if not failures else "FAIL",
        "file_input": file_payload.get("status"),
        "directory_input": dir_payload.get("status"),
        "dry_run": "PASS" if dir_payload.get("dry_run") is True else "FAIL",
        "output_directory": output_payload.get("status"),
        "raw_files_overwritten": before != after,
        "binary_skipped": binary_skipped,
        "summary_output": all(key in dir_payload for key in ("scanned_files", "redacted_files", "skipped_files", "findings_count", "output_dir")),
        "failures": failures,
    }
    return payload


def main() -> int:
    payload = validate()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
