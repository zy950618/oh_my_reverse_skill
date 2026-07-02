from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SUPPORTED_SUFFIXES = {".json", ".jsonl", ".txt", ".md", ".yaml", ".yml", ".har"}
SKIPPED_DIR_NAMES = {"redacted", "__pycache__", ".git"}
SENSITIVE_KEYS = (
    "cookie",
    "set-cookie",
    "authorization",
    "bearer",
    "token",
    "access_token",
    "refresh_token",
    "session",
    "sid",
    "csrf",
    "jwt",
    "api_key",
    "password",
    "order_id",
    "passenger",
    "email",
    "phone",
)
KEY_PATTERN = "|".join(re.escape(key) for key in sorted(SENSITIVE_KEYS, key=len, reverse=True))
KEY_VALUE_PATTERNS = [
    re.compile(rf"(?i)([\"']?(?:{KEY_PATTERN})[\"']?\s*[:=]\s*)([\"']?)([^\"'\n\r,;}}{{]+)([\"']?)"),
    re.compile(rf"(?i)\b((?:{KEY_PATTERN})\s+)([\"']?)([^\s,;]+)([\"']?)"),
]
VALUE_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+([A-Za-z0-9_.+/=-]+)"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<![A-Za-z0-9])\+?\d[\d .()/-]{8,}\d(?![A-Za-z0-9])"),
]


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk


def iter_candidate_files(path: Path) -> tuple[list[Path], list[dict[str, str]]]:
    skipped: list[dict[str, str]] = []
    if path.is_file():
        return [path], skipped
    if not path.is_dir():
        return [], [{"path": str(path), "reason": "missing_input"}]

    files: list[Path] = []
    for child in sorted(path.rglob("*"), key=lambda item: item.as_posix()):
        if not child.is_file():
            continue
        if any(part.lower() in SKIPPED_DIR_NAMES for part in child.parts):
            skipped.append({"path": child.as_posix(), "reason": "skipped_directory"})
            continue
        files.append(child)
    return files, skipped


def redact_text(text: str) -> tuple[str, int]:
    findings = 0
    redacted = text
    for pattern in KEY_VALUE_PATTERNS:
        redacted, count = pattern.subn(lambda match: f"{match.group(1)}{match.group(2)}<REDACTED>{match.group(4)}", redacted)
        findings += count
    for pattern in VALUE_PATTERNS:
        redacted, count = pattern.subn(lambda match: match.group(0).split()[0] + " <REDACTED>" if match.group(0).lower().startswith("bearer ") else "<REDACTED>", redacted)
        findings += count
    return redacted, findings


def output_path_for(input_root: Path, path: Path, output_root: Path | None) -> Path:
    if output_root:
        if input_root.is_dir():
            return output_root / path.relative_to(input_root)
        return output_root / path.name
    if input_root.is_dir():
        return input_root / "redacted" / path.relative_to(input_root)
    return path.with_name(path.name + ".redacted")


def redact_path(input_path: Path, output_root: Path | None, dry_run: bool) -> dict[str, object]:
    input_path = input_path.resolve()
    output_root = output_root.resolve() if output_root else None
    candidates, skipped = iter_candidate_files(input_path)
    scanned_files = 0
    redacted_files = 0
    findings_count = 0
    outputs: list[str] = []

    for path in candidates:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            skipped.append({"path": path.as_posix(), "reason": "unsupported_suffix"})
            continue
        if is_binary(path):
            skipped.append({"path": path.as_posix(), "reason": "binary_file"})
            continue

        scanned_files += 1
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        redacted, findings = redact_text(text)
        findings_count += findings
        destination = output_path_for(input_path, path, output_root)
        outputs.append(destination.as_posix())
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(redacted, encoding="utf-8")
            redacted_files += 1
        elif findings:
            redacted_files += 1

    return {
        "tool": "redact_live_evidence",
        "status": "PASS",
        "dry_run": dry_run,
        "input": input_path.as_posix(),
        "scanned_files": scanned_files,
        "redacted_files": redacted_files,
        "skipped_files": len(skipped),
        "findings_count": findings_count,
        "output_dir": output_root.as_posix() if output_root else "",
        "outputs": outputs[:50],
        "skipped": skipped[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact live evidence text files without overwriting raw inputs.")
    parser.add_argument("path", nargs="?", help="file or directory to redact")
    parser.add_argument("--dry-run", action="store_true", help="scan and summarize without writing redacted files")
    parser.add_argument("--output", help="write redacted files into this directory")
    args = parser.parse_args()

    if not args.path:
        print(json.dumps({"tool": "redact_live_evidence", "status": "DRY_RUN", "input_required": True}, indent=2))
        return 0

    dry_run = args.dry_run or not args.output
    payload = redact_path(Path(args.path), Path(args.output) if args.output else None, dry_run=dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
