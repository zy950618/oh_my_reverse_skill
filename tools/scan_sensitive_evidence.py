from __future__ import annotations

import json
import re
import subprocess
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = next(ROOT.glob("99-SKILLS*/"), ROOT / "99-SKILLS治理") / "47-secret-and-live-evidence-scan.md"

SECRET_TERMS = [
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
    "x-csrf",
    "jwt",
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "client_secret",
    "private_key",
    "begin rsa private key",
    "begin openssh private key",
    "storageState",
    "userDataDir",
    "profile",
    "browser profile",
]
TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".css",
    ".csv",
    ".env",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}
HIGH_RISK_SUFFIXES = {".har", ".cookies", ".cookie"}
PROFILE_PARTS = {"userdatadir", "browser-profile", "browser-profiles", ".browser-profiles", "profiles", ".profiles"}
PLACEHOLDER_WORDS = {
    "dummy",
    "example",
    "fake",
    "placeholder",
    "redacted",
    "sample",
    "test",
    "todo",
    "xxx",
    "your_",
    "changeme",
    "change_me",
    "<",
    "${",
}


def git_paths(staged: bool = False) -> list[Path]:
    if staged:
        raw = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"], cwd=ROOT)
        return sorted(
            set(path for item in raw.split(b"\0") if item for path in [ROOT / item.decode("utf-8", errors="replace")] if path.exists()),
            key=lambda item: item.as_posix(),
        )

    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "-uall"], cwd=ROOT)
    paths: list[Path] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        text = item.decode("utf-8", errors="replace")
        if len(text) < 4:
            continue
        paths.append(ROOT / text[3:])
    return sorted(set(path for path in paths if path.exists()), key=lambda item: item.as_posix())


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_text_candidate(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return ""


def value_is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    return any(word in lowered for word in PLACEHOLDER_WORDS)


def looks_like_secret_value(value: str) -> bool:
    cleaned = value.strip().strip("\"'`,; ")
    if value_is_placeholder(cleaned):
        return False
    if len(cleaned) < 20:
        return False
    if re.fullmatch(r"[A-Za-z0-9_./+=:-]{20,}", cleaned):
        return True
    return False


def classify_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    lowered = stripped.lower()
    if re.search(r"-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----", stripped):
        return "secret", "private_key_material"
    jwt_match = re.search(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", stripped)
    if jwt_match and not value_is_placeholder(jwt_match.group(0)):
        return "token", "jwt_like_value"
    bearer = re.search(r"authorization\s*[:=]\s*bearer\s+([A-Za-z0-9_./+=:-]{16,})", stripped, re.I)
    if bearer and looks_like_secret_value(bearer.group(1)):
        return "token", "authorization_bearer"
    cookie = re.search(r"^(set-cookie|cookie)\s*[:=]\s*(.+)$", stripped, re.I)
    if cookie and looks_like_secret_value(cookie.group(2)):
        return "cookie", "cookie_header"
    kv = re.search(
        r"(access_token|refresh_token|client_secret|api_key|apikey|password|passwd|private_key|secret|csrf|x-csrf)\s*[:=]\s*[\"']?([^\"'\s,}]+)",
        stripped,
        re.I,
    )
    if kv and looks_like_secret_value(kv.group(2)):
        key = kv.group(1).lower()
        if "token" in key or "csrf" in key:
            return "token", key
        return "secret", key
    return None


def scan_path(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    findings: list[dict[str, object]] = []
    info: list[dict[str, object]] = []
    relative = rel(path)
    lower_path = relative.lower()
    suffix = path.suffix.lower()
    parts = {part.lower() for part in path.relative_to(ROOT).parts}

    if suffix == ".har":
        findings.append({"path": relative, "kind": "har", "reason": "har_file_extension"})
    if suffix in {".cookies", ".cookie"}:
        findings.append({"path": relative, "kind": "cookie", "reason": "cookie_file_extension"})
    if parts & PROFILE_PARTS:
        findings.append({"path": relative, "kind": "profile", "reason": "browser_profile_path"})

    if any(term.lower() in lower_path for term in SECRET_TERMS):
        info.append({"path": relative, "kind": "keyword_path", "reason": "sensitive_keyword_in_path"})

    if not path.is_file() or not is_text_candidate(path):
        return findings, info

    text = read_text(path)
    if not text:
        return findings, info
    lowered_text = text.lower()
    if any(term.lower() in lowered_text for term in SECRET_TERMS):
        info.append({"path": relative, "kind": "keyword_content", "reason": "sensitive_keyword_in_content"})

    for lineno, line in enumerate(text.splitlines(), start=1):
        classified = classify_line(line)
        if classified:
            kind, reason = classified
            findings.append({"path": relative, "line": lineno, "kind": kind, "reason": reason})
    return findings, info


def summarize(findings: list[dict[str, object]], info: list[dict[str, object]], paths: list[Path], staged: bool) -> dict[str, object]:
    secret_count = sum(1 for item in findings if item["kind"] == "secret")
    cookie_count = sum(1 for item in findings if item["kind"] == "cookie")
    token_count = sum(1 for item in findings if item["kind"] == "token")
    har_count = sum(1 for item in findings if item["kind"] == "har")
    profile_count = sum(1 for item in findings if item["kind"] == "profile")
    return {
        "tool": "scan_sensitive_evidence",
        "scope": "staged" if staged else "visible_status",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not findings else "FAIL",
        "scanned_file_count": len(paths),
        "secret_count": secret_count,
        "live_cookie_count": cookie_count,
        "live_token_count": token_count,
        "live_har_count": har_count,
        "browser_profile_count": profile_count,
        "informational_keyword_hit_count": len(info),
        "findings": findings[:200],
        "informational": info[:200],
    }


def write_report(payload: dict[str, object]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Secret and Live Evidence Scan\n\n"
        f"checked_at: {payload['checked_at']}\n\n"
        f"status: {payload['status']}\n\n"
        f"scanned_file_count: {payload['scanned_file_count']}\n\n"
        f"secret_count: {payload['secret_count']}\n\n"
        f"live_cookie_count: {payload['live_cookie_count']}\n\n"
        f"live_token_count: {payload['live_token_count']}\n\n"
        f"live_har_count: {payload['live_har_count']}\n\n"
        f"browser_profile_count: {payload['browser_profile_count']}\n\n"
        f"informational_keyword_hit_count: {payload['informational_keyword_hit_count']}\n\n"
        "## Findings\n\n"
        + json.dumps(payload["findings"], ensure_ascii=False, indent=2)
        + "\n\n## Informational Keyword Hits\n\n"
        + json.dumps(payload["informational"], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan visible or staged git candidates for secrets and live evidence.")
    parser.add_argument("--staged", action="store_true", help="scan only staged files from the git index")
    args = parser.parse_args()

    paths = git_paths(staged=args.staged)
    findings: list[dict[str, object]] = []
    info: list[dict[str, object]] = []
    for path in paths:
        path_findings, path_info = scan_path(path)
        findings.extend(path_findings)
        info.extend(path_info)
    payload = summarize(findings, info, paths, args.staged)
    if not args.staged and paths:
        write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
