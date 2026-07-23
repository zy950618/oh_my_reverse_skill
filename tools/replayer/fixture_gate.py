#!/usr/bin/env python3
"""Canonical selector-backed fixture validation and freshness gate."""
from __future__ import annotations

import argparse
import datetime as dt
import errno
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from fixture_layout import select_fixture_layout


SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITE_ROOT = REPO_ROOT / "站点经验库"


class Mode(str, Enum):
    OFFLINE = "offline"
    DIAGNOSTIC = "diagnostic"
    STRICT = "strict"
    REFRESH = "refresh"


TOP_LEVEL_KEYS = (
    "schema_version",
    "tool",
    "mode",
    "status",
    "exit_code",
    "capability",
    "no_data",
    "freshness_checked",
    "replay_lineage",
    "totals",
    "domains",
    "issues",
    "refresh_tasks",
    "artifact",
)
TOTAL_KEYS = (
    "domains_selected",
    "domains_with_snapshots",
    "request_files",
    "response_files",
    "metadata_files",
    "complete_triplets",
    "valid_triplets",
    "expired_count",
    "review_pending_count",
    "missing_expiry_count",
    "structure_issue_count",
    "freshness_issue_count",
    "refresh_task_count",
)
DOMAIN_KEYS = (
    "domain",
    "selected_root",
    "selected_layout",
    "snapshots_state",
    "request_files",
    "response_files",
    "metadata_files",
    "complete_triplets",
    "valid_triplets",
    "structure_issue_count",
    "freshness_issue_count",
    "source_freshness",
    "selected_report",
)
SELECTED_REPORT_KEYS = ("path", "status", "total", "replayed", "source", "recent")
ISSUE_KEYS = ("scope", "domain", "prefix", "selected_root", "reason")
TASK_KEYS = ISSUE_KEYS + ("action",)
ARTIFACT_KEYS = ("path", "sha256")

TOOLS = {"validate_fixtures", "fixture_freshness_report"}
STATUSES = {
    "PASS",
    "STRUCTURE_ONLY",
    "STALE",
    "NO_DATA",
    "RECERTIFICATION_REQUIRED",
    "STRUCTURE_INVALID",
    "INVALID_ARGUMENT",
    "INTERNAL_ERROR",
}
CAPABILITIES = {
    "FRESH_FIXTURE_GATE",
    "STRUCTURE_ONLY",
    "DIAGNOSTIC_ONLY",
    "REFRESH_PLAN",
    "REFRESH_NOT_REQUIRED",
    "NO_CAPABILITY",
}
SCOPES = {"ROOT", "DOMAIN", "FIXTURE", "REPORT"}
SNAPSHOT_STATES = {"MISSING", "NOT_DIRECTORY", "DIRECTORY"}
SOURCE_FRESHNESS = {"fresh", "stale", "missing", "not_checked"}

STRUCTURE_REASONS = {
    "DOMAIN_MISSING",
    "DOMAIN_NOT_DIRECTORY",
    "UNSAFE_DOMAIN",
    "SNAPSHOTS_MISSING",
    "SNAPSHOTS_NOT_DIRECTORY",
    "ORPHAN_REQ",
    "ORPHAN_RESP",
    "ORPHAN_META",
    "JSON_UNREADABLE",
    "JSON_MALFORMED",
    "JSON_ROOT_NOT_OBJECT",
    "META_UNREADABLE",
    "META_REQUIRED_MISSING",
    "META_BOOL_INVALID",
    "CATEGORY_FORBIDDEN",
}
FRESHNESS_REASONS = {
    "EXPIRY_MISSING",
    "EXPIRY_INVALID",
    "EXPIRED",
    "REVIEW_PENDING",
    "REPORT_MISSING",
    "REPORT_STALE",
    "REPORT_MALFORMED",
    "REPORT_NOT_PASS",
    "REPORT_COVERAGE_MISMATCH",
}
OTHER_REASONS = {
    "SITE_ROOT_MISSING",
    "NO_DOMAINS",
    "NO_COMPLETE_TRIPLETS",
    "INVALID_ARGUMENT",
    "INTERNAL_ERROR",
}
REASONS = STRUCTURE_REASONS | FRESHNESS_REASONS | OTHER_REASONS
ALLOWED_CATEGORIES = {"public-read", "search", "detail", "list", "session", "config"}
META_REQUIRED = (
    "endpoint",
    "recorded_at",
    "captured_at",
    "expires_at",
    "category",
    "sensitive",
    "requires_auth",
    "source",
    "schema_version",
    "review_status",
)
BOOL_FIELDS = ("sensitive", "requires_auth")
REVIEW_PATTERNS = (
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"auto[- ]extracted", re.IGNORECASE),
    re.compile(r"pending review|review pending|needs review|review required|needs edit|manual edit", re.IGNORECASE),
)
UNSAFE_OUTPUT_PATTERN = re.compile(
    r"(?i)(?:://|[?\#@=&]|authorization|bearer|cookie|credential|headers?|"
    r"password|passwd|secret|tokens?|api[-_]?key|userinfo)"
)

TASK_MAPPING = {
    "SITE_ROOT_MISSING": ("ROOT", "CREATE_CAPTURE_ROOT"),
    "NO_DOMAINS": ("ROOT", "CREATE_CAPTURE_ROOT"),
    "SNAPSHOTS_MISSING": ("DOMAIN", "CAPTURE_DOMAIN"),
    "SNAPSHOTS_NOT_DIRECTORY": ("DOMAIN", "CAPTURE_DOMAIN"),
    "NO_COMPLETE_TRIPLETS": ("DOMAIN", "CAPTURE_DOMAIN"),
    "NO_COMPLETE_TRIPLETS": ("DOMAIN", "CAPTURE_DOMAIN"),
    "ORPHAN_REQ": ("FIXTURE", "COMPLETE_TRIPLET"),
    "ORPHAN_RESP": ("FIXTURE", "COMPLETE_TRIPLET"),
    "ORPHAN_META": ("FIXTURE", "COMPLETE_TRIPLET"),
    "JSON_UNREADABLE": ("FIXTURE", "RECAPTURE_FIXTURE"),
    "JSON_MALFORMED": ("FIXTURE", "RECAPTURE_FIXTURE"),
    "JSON_ROOT_NOT_OBJECT": ("FIXTURE", "RECAPTURE_FIXTURE"),
    "META_UNREADABLE": ("FIXTURE", "REVIEW_METADATA"),
    "META_REQUIRED_MISSING": ("FIXTURE", "REVIEW_METADATA"),
    "META_BOOL_INVALID": ("FIXTURE", "REVIEW_METADATA"),
    "CATEGORY_FORBIDDEN": ("FIXTURE", "REVIEW_METADATA"),
    "EXPIRY_MISSING": ("FIXTURE", "REVIEW_METADATA"),
    "EXPIRY_INVALID": ("FIXTURE", "REVIEW_METADATA"),
    "EXPIRED": ("FIXTURE", "RECAPTURE_FIXTURE"),
    "REVIEW_PENDING": ("FIXTURE", "REVIEW_METADATA"),
    "REPORT_MISSING": ("REPORT", "REPLAY_SELECTED_FIXTURES"),
    "REPORT_STALE": ("REPORT", "REPLAY_SELECTED_FIXTURES"),
    "REPORT_MALFORMED": ("REPORT", "REPLAY_SELECTED_FIXTURES"),
    "REPORT_NOT_PASS": ("REPORT", "REPLAY_SELECTED_FIXTURES"),
    "REPORT_COVERAGE_MISMATCH": ("REPORT", "REPLAY_SELECTED_FIXTURES"),
    "DOMAIN_MISSING": ("DOMAIN", "CAPTURE_DOMAIN"),
    "DOMAIN_NOT_DIRECTORY": ("DOMAIN", "CAPTURE_DOMAIN"),
    "UNSAFE_DOMAIN": ("DOMAIN", "RENAME_DOMAIN"),
}

CONSISTENCY_KEYS = (
    "status",
    "exit_code",
    "total",
    "selected",
    "replayed",
    "compared",
    "fatal_error_count",
    "status_mismatch_count",
    "no_data",
    "consistency_rate",
    "threshold",
    "failure_kind",
    "report_artifact",
    "trend_artifact",
    "comparable_fields",
    "matched_fields",
    "structure_ok",
    "empty_snapshot_count",
)


class PublicationStop(RuntimeError):
    """Ambiguous publication state that must not become a canonical result."""


class PublicationPreflightError(OSError):
    """Publication platform admission failed before repository staging."""


def _zero_totals() -> dict[str, int]:
    return {key: 0 for key in TOTAL_KEYS}


def _display_path(path: Path, site_root: Path) -> str:
    resolved = path.resolve(strict=False)
    for base in (REPO_ROOT, site_root.resolve(strict=False)):
        try:
            display = resolved.relative_to(base).as_posix()
            return "/".join(_sanitize_identifier(part, "path") for part in display.split("/"))
        except ValueError:
            pass
    return _sanitize_identifier(path.name, "path")


def _sanitize_identifier(value: str, kind: str) -> str:
    normalized = str(value).strip()
    if normalized and not UNSAFE_OUTPUT_PATTERN.search(normalized) and not any(
        ord(char) < 32 for char in normalized
    ):
        return normalized
    digest = hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{kind}-sha256-{digest}"


def _safe_output_path(value: str) -> bool:
    return isinstance(value, str) and bool(value) and all(
        part == _sanitize_identifier(part, "path") for part in value.split("/")
    )


def _safe_repo_relative_posix_path(value: Any) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or "\\" in value
        or re.match(r"^[A-Za-z]:/", value)
    ):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return _safe_output_path(value) and Path(value).as_posix() == value


def _selected_report_path_matches(report_path: Any, selected_root: Any) -> bool:
    if not _safe_repo_relative_posix_path(report_path) or not _safe_repo_relative_posix_path(
        selected_root
    ):
        return False
    report = PurePosixPath(report_path)
    expected_parent = PurePosixPath(selected_root) / "reports"
    return (
        report.parent == expected_parent
        and report.name.endswith("-replay.md")
        and report.name != "-replay.md"
    )


def _domain_root_binding(
    item: dict[str, Any],
    expected_site_root: Path | None = None,
    expected_bindings: dict[str, tuple[str, str]] | None = None,
) -> bool:
    domain = item.get("domain")
    selected_root = item.get("selected_root")
    layout = item.get("selected_layout")
    if not _is_safe_domain(domain) or not _safe_repo_relative_posix_path(selected_root):
        return False
    if expected_bindings is not None:
        return expected_bindings.get(domain) == (selected_root, layout)
    expected = (domain, "fixtures", "active") if layout == "active" else (domain, "fixtures")
    if expected_site_root is not None:
        site_root = Path(os.path.abspath(expected_site_root))
        domain_dir = site_root / domain
        fixtures = domain_dir / "fixtures"
        if _lexists(domain_dir) and not _is_symlink(domain_dir) and domain_dir.is_dir():
            physical_root, _ = select_fixture_layout(fixtures)
        else:
            physical_root = fixtures
        expected_display = _display_path(physical_root, site_root)
        expected_layout = "active" if physical_root == fixtures / "active" else "legacy"
        return selected_root == expected_display and layout == expected_layout
    parts = PurePosixPath(selected_root).parts
    return parts == expected or parts == (DEFAULT_SITE_ROOT.name, *expected)


def _is_actual_int(value: Any) -> bool:
    return type(value) is int


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _is_symlink(path: Path) -> bool:
    try:
        return stat.S_ISLNK(path.lstat().st_mode)
    except OSError:
        return False


def _contained(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except (OSError, ValueError):
        return False


def _is_safe_domain(value: Any) -> bool:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        return False
    try:
        encoded = value.encode("utf-8", errors="strict")
        if encoded.decode("utf-8", errors="strict") != value:
            return False
    except UnicodeError:
        return False
    if not 1 <= len(encoded) <= 253 or unicodedata.normalize("NFC", value) != value:
        return False
    if value[0] in "_." or value[-1] == "." or ".." in value:
        return False
    labels = value.split(".")
    if any(not label or label[0] == "-" or label[-1] == "-" for label in labels):
        return False
    for char in value:
        if char in "-.":
            continue
        category = unicodedata.category(char)
        if category[0] not in {"L", "N", "M"}:
            return False
    return True


def _unsafe_domain_identifier(value: str) -> str:
    digest = hashlib.sha256(os.fsencode(value)).hexdigest()[:16]
    return f"domain-sha256-{digest}"


def _issue(
    scope: str,
    reason: str,
    *,
    domain: str | None = None,
    prefix: str | None = None,
    selected_root: str | None = None,
) -> dict[str, str | None]:
    return {
        "scope": scope,
        "domain": _sanitize_identifier(domain, "domain") if domain is not None else None,
        "prefix": _sanitize_identifier(prefix, "prefix") if prefix is not None else None,
        "selected_root": (
            "/".join(_sanitize_identifier(part, "path") for part in selected_root.split("/"))
            if selected_root is not None
            else None
        ),
        "reason": reason,
    }


def _identity(item: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(item.get(key) or "") for key in (*ISSUE_KEYS, "action") if key in item)


def _sorted_unique(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_identity = {_identity(item): item for item in items}
    return [by_identity[key] for key in sorted(by_identity)]


def _parse_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in {'"', "'"}:
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError("unbalanced metadata quote")
        return value[1:-1]
    if value[-1:] in {'"', "'"}:
        raise ValueError("unbalanced metadata quote")
    return value.split(" #", 1)[0].strip()


def _parse_meta(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    values: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if "\t" in line:
            raise ValueError("tab indentation is forbidden")
        if not line.strip() or line.startswith("#"):
            index += 1
            continue
        match = re.fullmatch(r"([a-z_][a-z0-9_]*):(?:[ ](.*))?", line)
        if match is None:
            raise ValueError("malformed metadata key or indentation")
        key = match.group(1)
        if key in values:
            raise ValueError("duplicate metadata key")
        raw = (match.group(2) or "").rstrip()
        if raw.startswith("|") or raw.startswith(">"):
            if key != "notes" or raw != "|":
                raise ValueError("unsupported metadata block scalar")
            index += 1
            content: list[str] = []
            while index < len(lines):
                current = lines[index]
                if current and not current.startswith("  "):
                    break
                content.append(current[2:] if current else "")
                index += 1
            values[key] = "\n".join(content).rstrip("\n") + "\n"
            continue
        if raw == "":
            index += 1
            block: list[str] = []
            while index < len(lines):
                current = lines[index]
                if not current.strip():
                    block.append("")
                    index += 1
                    continue
                if not current.startswith("  ") or current.startswith("   "):
                    break
                block.append(current[2:])
                index += 1
            nonblank = [item for item in block if item]
            if nonblank and all(item.startswith("- ") for item in nonblank):
                values[key] = [_parse_scalar(item[2:]) for item in nonblank]
            elif nonblank and all(re.fullmatch(r"[a-z_][a-z0-9_]*:.*", item) for item in nonblank):
                mapping: dict[str, str] = {}
                for item in nonblank:
                    child, child_raw = item.split(":", 1)
                    if child in mapping:
                        raise ValueError("duplicate metadata mapping key")
                    mapping[child] = _parse_scalar(child_raw)
                values[key] = mapping
            elif nonblank:
                raise ValueError("malformed metadata container")
            else:
                values[key] = ""
            continue
        if raw.startswith("[") or raw.startswith("{"):
            if not ((raw.startswith("[") and raw.endswith("]")) or (raw.startswith("{") and raw.endswith("}"))):
                raise ValueError("malformed metadata inline container")
            try:
                values[key] = json.loads(raw.replace("'", '"'))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError("malformed metadata inline container") from exc
        else:
            parsed = _parse_scalar(raw)
            values[key] = raw if key in BOOL_FIELDS and raw not in {"true", "false"} else parsed
        index += 1
    if "volatile_fields" in values and not isinstance(values["volatile_fields"], list):
        raise ValueError("volatile_fields must be a list")
    if "tolerance" in values and not isinstance(values["tolerance"], dict):
        raise ValueError("tolerance must be a mapping")
    if "expires_at" in values and not isinstance(values["expires_at"], str):
        raise ValueError("expires_at must be a scalar")
    return values


def _metadata_review_text(values: dict[str, Any]) -> str:
    parts: list[str] = []
    for value in values.values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
    return "\n".join(parts)


def _parse_expiry(value: str) -> dt.datetime | None:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _validate_json(path: Path, selected_root: Path) -> str | None:
    if _is_symlink(path) or not _contained(path, selected_root):
        return "JSON_UNREADABLE"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "JSON_UNREADABLE"
    try:
        value = json.loads(
            text,
            parse_constant=lambda constant: (_ for _ in ()).throw(ValueError(constant)),
        )
    except (json.JSONDecodeError, ValueError):
        return "JSON_MALFORMED"
    return None if isinstance(value, dict) else "JSON_ROOT_NOT_OBJECT"


def _bare_report_fields(text: str) -> dict[str, Any] | None:
    recognized: dict[str, str] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"(status|consistency_rate|total|replayed|source):[ ]*(.*)", line)
        if match is None:
            continue
        key, value = match.groups()
        if key in recognized:
            return None
        recognized[key] = value.strip()
    if set(recognized) - {"status", "consistency_rate", "total", "replayed", "source"}:
        return None
    if not {"status", "total", "replayed", "source"}.issubset(recognized):
        return None
    if not re.fullmatch(r"[0-9]+", recognized["total"]) or not re.fullmatch(
        r"[0-9]+", recognized["replayed"]
    ):
        return None
    if not recognized["source"]:
        return None
    if "consistency_rate" in recognized:
        try:
            rate = float(recognized["consistency_rate"])
        except ValueError:
            return None
        if not math.isfinite(rate) or not 0.0 <= rate <= 1.0:
            return None
    return {
        "status": recognized["status"],
        "total": int(recognized["total"]),
        "replayed": int(recognized["replayed"]),
        "source": recognized["source"],
    }


def _bare_report_claimed(text: str) -> bool:
    return re.search(
        r"(?m)^(?:status|consistency_rate|total|replayed|source):[ ]*.*$", text
    ) is not None


def _canonical_report_fields(text: str, report_relative: str) -> dict[str, Any] | None:
    if len(re.findall(r"(?m)^## Canonical Result$", text)) != 1:
        return None
    match = re.search(r"(?ms)^## Canonical Result\n\n?```json\n(.*?)\n```(?:\n|$)", text)
    if (
        match is None
        or len(re.findall(r"(?m)^```json$", text)) != 1
        or len(re.findall(r"(?m)^```$", text)) != 1
    ):
        return None
    try:
        value = parse_result_json(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return None
    if not _exact_keys(value, CONSISTENCY_KEYS):
        return None
    integer_keys = (
        "exit_code",
        "total",
        "selected",
        "replayed",
        "compared",
        "fatal_error_count",
        "status_mismatch_count",
        "comparable_fields",
        "matched_fields",
        "structure_ok",
        "empty_snapshot_count",
    )
    if any(not _is_actual_int(value[key]) or value[key] < 0 for key in integer_keys):
        return None
    rate = value["consistency_rate"]
    threshold = value["threshold"]
    if (
        value["status"] != "PASS"
        or value["exit_code"] != 0
        or value["no_data"] is not False
        or value["total"] <= 0
        or value["selected"] != value["total"]
        or value["replayed"] != value["total"]
        or value["compared"] != value["total"]
        or value["fatal_error_count"] != 0
        or value["status_mismatch_count"] != 0
        or not 0 < value["structure_ok"] <= value["compared"]
        or not 0 <= value["empty_snapshot_count"] <= value["total"]
        or value["comparable_fields"] <= 0
        or not 0 <= value["matched_fields"] <= value["comparable_fields"]
        or isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or not 0.0 <= rate <= 1.0
        or isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or not 0.0 <= threshold <= 1.0
        or rate != round(value["matched_fields"] / value["comparable_fields"], 4)
        or rate < threshold
        or value["failure_kind"] is not None
        or value["report_artifact"] != report_relative
        or value["trend_artifact"] != "reports/trend.json"
    ):
        return None
    return {
        "status": "PASS",
        "total": value["total"],
        "replayed": value["replayed"],
        "source": "consistency_report",
    }


def _report_time(name: str) -> dt.datetime | None:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-replay\.md", name)
    if match is None:
        return None
    try:
        date = dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None
    return dt.datetime.combine(date, dt.time.min, tzinfo=dt.timezone.utc)


def _validated_report(
    path: Path, selected_root: Path, expected_triplets: int
) -> tuple[dict[str, Any] | None, str | None]:
    if _is_symlink(path) or not _contained(path, selected_root):
        return None, "REPORT_MALFORMED"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "REPORT_MALFORMED"
    report_relative = f"reports/{path.name}"
    bare_claim = _bare_report_claimed(text)
    bare = _bare_report_fields(text) if bare_claim else None
    canonical_claim = "## Canonical Result" in text or "```json" in text
    if bare_claim and canonical_claim:
        return None, "REPORT_MALFORMED"
    canonical = _canonical_report_fields(text, report_relative) if canonical_claim else None
    if (bare is None) == (canonical is None):
        return None, "REPORT_MALFORMED"
    fields = bare if bare is not None else canonical
    assert fields is not None
    if fields["status"] != "PASS":
        return None, "REPORT_NOT_PASS"
    total = fields["total"]
    replayed = fields["replayed"]
    if total <= 0 or replayed <= 0 or replayed != total or total != expected_triplets:
        return None, "REPORT_COVERAGE_MISMATCH"
    return {
        "status": "PASS",
        "total": total,
        "replayed": replayed,
        "source": _sanitize_identifier(fields["source"], "source"),
    }, None


def _scan_report(
    selected_root: Path,
    selected_root_display: str,
    domain: str,
    site_root: Path,
    now: dt.datetime,
    recent_days: int,
    expected_triplets: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    reports = selected_root / "reports"
    if _lexists(reports) and (
        _is_symlink(reports) or not reports.is_dir() or not _contained(reports, selected_root)
    ):
        return None, [
            _issue("REPORT", "REPORT_MALFORMED", domain=domain, selected_root=selected_root_display)
        ]
    candidates = sorted(reports.glob("*-replay.md")) if reports.is_dir() else []
    if not candidates:
        return None, [_issue("REPORT", "REPORT_MISSING", domain=domain, selected_root=selected_root_display)]
    authoritative = max(
        candidates,
        key=lambda path: (_report_time(path.name) or dt.datetime.max.replace(tzinfo=dt.timezone.utc), _display_path(path, site_root)),
    )
    display = _display_path(authoritative, site_root)
    report_time = _report_time(authoritative.name)
    if report_time is None or not _selected_report_path_matches(display, selected_root_display):
        return None, [_issue("REPORT", "REPORT_MALFORMED", domain=domain, selected_root=selected_root_display)]
    if report_time > now:
        return None, [_issue("REPORT", "REPORT_STALE", domain=domain, selected_root=selected_root_display)]
    parsed, reason = _validated_report(authoritative, selected_root, expected_triplets)
    if parsed is None:
        return None, [_issue("REPORT", reason or "REPORT_MALFORMED", domain=domain, selected_root=selected_root_display)]
    cutoff = now - dt.timedelta(days=recent_days)
    if report_time < cutoff:
        return None, [_issue("REPORT", "REPORT_STALE", domain=domain, selected_root=selected_root_display)]
    return {
        "path": display,
        **parsed,
        "recent": True,
    }, []


def _scan_domain(
    domain_dir: Path,
    site_root: Path,
    mode: Mode,
    now: dt.datetime,
    recent_days: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    domain = domain_dir.name
    if not _is_safe_domain(domain):
        raise ValueError("unsafe physical domain")
    fixtures = domain_dir / "fixtures"
    selected_root, snapshots = select_fixture_layout(fixtures)
    selected_display = _display_path(selected_root, site_root)
    selected_layout = "active" if selected_root == fixtures / "active" else "legacy"
    selected_root_invalid = (
        _is_symlink(fixtures)
        or _is_symlink(selected_root)
        or not _contained(selected_root, fixtures)
    )
    if selected_root_invalid or _is_symlink(snapshots) or not _contained(snapshots, selected_root):
        snapshot_state = "NOT_DIRECTORY"
    elif not _lexists(snapshots):
        snapshot_state = "MISSING"
    elif not snapshots.is_dir():
        snapshot_state = "NOT_DIRECTORY"
    else:
        snapshot_state = "DIRECTORY"

    issues: list[dict[str, Any]] = []
    if snapshot_state != "DIRECTORY":
        reason = "SNAPSHOTS_MISSING" if snapshot_state == "MISSING" else "SNAPSHOTS_NOT_DIRECTORY"
        issues.append(_issue("DOMAIN", reason, domain=domain, selected_root=selected_display))
        request_paths: list[Path] = []
        response_paths: list[Path] = []
        metadata_paths: list[Path] = []
    else:
        request_paths = sorted(snapshots.glob("*.req.json"))
        response_paths = sorted(snapshots.glob("*.resp.json"))
        metadata_paths = sorted(snapshots.glob("*.meta.yaml"))

    req = {path.name[:-9]: path for path in request_paths}
    resp = {path.name[:-10]: path for path in response_paths}
    meta = {path.name[:-10]: path for path in metadata_paths}
    complete = sorted(set(req) & set(resp) & set(meta))
    all_prefixes = sorted(set(req) | set(resp) | set(meta))
    for prefix in all_prefixes:
        if prefix in complete:
            continue
        for present, reason in ((req, "ORPHAN_REQ"), (resp, "ORPHAN_RESP"), (meta, "ORPHAN_META")):
            if prefix in present:
                issues.append(
                    _issue(
                        "FIXTURE",
                        reason,
                        domain=domain,
                        prefix=prefix,
                        selected_root=selected_display,
                    )
                )
    valid_triplets = 0
    for prefix in complete:
        before = len(issues)
        for path in (req[prefix], resp[prefix]):
            reason = _validate_json(path, selected_root)
            if reason:
                issues.append(
                    _issue("FIXTURE", reason, domain=domain, prefix=prefix, selected_root=selected_display)
                )
        meta_readable = not _is_symlink(meta[prefix]) and _contained(meta[prefix], selected_root)
        try:
            if not meta_readable:
                raise OSError("unsafe metadata path")
            meta_text = meta[prefix].read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            meta_text = ""
            meta_readable = False
            issues.append(
                _issue("FIXTURE", "META_UNREADABLE", domain=domain, prefix=prefix, selected_root=selected_display)
            )
        if meta_readable:
            try:
                values = _parse_meta(meta_text)
            except ValueError:
                issues.append(
                    _issue("FIXTURE", "META_UNREADABLE", domain=domain, prefix=prefix, selected_root=selected_display)
                )
                continue
            missing = [
                key
                for key in META_REQUIRED
                if key not in values
                or (key != "expires_at" and (not isinstance(values[key], str) or not values[key]))
            ]
            if missing:
                issues.append(
                    _issue("FIXTURE", "META_REQUIRED_MISSING", domain=domain, prefix=prefix, selected_root=selected_display)
                )
            if any(values.get(key) not in {"true", "false"} for key in BOOL_FIELDS):
                issues.append(
                    _issue("FIXTURE", "META_BOOL_INVALID", domain=domain, prefix=prefix, selected_root=selected_display)
                )
            if values.get("category") not in ALLOWED_CATEGORIES:
                issues.append(
                    _issue("FIXTURE", "CATEGORY_FORBIDDEN", domain=domain, prefix=prefix, selected_root=selected_display)
                )
            if values.get("schema_version") != "fixture-meta-v2":
                issues.append(
                    _issue("FIXTURE", "META_UNREADABLE", domain=domain, prefix=prefix, selected_root=selected_display)
                )
            if mode is not Mode.OFFLINE:
                expiry = values.get("expires_at")
                if expiry is None or expiry == "":
                    reason = "EXPIRY_MISSING"
                elif not isinstance(expiry, str):
                    reason = "EXPIRY_INVALID"
                else:
                    parsed_expiry = _parse_expiry(expiry)
                    reason = "EXPIRY_INVALID" if parsed_expiry is None else "EXPIRED" if parsed_expiry <= now else ""
                if reason:
                    issues.append(
                        _issue("FIXTURE", reason, domain=domain, prefix=prefix, selected_root=selected_display)
                    )
                review_pending = values.get("review_status") != "reviewed"
                review_text = _metadata_review_text(values)
                if review_pending or any(pattern.search(review_text) for pattern in REVIEW_PATTERNS):
                    issues.append(
                        _issue("FIXTURE", "REVIEW_PENDING", domain=domain, prefix=prefix, selected_root=selected_display)
                    )
        new_structure = any(item["reason"] in STRUCTURE_REASONS for item in issues[before:])
        new_freshness = any(item["reason"] in FRESHNESS_REASONS for item in issues[before:])
        if not new_structure and (mode is Mode.OFFLINE or not new_freshness):
            valid_triplets += 1

    if snapshot_state == "DIRECTORY" and not complete and not any(
        item["reason"] in STRUCTURE_REASONS for item in issues
    ):
        issues.append(_issue("DOMAIN", "NO_COMPLETE_TRIPLETS", domain=domain, selected_root=selected_display))

    selected_report: dict[str, Any] | None = None
    if mode is not Mode.OFFLINE and complete:
        selected_report, report_issues = _scan_report(
            selected_root,
            selected_display,
            domain,
            site_root,
            now,
            recent_days,
            len(complete),
        )
        issues.extend(report_issues)

    issues = _sorted_unique(issues)
    structure_count = sum(item["reason"] in STRUCTURE_REASONS for item in issues)
    freshness_count = sum(item["reason"] in FRESHNESS_REASONS for item in issues)
    if mode is Mode.OFFLINE:
        source_freshness = "not_checked"
    elif not complete:
        source_freshness = "missing"
    elif freshness_count:
        source_freshness = "stale"
    else:
        source_freshness = "fresh"
    domain_result = {
        "domain": domain,
        "selected_root": selected_display,
        "selected_layout": selected_layout,
        "snapshots_state": snapshot_state,
        "request_files": len(req),
        "response_files": len(resp),
        "metadata_files": len(meta),
        "complete_triplets": len(complete),
        "valid_triplets": valid_triplets,
        "structure_issue_count": structure_count,
        "freshness_issue_count": freshness_count,
        "source_freshness": source_freshness,
        "selected_report": selected_report,
    }
    return domain_result, issues


def _tasks_for(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for item in issues:
        mapped = TASK_MAPPING.get(item["reason"])
        if mapped is None:
            continue
        expected_scope, action = mapped
        task = {key: item[key] for key in ISSUE_KEYS}
        task["scope"] = expected_scope
        task["action"] = action
        tasks.append(task)
    return _sorted_unique(tasks)


def _status_for(
    mode: Mode,
    require_data: bool,
    totals: dict[str, int],
    issues: list[dict[str, Any]],
) -> tuple[str, int, str]:
    if totals["structure_issue_count"]:
        return "STRUCTURE_INVALID", 1, "NO_CAPABILITY"
    domain_no_data = any(item["reason"] == "NO_COMPLETE_TRIPLETS" for item in issues)
    if totals["complete_triplets"] == 0 or domain_no_data:
        if mode is Mode.REFRESH:
            return "RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN"
        if require_data or mode is Mode.STRICT:
            return "NO_DATA", 4, "NO_CAPABILITY"
        capability = "STRUCTURE_ONLY" if mode is Mode.OFFLINE else "DIAGNOSTIC_ONLY"
        return "NO_DATA", 0, capability
    if mode is not Mode.OFFLINE and any(item["reason"] in FRESHNESS_REASONS for item in issues):
        if mode is Mode.DIAGNOSTIC:
            return "STALE", 0, "DIAGNOSTIC_ONLY"
        if mode is Mode.STRICT:
            return "STALE", 3, "NO_CAPABILITY"
        return "RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN"
    if mode is Mode.OFFLINE:
        return "STRUCTURE_ONLY", 0, "STRUCTURE_ONLY"
    if mode is Mode.DIAGNOSTIC:
        return "PASS", 0, "DIAGNOSTIC_ONLY"
    if mode is Mode.STRICT:
        return "PASS", 0, "FRESH_FIXTURE_GATE"
    return "PASS", 0, "REFRESH_NOT_REQUIRED"


@dataclass(frozen=True)
class FixtureGateResult:
    value: dict[str, Any]

    @property
    def exit_code(self) -> int:
        return int(self.value["exit_code"])

    def to_dict(self) -> dict[str, Any]:
        return self.value

    def serialize(self) -> str:
        return serialize_result(self.value)


def _base_result(
    tool: str,
    mode: Mode,
    status: str,
    exit_code: int,
    capability: str,
    *,
    no_data: bool,
    freshness_checked: bool,
    totals: dict[str, int] | None = None,
    domains: list[dict[str, Any]] | None = None,
    issues: list[dict[str, Any]] | None = None,
    refresh_tasks: list[dict[str, Any]] | None = None,
    artifact: dict[str, str] | None = None,
) -> FixtureGateResult:
    return FixtureGateResult(
        {
            "schema_version": SCHEMA_VERSION,
            "tool": tool,
            "mode": mode.value,
            "status": status,
            "exit_code": exit_code,
            "capability": capability,
            "no_data": no_data,
            "freshness_checked": freshness_checked,
            "replay_lineage": "NOT_CHECKED" if mode is Mode.OFFLINE else "UNKNOWN",
            "totals": totals or _zero_totals(),
            "domains": domains or [],
            "issues": issues or [],
            "refresh_tasks": refresh_tasks or [],
            "artifact": artifact,
        }
    )


def invalid_argument_result(tool: str, mode: Mode, detail: str = "") -> FixtureGateResult:
    del detail
    return _base_result(
        tool,
        mode,
        "INVALID_ARGUMENT",
        2,
        "NO_CAPABILITY",
        no_data=False,
        freshness_checked=False,
        issues=[_issue("ROOT", "INVALID_ARGUMENT")],
    )


def _internal_result(
    tool: str,
    mode: Mode,
    *,
    totals: dict[str, int] | None = None,
    domains: list[dict[str, Any]] | None = None,
    issues: list[dict[str, Any]] | None = None,
    tasks: list[dict[str, Any]] | None = None,
    freshness_checked: bool = False,
) -> FixtureGateResult:
    retained = bool(domains)
    retained_totals = totals if retained else _zero_totals()
    retained_issues = issues if retained else []
    retained_tasks = tasks if retained else []
    return _base_result(
        tool,
        mode,
        "INTERNAL_ERROR",
        5,
        "NO_CAPABILITY",
        no_data=bool(retained and retained_totals and retained_totals["complete_triplets"] == 0),
        freshness_checked=bool(retained and freshness_checked),
        totals=retained_totals,
        domains=domains if retained else [],
        issues=_sorted_unique([*retained_issues, _issue("ROOT", "INTERNAL_ERROR")]),
        refresh_tasks=retained_tasks,
    )


def _aggregate_result_evidence(
    mode: Mode,
    domains: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    domains.sort(key=lambda item: item["domain"])
    issues = _sorted_unique(issues)
    totals = _zero_totals()
    totals["domains_selected"] = len(domains)
    totals["domains_with_snapshots"] = sum(
        item["snapshots_state"] == "DIRECTORY" for item in domains
    )
    for key in ("request_files", "response_files", "metadata_files", "complete_triplets", "valid_triplets"):
        totals[key] = sum(item[key] for item in domains)
    totals["expired_count"] = sum(item["reason"] == "EXPIRED" for item in issues)
    totals["review_pending_count"] = sum(item["reason"] == "REVIEW_PENDING" for item in issues)
    totals["missing_expiry_count"] = sum(item["reason"] == "EXPIRY_MISSING" for item in issues)
    totals["structure_issue_count"] = sum(item["reason"] in STRUCTURE_REASONS for item in issues)
    totals["freshness_issue_count"] = sum(item["reason"] in FRESHNESS_REASONS for item in issues)
    tasks = _tasks_for(issues) if mode is Mode.REFRESH else []
    totals["refresh_task_count"] = len(tasks)
    return totals, issues, tasks


def _empty_domain_result(
    domain_dir: Path, site_root: Path, mode: Mode, *, select_layout: bool = True
) -> dict[str, Any]:
    fixtures = domain_dir / "fixtures"
    selected_root = select_fixture_layout(fixtures)[0] if select_layout else fixtures
    selected_layout = "active" if selected_root == fixtures / "active" else "legacy"
    return {
        "domain": domain_dir.name,
        "selected_root": _display_path(selected_root, site_root),
        "selected_layout": selected_layout,
        "snapshots_state": "MISSING",
        "request_files": 0,
        "response_files": 0,
        "metadata_files": 0,
        "complete_triplets": 0,
        "valid_triplets": 0,
        "structure_issue_count": 1,
        "freshness_issue_count": 0,
        "source_freshness": "not_checked" if mode is Mode.OFFLINE else "missing",
        "selected_report": None,
    }


def _normalize_output_target(out: Path) -> Path:
    target = Path(os.path.abspath(REPO_ROOT / out if not out.is_absolute() else out))
    try:
        relative = target.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError("artifact output must be inside repository root") from exc
    if not relative.parts:
        raise ValueError("artifact output must be a strict repository descendant")
    return target


def run_gate(
    *,
    site_root: Path,
    tool: str,
    mode: Mode = Mode.DIAGNOSTIC,
    require_data: bool = False,
    recent_days: int = 30,
    domains: Sequence[str] = (),
    out: Path | None = None,
    now: dt.datetime | None = None,
) -> FixtureGateResult:
    if tool not in TOOLS or not isinstance(mode, Mode):
        raise ValueError("run_gate requires a fixed tool and Mode enum")
    require_data = bool(require_data or mode is Mode.STRICT)
    site_root = Path(os.path.abspath(site_root))
    if type(recent_days) is not int or recent_days <= 0 or (
        out is not None and mode is not Mode.REFRESH
    ):
        return invalid_argument_result(tool, mode)
    try:
        output_target = _normalize_output_target(out) if out is not None else None
    except ValueError:
        return invalid_argument_result(tool, mode)
    requested = sorted(set(domains))
    if any(not _is_safe_domain(domain) for domain in requested):
        return invalid_argument_result(tool, mode)
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        return invalid_argument_result(tool, mode)
    now = now.astimezone(dt.timezone.utc)

    issues: list[dict[str, Any]] = []
    domain_results: list[dict[str, Any]] = []
    try:
        if not site_root.is_dir() or _is_symlink(site_root):
            issues.append(_issue("ROOT", "SITE_ROOT_MISSING"))
            candidates: list[Path] = []
        elif requested:
            candidates = []
            for domain in requested:
                candidate = site_root / domain
                if not _lexists(candidate):
                    empty = _empty_domain_result(
                        candidate, site_root, mode, select_layout=False
                    )
                    domain_results.append(empty)
                    issues.append(
                        _issue("DOMAIN", "DOMAIN_MISSING", domain=domain, selected_root=empty["selected_root"])
                    )
                elif _is_symlink(candidate) or not candidate.is_dir():
                    empty = _empty_domain_result(
                        candidate, site_root, mode, select_layout=False
                    )
                    domain_results.append(empty)
                    issues.append(
                        _issue("DOMAIN", "DOMAIN_NOT_DIRECTORY", domain=domain, selected_root=empty["selected_root"])
                    )
                else:
                    candidates.append(candidate)
        else:
            candidates = []
            for child in sorted(site_root.iterdir(), key=lambda item: os.fsencode(item.name)):
                if child.name.startswith("_") or _is_symlink(child) or not child.is_dir():
                    continue
                fixtures_entry = child / "fixtures"
                if not _lexists(fixtures_entry):
                    continue
                if not _is_safe_domain(child.name):
                    issues.append(
                        {
                            "scope": "DOMAIN",
                            "domain": _unsafe_domain_identifier(child.name),
                            "prefix": None,
                            "selected_root": None,
                            "reason": "UNSAFE_DOMAIN",
                        }
                    )
                else:
                    candidates.append(child)
            if not candidates and not domain_results and not issues:
                issues.append(_issue("ROOT", "NO_DOMAINS"))
        for candidate in candidates:
            try:
                domain_result, domain_issues = _scan_domain(candidate, site_root, mode, now, recent_days)
            except Exception:
                totals, retained_issues, tasks = _aggregate_result_evidence(mode, domain_results, issues)
                return _internal_result(
                    tool,
                    mode,
                    totals=totals,
                    domains=domain_results,
                    issues=retained_issues,
                    tasks=tasks,
                    freshness_checked=mode is not Mode.OFFLINE,
                )
            domain_results.append(domain_result)
            issues.extend(domain_issues)
    except Exception:
        totals, retained_issues, tasks = _aggregate_result_evidence(mode, domain_results, issues)
        return _internal_result(
            tool,
            mode,
            totals=totals,
            domains=domain_results,
            issues=retained_issues,
            tasks=tasks,
            freshness_checked=mode is not Mode.OFFLINE,
        )

    totals, issues, tasks = _aggregate_result_evidence(mode, domain_results, issues)
    status, exit_code, capability = _status_for(mode, require_data, totals, issues)
    result = _base_result(
        tool,
        mode,
        status,
        exit_code,
        capability,
        no_data=totals["complete_triplets"] == 0,
        freshness_checked=mode is not Mode.OFFLINE,
        totals=totals,
        domains=domain_results,
        issues=issues,
        refresh_tasks=tasks,
    )
    if validate_result_document(
        result.value,
        expected_tool=tool,
        expected_site_root=site_root,
        expected_bindings={
            item["domain"]: (item["selected_root"], item["selected_layout"])
            for item in domain_results
        },
    ):
        return _internal_result(
            tool,
            mode,
            totals=totals,
            domains=domain_results,
            issues=issues,
            tasks=tasks,
            freshness_checked=mode is not Mode.OFFLINE,
        )
    if output_target is not None:
        try:
            result = _publish_artifact(
                output_target,
                result,
                site_root,
                {
                    item["domain"]: (item["selected_root"], item["selected_layout"])
                    for item in domain_results
                },
            )
        except PublicationStop:
            raise
        except PublicationPreflightError:
            return _internal_result(tool, mode)
        except Exception:
            return _internal_result(
                tool,
                mode,
                totals=totals,
                domains=domain_results,
                issues=issues,
                tasks=tasks,
                freshness_checked=mode is not Mode.OFFLINE,
            )
    return result


def serialize_result(value: dict[str, Any] | FixtureGateResult) -> str:
    raw = value.value if isinstance(value, FixtureGateResult) else value
    ordered = {key: raw[key] for key in TOP_LEVEL_KEYS}
    return json.dumps(ordered, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _artifact_bytes(result: FixtureGateResult) -> bytes:
    return (result.serialize() + "\n").encode("utf-8")


def _artifact_claim_payload(value: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(value)
    canonical["artifact"] = None
    return canonical


def _artifact_claim_bytes(value: dict[str, Any]) -> bytes:
    return (serialize_result(_artifact_claim_payload(value)) + "\n").encode("utf-8")


def _artifact_claim_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(_artifact_claim_bytes(value)).hexdigest()


def _directory_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _require_dir_fd_publication() -> None:
    required = (os.open, os.stat, os.rename, os.unlink, os.mkdir, os.rmdir)
    if (
        os.name != "posix"
        or
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or any(function not in os.supports_dir_fd for function in required)
        or os.stat not in os.supports_follow_symlinks
    ):
        raise OSError("race-resistant artifact publication is unavailable")


def _validate_output_chain(
    trusted_root: Path,
    root_fd: int,
    links: list[tuple[int, str, int]],
) -> None:
    root_entry = os.stat(trusted_root, follow_symlinks=False)
    root_held = os.fstat(root_fd)
    if (
        not stat.S_ISDIR(root_entry.st_mode)
        or _directory_identity(root_entry) != _directory_identity(root_held)
    ):
        raise OSError("trusted output root identity changed")
    for parent_fd, name, child_fd in links:
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        held = os.fstat(child_fd)
        if not stat.S_ISDIR(entry.st_mode) or _directory_identity(entry) != _directory_identity(held):
            raise OSError("artifact output ancestor identity changed")


def _open_output_parent(
    trusted_root: Path, target: Path
) -> tuple[list[int], list[tuple[int, str, int]]]:
    _require_dir_fd_publication()
    relative_parent = target.parent.relative_to(trusted_root)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds: list[int] = []
    links: list[tuple[int, str, int]] = []
    try:
        root_fd = os.open(trusted_root, flags)
        fds.append(root_fd)
        _validate_output_chain(trusted_root, root_fd, links)
        for part in relative_parent.parts:
            child_fd = os.open(part, flags, dir_fd=fds[-1])
            links.append((fds[-1], part, child_fd))
            fds.append(child_fd)
            _validate_output_chain(trusted_root, root_fd, links)
        return fds, links
    except Exception:
        close_error: Exception | None = None
        for open_fd in reversed(fds):
            try:
                _close_raw_fd(open_fd, committed=False)
            except Exception as exc:
                close_error = close_error or exc
        if close_error is not None:
            raise close_error
        raise


def _create_temp_at(parent_fd: int, target_name: str) -> tuple[int, str]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    for _ in range(100):
        name = f".{target_name}.{secrets.token_hex(12)}.tmp"
        try:
            return os.open(name, flags, 0o600, dir_fd=parent_fd), name
        except FileExistsError:
            continue
    raise OSError("unable to allocate artifact staging file")


def _target_identity(parent_fd: int, name: str) -> tuple[int, int] | None:
    try:
        value = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(value.st_mode):
        raise OSError("artifact target is not a regular file")
    return _directory_identity(value)


def _rename_commit(parent_fd: int, source: str, target: str) -> None:
    try:
        os.rename(source, target, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno in {errno.EINTR, errno.EIO}:
            raise PublicationStop("ambiguous rename result") from exc
        raise


def _unlink_at(parent_fd: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=parent_fd)
    except FileNotFoundError:
        pass


def _close_raw_fd(fd: int, *, committed: bool) -> None:
    try:
        os.close(fd)
    except OSError as exc:
        # A failed close is ambiguous: the numeric descriptor may already have
        # been reused, so it must never be inspected or closed again.
        raise PublicationStop("descriptor close state is ambiguous") from exc


def _fdopen_owned(fd: int, mode: str) -> Any:
    return os.fdopen(fd, mode, closefd=False)


def _close_file_owned(handle: Any, fd: int) -> None:
    close_error: Exception | None = None
    try:
        handle.close()
    except Exception as exc:
        close_error = exc
    # closefd=False keeps raw ownership here even when file-object close fails.
    _close_raw_fd(fd, committed=False)
    if close_error is not None:
        raise OSError("file close failed before descriptor close") from close_error


def _cleanup_owned_temp(parent_fd: int, name: str, identity: tuple[int, int]) -> None:
    last_error: Exception | None = None
    for _ in range(2):
        if _target_identity(parent_fd, name) != identity:
            raise PublicationStop("owned staging identity changed")
        try:
            os.unlink(name, dir_fd=parent_fd)
            return
        except OSError as exc:
            last_error = exc
    raise PublicationStop("owned staging cleanup failed") from last_error


def _publication_platform_probe(trusted_dev: int) -> None:
    _require_dir_fd_publication()
    with tempfile.TemporaryDirectory(prefix="ll0004-rename-probe-") as raw:
        probe = Path(raw)
        if probe.stat().st_dev != trusted_dev:
            raise OSError("publication probe device mismatch")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        probe_fd = os.open(probe, flags)
        source_fd = -1
        try:
            source_fd = os.open(
                "source",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=probe_fd,
            )
            os.write(source_fd, b"probe\n")
            os.fsync(source_fd)
            owned_source_fd = source_fd
            source_fd = -1
            _close_raw_fd(owned_source_fd, committed=False)
            os.mkdir("destination", dir_fd=probe_fd)
            source_before = os.stat("source", dir_fd=probe_fd, follow_symlinks=False)
            destination_before = os.stat("destination", dir_fd=probe_fd, follow_symlinks=False)
            entries_before = sorted(os.listdir(probe_fd))
            try:
                os.rename(
                    "source",
                    "destination",
                    src_dir_fd=probe_fd,
                    dst_dir_fd=probe_fd,
                )
            except OSError as exc:
                if exc.errno not in {errno.EISDIR, errno.ENOTDIR}:
                    raise OSError("publication rename probe failed") from exc
            else:
                raise OSError("publication rename probe mutated destination")
            source_after = os.stat("source", dir_fd=probe_fd, follow_symlinks=False)
            destination_after = os.stat("destination", dir_fd=probe_fd, follow_symlinks=False)
            read_fd = os.open("source", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=probe_fd)
            try:
                source_bytes = os.read(read_fd, 64)
            finally:
                _close_raw_fd(read_fd, committed=False)
            if (
                _directory_identity(source_before) != _directory_identity(source_after)
                or _directory_identity(destination_before) != _directory_identity(destination_after)
                or not stat.S_ISREG(source_after.st_mode)
                or not stat.S_ISDIR(destination_after.st_mode)
                or source_bytes != b"probe\n"
                or entries_before != sorted(os.listdir(probe_fd))
            ):
                raise OSError("publication rename probe nonmutation check failed")
            os.unlink("source", dir_fd=probe_fd)
            os.rmdir("destination", dir_fd=probe_fd)
        finally:
            if source_fd >= 0:
                _close_raw_fd(source_fd, committed=False)
            _close_raw_fd(probe_fd, committed=False)


def _publish_artifact(
    target: Path,
    result: FixtureGateResult,
    expected_site_root: Path,
    expected_bindings: dict[str, tuple[str, str]],
) -> FixtureGateResult:
    content = _artifact_bytes(result)
    digest = hashlib.sha256(content).hexdigest()
    artifact = {"path": target.relative_to(REPO_ROOT).as_posix(), "sha256": digest}
    prepared_value = dict(result.value)
    prepared_value["artifact"] = artifact
    prepared = FixtureGateResult(prepared_value)
    if _prepared_artifact_consistency_errors(target, prepared.value):
        raise OSError("prepared artifact result is invalid")

    fds: list[int] = []
    links: list[tuple[int, str, int]] = []
    raw_fd = -1
    temp_name: str | None = None
    temp_identity: tuple[int, int] | None = None
    committed = False
    try:
        fds, links = _open_output_parent(REPO_ROOT, target)
        root_fd, parent_fd = fds[0], fds[-1]
        if os.fstat(root_fd).st_dev != os.fstat(parent_fd).st_dev:
            raise OSError("trusted root and output parent device mismatch")
        try:
            _publication_platform_probe(os.fstat(root_fd).st_dev)
        except PublicationStop:
            raise
        except Exception as exc:
            raise PublicationPreflightError("publication platform admission failed") from exc
        _validate_output_chain(REPO_ROOT, root_fd, links)
        prior_identity = _target_identity(parent_fd, target.name)
        raw_fd, temp_name = _create_temp_at(parent_fd, target.name)
        temp_identity = _directory_identity(os.fstat(raw_fd))

        write_handle = _fdopen_owned(raw_fd, "wb")
        write_fd = raw_fd
        raw_fd = -1
        try:
            write_handle.write(content)
            write_handle.flush()
            os.fsync(write_fd)
        finally:
            _close_file_owned(write_handle, write_fd)

        verify_fd = os.open(temp_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        try:
            verify_handle = _fdopen_owned(verify_fd, "rb")
        except Exception:
            _close_raw_fd(verify_fd, committed=False)
            raise
        try:
            verified = verify_handle.read()
            verified_identity = _directory_identity(os.fstat(verify_fd))
        finally:
            _close_file_owned(verify_handle, verify_fd)
        if verified != content or verified_identity != temp_identity:
            raise OSError("artifact staging verification failed")
        _validate_output_chain(REPO_ROOT, root_fd, links)
        if _target_identity(parent_fd, target.name) != prior_identity:
            raise OSError("artifact target identity changed before commit")
        if _target_identity(parent_fd, temp_name) != temp_identity:
            raise OSError("artifact staging identity changed before commit")

        _rename_commit(parent_fd, temp_name, target.name)
        committed = True
        temp_name = None
        return prepared
    finally:
        final_error: Exception | None = None
        if raw_fd >= 0:
            try:
                _close_raw_fd(raw_fd, committed=committed)
            except Exception as exc:
                final_error = exc
        if not committed and temp_name is not None and temp_identity is not None and fds:
            try:
                _cleanup_owned_temp(fds[-1], temp_name, temp_identity)
            except Exception as exc:
                final_error = final_error or exc
        for open_fd in reversed(fds):
            try:
                _close_raw_fd(open_fd, committed=committed)
            except Exception as exc:
                final_error = final_error or exc
        if final_error is not None and not committed:
            raise final_error


def _exact_keys(value: Any, keys: tuple[str, ...]) -> bool:
    return isinstance(value, dict) and tuple(value.keys()) == keys


def parse_result_json(text: str) -> Any:
    """Parse one strict JSON document, rejecting duplicate keys and constants."""

    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    def reject_constant(_: str) -> Any:
        raise ValueError("non-finite JSON constant")

    return json.loads(
        text,
        object_pairs_hook=object_without_duplicates,
        parse_constant=reject_constant,
    )


def validate_result_document(
    value: Any,
    expected_tool: str | None = None,
    expected_site_root: Path | None = None,
    expected_bindings: dict[str, tuple[str, str]] | None = None,
    expected_out: Path | None = None,
) -> list[str]:
    """Total exact-schema validator for every decoded JSON value."""
    try:
        errors = _validate_result_document(
            value,
            expected_site_root=expected_site_root,
            expected_bindings=expected_bindings,
            expected_out=expected_out,
        )
        if expected_tool is not None and (
            expected_tool not in TOOLS or not isinstance(value, dict) or value.get("tool") != expected_tool
        ):
            errors.append("tool producer binding")
        return sorted(set(errors))
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return ["malformed value"]


def _validate_result_document(
    value: Any,
    *,
    expected_site_root: Path | None = None,
    expected_bindings: dict[str, tuple[str, str]] | None = None,
    expected_out: Path | None = None,
) -> list[str]:
    """Return deterministic exact-schema validation errors for workflow consumers."""
    errors: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)

    if not _exact_keys(value, TOP_LEVEL_KEYS):
        return ["top-level fields/order mismatch"]
    if not _is_actual_int(value["schema_version"]) or value["schema_version"] != 1:
        fail("schema_version")
    if value["tool"] not in TOOLS:
        fail("tool")
    if value["mode"] not in {mode.value for mode in Mode}:
        fail("mode")
    if value["status"] not in STATUSES:
        fail("status")
    if not _is_actual_int(value["exit_code"]):
        fail("exit_code")
    if value["capability"] not in CAPABILITIES:
        fail("capability")
    for key in ("no_data", "freshness_checked"):
        if not isinstance(value[key], bool):
            fail(key)
    expected_lineage = "NOT_CHECKED" if value["mode"] == "offline" else "UNKNOWN"
    if value["replay_lineage"] != expected_lineage:
        fail("replay_lineage")

    totals = value["totals"]
    if not _exact_keys(totals, TOTAL_KEYS):
        fail("totals fields/order")
        totals = _zero_totals()
    elif any(not _is_actual_int(totals[key]) or totals[key] < 0 for key in TOTAL_KEYS):
        fail("totals types")

    domains = value["domains"]
    if not isinstance(domains, list):
        fail("domains")
        domains = []
    domain_names: list[str] = []
    for item in domains:
        if not _exact_keys(item, DOMAIN_KEYS):
            fail("domain fields/order")
            continue
        domain_names.append(item["domain"] if isinstance(item["domain"], str) else "")
        if not _is_safe_domain(item["domain"]):
            fail("domain name")
        if (
            not _safe_repo_relative_posix_path(item["selected_root"])
            or Path(item["selected_root"]).is_absolute()
        ):
            fail("selected_root")
        if item["selected_layout"] not in {"active", "legacy"}:
            fail("selected_layout")
        elif not _domain_root_binding(
            item, expected_site_root, expected_bindings
        ):
            fail("domain selected_root binding")
        if item["snapshots_state"] not in SNAPSHOT_STATES:
            fail("snapshots_state")
        for key in ("request_files", "response_files", "metadata_files", "complete_triplets", "valid_triplets", "structure_issue_count", "freshness_issue_count"):
            if not _is_actual_int(item[key]) or item[key] < 0:
                fail(f"domain {key}")
        if item["complete_triplets"] > min(item["request_files"], item["response_files"], item["metadata_files"]):
            fail("domain complete_triplets")
        if item["valid_triplets"] > item["complete_triplets"]:
            fail("domain valid_triplets")
        if item["source_freshness"] not in SOURCE_FRESHNESS:
            fail("source_freshness")
        report = item["selected_report"]
        if report is not None:
            if not _exact_keys(report, SELECTED_REPORT_KEYS):
                fail("selected_report fields/order")
            elif (
                not isinstance(report["path"], str)
                or not _safe_repo_relative_posix_path(report["path"])
                or Path(report["path"]).is_absolute()
                or not _selected_report_path_matches(report["path"], item["selected_root"])
                or _report_time(PurePosixPath(report["path"]).name) is None
                or report["status"] != "PASS"
                or not _is_actual_int(report["total"])
                or report["total"] <= 0
                or not _is_actual_int(report["replayed"])
                or report["replayed"] <= 0
                or report["replayed"] != report["total"]
                or report["total"] != item["complete_triplets"]
                or not isinstance(report["source"], str)
                or not report["source"]
                or report["source"] != _sanitize_identifier(report["source"], "source")
                or report["recent"] is not True
            ):
                fail("selected_report")
    if domain_names != sorted(set(domain_names)):
        fail("domains sorting")

    issues = value["issues"]
    if not isinstance(issues, list):
        fail("issues")
        issues = []
    for item in issues:
        if not _exact_keys(item, ISSUE_KEYS):
            fail("issue fields/order")
            continue
        if item["scope"] not in SCOPES or item["reason"] not in REASONS:
            fail("issue enum")
        elif item["scope"] != _reason_scope(item["reason"]):
            fail("issue scope")
        _validate_nullable(item, fail, "issue")
        _validate_safe_identifiers(item, fail, "issue")
        _validate_selected_root_binding(
            item, domains, expected_site_root, fail, "issue"
        )
    if [_identity(item) for item in issues] != sorted(set(_identity(item) for item in issues)):
        fail("issues sorting")
    reason_list = [item.get("reason") for item in issues]
    if "SITE_ROOT_MISSING" in reason_list and reason_list != ["SITE_ROOT_MISSING"]:
        fail("missing root issue cardinality")
    if "NO_DOMAINS" in reason_list and (domains or reason_list != ["NO_DOMAINS"]):
        fail("no domains issue cardinality")
    for domain_item in domains:
        domain_issues = [item for item in issues if item.get("domain") == domain_item.get("domain")]
        structure_present = any(item.get("reason") in STRUCTURE_REASONS for item in domain_issues)
        no_complete = sum(item.get("reason") == "NO_COMPLETE_TRIPLETS" for item in domain_issues)
        expected_no_complete = (
            domain_item.get("snapshots_state") == "DIRECTORY"
            and domain_item.get("complete_triplets") == 0
            and not structure_present
        )
        if no_complete != int(expected_no_complete):
            fail("no complete triplets cardinality")
        failure_reasons = {item.get("reason") for item in domain_issues}
        if failure_reasons & {"DOMAIN_MISSING", "DOMAIN_NOT_DIRECTORY"} and (
            domain_item.get("snapshots_state") != "MISSING"
            or any(domain_item.get(key) != 0 for key in ("request_files", "response_files", "metadata_files", "complete_triplets", "valid_triplets"))
        ):
            fail("failed domain representation")

    tasks = value["refresh_tasks"]
    if not isinstance(tasks, list):
        fail("refresh_tasks")
        tasks = []
    for item in tasks:
        if not _exact_keys(item, TASK_KEYS):
            fail("task fields/order")
            continue
        mapped = TASK_MAPPING.get(item["reason"])
        if mapped != (item["scope"], item["action"]):
            fail("task mapping")
        _validate_nullable(item, fail, "task")
        _validate_safe_identifiers(item, fail, "task")
        _validate_selected_root_binding(
            item, domains, expected_site_root, fail, "task"
        )
    if [_identity(item) for item in tasks] != sorted(set(_identity(item) for item in tasks)):
        fail("tasks sorting")
    expected_tasks = _tasks_for(issues) if value["mode"] == "refresh" else []
    if tasks != expected_tasks:
        fail("task cardinality")

    artifact = value["artifact"]
    if artifact is not None and (
        not _exact_keys(artifact, ARTIFACT_KEYS)
        or not isinstance(artifact["path"], str)
        or not _safe_repo_relative_posix_path(artifact["path"])
        or Path(artifact["path"]).is_absolute()
        or not isinstance(artifact["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None
    ):
        fail("artifact")

    if _exact_keys(value["totals"], TOTAL_KEYS):
        if totals["domains_selected"] != len(domains):
            fail("domains_selected")
        if totals["domains_with_snapshots"] > totals["domains_selected"]:
            fail("domains_with_snapshots")
        if totals["domains_with_snapshots"] != sum(item.get("snapshots_state") == "DIRECTORY" for item in domains):
            fail("domains_with_snapshots total")
        if totals["complete_triplets"] > min(
            totals["request_files"], totals["response_files"], totals["metadata_files"]
        ):
            fail("complete_triplets")
        if totals["valid_triplets"] > totals["complete_triplets"]:
            fail("valid_triplets")
        if totals["refresh_task_count"] != len(tasks):
            fail("refresh_task_count")
        if totals["structure_issue_count"] != sum(item.get("reason") in STRUCTURE_REASONS for item in issues):
            fail("structure_issue_count")
        if totals["freshness_issue_count"] != sum(item.get("reason") in FRESHNESS_REASONS for item in issues):
            fail("freshness_issue_count")
        if totals["expired_count"] != sum(item.get("reason") == "EXPIRED" for item in issues):
            fail("expired_count")
        if totals["review_pending_count"] != sum(item.get("reason") == "REVIEW_PENDING" for item in issues):
            fail("review_pending_count")
        if totals["missing_expiry_count"] != sum(item.get("reason") == "EXPIRY_MISSING" for item in issues):
            fail("missing_expiry_count")
        for key in ("request_files", "response_files", "metadata_files", "complete_triplets", "valid_triplets"):
            if totals[key] != sum(item.get(key, 0) for item in domains):
                fail(f"totals {key}")
        for item in domains:
            domain_issues = [issue for issue in issues if issue.get("domain") == item.get("domain")]
            if item.get("structure_issue_count") != sum(
                issue.get("reason") in STRUCTURE_REASONS for issue in domain_issues
            ):
                fail("domain structure_issue_count")
            if item.get("freshness_issue_count") != sum(
                issue.get("reason") in FRESHNESS_REASONS for issue in domain_issues
            ):
                fail("domain freshness_issue_count")
            invalid_reasons = STRUCTURE_REASONS - {"ORPHAN_REQ", "ORPHAN_RESP", "ORPHAN_META"}
            if value["mode"] != "offline":
                invalid_reasons |= {"EXPIRY_MISSING", "EXPIRY_INVALID", "EXPIRED", "REVIEW_PENDING"}
            invalid_prefixes = {
                issue.get("prefix")
                for issue in domain_issues
                if issue.get("prefix") is not None and issue.get("reason") in invalid_reasons
            }
            if item.get("valid_triplets") != max(0, item.get("complete_triplets", 0) - len(invalid_prefixes)):
                fail("domain valid_triplets predicate")
    zero_internal = value["status"] == "INTERNAL_ERROR" and not domains and not any(totals.values())
    before_scan = value["status"] == "INVALID_ARGUMENT" or zero_internal
    if before_scan:
        if value["no_data"] is not False or any(totals.values()) or domains:
            fail("before-scan invariants")
    elif value["no_data"] != (totals["complete_triplets"] == 0):
        fail("no_data")
    if value["mode"] == "offline" and value["freshness_checked"] is not False:
        fail("offline freshness_checked")
    if value["mode"] == "offline" and (
        any(item.get("reason") in FRESHNESS_REASONS for item in issues)
        or any(totals[key] != 0 for key in (
            "expired_count",
            "review_pending_count",
            "missing_expiry_count",
            "freshness_issue_count",
        ))
        or any(
            item.get("freshness_issue_count") != 0
            or item.get("source_freshness") != "not_checked"
            or item.get("selected_report") is not None
            for item in domains
        )
    ):
        fail("offline freshness evidence")
    if value["status"] == "INVALID_ARGUMENT" and value["freshness_checked"] is not False:
        fail("argument freshness_checked")
    if value["status"] == "INVALID_ARGUMENT" and (
        len(issues) != 1 or issues[0].get("reason") != "INVALID_ARGUMENT"
    ):
        fail("argument issue")
    if value["status"] == "INTERNAL_ERROR" and not any(
        item.get("reason") == "INTERNAL_ERROR" for item in issues
    ):
        fail("internal issue")
    if value["status"] == "INTERNAL_ERROR" and zero_internal:
        if len(issues) != 1 or issues[0].get("reason") != "INTERNAL_ERROR" or tasks:
            fail("zero evidence internal")
    if value["status"] == "INTERNAL_ERROR" and not zero_internal and not domains:
        fail("retained evidence internal")
    if artifact is not None:
        if expected_out is None:
            fail("artifact publication state")
        else:
            errors.extend(_artifact_claim_errors(value, expected_out))
    if (value["status"], value["exit_code"], value["capability"]) not in _allowed_terminals(value["mode"]):
        fail("terminal mapping")
    if not errors:
        errors.extend(_derived_semantic_errors(value, totals, domains, issues))
    return sorted(set(errors))


def _prepared_artifact_consistency_errors(target: Path, value: dict[str, Any]) -> list[str]:
    artifact = value.get("artifact")
    if not isinstance(artifact, dict):
        return ["prepared artifact schema"]
    expected_path = target.relative_to(REPO_ROOT).as_posix()
    expected_digest = hashlib.sha256(_artifact_claim_bytes(value)).hexdigest()
    errors: list[str] = []
    if artifact.get("path") != expected_path:
        errors.append("prepared artifact path")
    if artifact.get("sha256") != expected_digest:
        errors.append("prepared artifact digest")
    return errors


def _read_bound_output_bytes(expected_out: Path) -> tuple[str, bytes]:
    target = _normalize_output_target(expected_out)
    fds: list[int] = []
    links: list[tuple[int, str, int]] = []
    file_fd = -1
    try:
        fds, links = _open_output_parent(REPO_ROOT, target)
        root_fd, parent_fd = fds[0], fds[-1]
        _validate_output_chain(REPO_ROOT, root_fd, links)
        entry = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(entry.st_mode):
            raise OSError("artifact target is not a regular file")
        target_identity = _directory_identity(entry)
        file_fd = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        _validate_output_chain(REPO_ROOT, root_fd, links)
        opened_entry = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(opened_entry.st_mode) or _directory_identity(opened_entry) != target_identity:
            raise OSError("artifact target identity changed during open")
        if _directory_identity(os.fstat(file_fd)) != target_identity:
            raise OSError("artifact file descriptor identity changed during open")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        _validate_output_chain(REPO_ROOT, root_fd, links)
        if _directory_identity(os.fstat(file_fd)) != target_identity:
            raise OSError("artifact file descriptor identity changed during read")
        reread_entry = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(reread_entry.st_mode) or _directory_identity(reread_entry) != target_identity:
            raise OSError("artifact target identity changed during read")
        return target.relative_to(REPO_ROOT).as_posix(), b"".join(chunks)
    finally:
        final_error: Exception | None = None
        if file_fd >= 0:
            try:
                _close_raw_fd(file_fd, committed=False)
            except Exception as exc:
                final_error = exc
        for open_fd in reversed(fds):
            try:
                _close_raw_fd(open_fd, committed=False)
            except Exception as exc:
                final_error = final_error or exc
        if final_error is not None:
            raise final_error


def _artifact_claim_errors(value: dict[str, Any], expected_out: Path) -> list[str]:
    artifact = value.get("artifact")
    if not _exact_keys(artifact, ARTIFACT_KEYS):
        return ["artifact fields/order"]
    expected_bytes = _artifact_claim_bytes(value)
    expected_digest = hashlib.sha256(expected_bytes).hexdigest()
    try:
        expected_path, actual_bytes = _read_bound_output_bytes(expected_out)
    except Exception:
        return ["artifact publication state"]
    errors: list[str] = []
    if artifact.get("path") != expected_path:
        errors.append("artifact publication path")
    if artifact.get("sha256") != expected_digest:
        errors.append("artifact publication digest")
    if actual_bytes != expected_bytes:
        errors.append("artifact publication bytes")
    return errors


def _derived_semantic_errors(
    value: dict[str, Any],
    totals: dict[str, int],
    domains: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    mode = value["mode"]
    reasons = {item["reason"] for item in issues}
    terminal = (value["status"], value["exit_code"], value["capability"])
    if "INVALID_ARGUMENT" in reasons:
        expected = {("INVALID_ARGUMENT", 2, "NO_CAPABILITY")}
    elif "INTERNAL_ERROR" in reasons:
        expected = {("INTERNAL_ERROR", 5, "NO_CAPABILITY")}
    elif totals["structure_issue_count"]:
        expected = {("STRUCTURE_INVALID", 1, "NO_CAPABILITY")}
    elif totals["complete_triplets"] == 0 or "NO_COMPLETE_TRIPLETS" in reasons:
        if mode == "refresh":
            expected = {("RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN")}
        elif mode == "strict":
            expected = {("NO_DATA", 4, "NO_CAPABILITY")}
        elif mode == "offline":
            expected = {
                ("NO_DATA", 0, "STRUCTURE_ONLY"),
                ("NO_DATA", 4, "NO_CAPABILITY"),
            }
        else:
            expected = {
                ("NO_DATA", 0, "DIAGNOSTIC_ONLY"),
                ("NO_DATA", 4, "NO_CAPABILITY"),
            }
    elif totals["freshness_issue_count"]:
        expected = {
            "diagnostic": {("STALE", 0, "DIAGNOSTIC_ONLY")},
            "strict": {("STALE", 3, "NO_CAPABILITY")},
            "refresh": {("RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN")},
        }.get(mode, {("STRUCTURE_ONLY", 0, "STRUCTURE_ONLY")})
    else:
        expected = {
            "offline": {("STRUCTURE_ONLY", 0, "STRUCTURE_ONLY")},
            "diagnostic": {("PASS", 0, "DIAGNOSTIC_ONLY")},
            "strict": {("PASS", 0, "FRESH_FIXTURE_GATE")},
            "refresh": {("PASS", 0, "REFRESH_NOT_REQUIRED")},
        }[mode]
    if terminal not in expected:
        errors.append("derived terminal")

    before_scan = terminal[0] == "INVALID_ARGUMENT" or (
        terminal[0] == "INTERNAL_ERROR" and not domains and not any(totals.values())
    )
    expected_freshness = mode != "offline" and not before_scan
    if value["freshness_checked"] != expected_freshness:
        errors.append("derived freshness_checked")
    for item in domains:
        if mode == "offline":
            expected_source = "not_checked"
        elif item["complete_triplets"] == 0:
            expected_source = "missing"
        elif item["freshness_issue_count"]:
            expected_source = "stale"
        else:
            expected_source = "fresh"
        if item["source_freshness"] != expected_source:
            errors.append("derived source_freshness")
        if mode == "offline" and item["selected_report"] is not None:
            errors.append("offline selected_report")
        if expected_source == "fresh" and item["selected_report"] is None:
            errors.append("fresh selected_report")

    if terminal == ("PASS", 0, "FRESH_FIXTURE_GATE"):
        strict_pass = (
            totals["domains_selected"] > 0
            and totals["complete_triplets"] > 0
            and totals["valid_triplets"] == totals["complete_triplets"]
            and not issues
            and all(
                item["snapshots_state"] == "DIRECTORY"
                and item["complete_triplets"] > 0
                and item["valid_triplets"] == item["complete_triplets"]
                and item["structure_issue_count"] == 0
                and item["freshness_issue_count"] == 0
                and item["source_freshness"] == "fresh"
                and item["selected_report"] is not None
                and item["selected_report"]["recent"] is True
                for item in domains
            )
        )
        if not strict_pass:
            errors.append("strict PASS invariants")
    return errors


def _reason_scope(reason: str) -> str:
    if reason in {"SITE_ROOT_MISSING", "NO_DOMAINS", "INVALID_ARGUMENT", "INTERNAL_ERROR"}:
        return "ROOT"
    if reason in {
        "DOMAIN_MISSING",
        "DOMAIN_NOT_DIRECTORY",
        "UNSAFE_DOMAIN",
        "SNAPSHOTS_MISSING",
        "SNAPSHOTS_NOT_DIRECTORY",
        "NO_COMPLETE_TRIPLETS",
    }:
        return "DOMAIN"
    if reason in FRESHNESS_REASONS and reason.startswith("REPORT_"):
        return "REPORT"
    return "FIXTURE"


def _validate_selected_root_binding(
    item: dict[str, Any],
    domains: list[dict[str, Any]],
    expected_site_root: Path | None,
    fail: Any,
    label: str,
) -> None:
    if item.get("selected_root") is None:
        return
    matches = [domain for domain in domains if domain.get("domain") == item.get("domain")]
    if len(matches) == 1:
        if item["selected_root"] != matches[0].get("selected_root"):
            fail(f"{label} selected_root binding")
        return
    if (
        item.get("scope") == "DOMAIN"
        and item.get("reason") in {"DOMAIN_MISSING", "DOMAIN_NOT_DIRECTORY"}
        and expected_site_root is not None
    ):
        expected = _empty_domain_result(
            Path(os.path.abspath(expected_site_root)) / item["domain"],
            Path(os.path.abspath(expected_site_root)),
            Mode.OFFLINE,
            select_layout=False,
        )["selected_root"]
        if item["selected_root"] != expected:
            fail(f"{label} selected_root binding")
        return
    fail(f"{label} domain binding")


def _validate_nullable(item: dict[str, Any], fail: Any, label: str) -> None:
    scope = item.get("scope")
    domain = item.get("domain")
    prefix = item.get("prefix")
    selected = item.get("selected_root")
    if scope == "ROOT":
        valid = domain is None and prefix is None and selected is None
    elif item.get("reason") == "UNSAFE_DOMAIN":
        valid = (
            isinstance(domain, str)
            and re.fullmatch(r"domain-sha256-[0-9a-f]{16}", domain) is not None
            and prefix is None
            and selected is None
        )
    elif scope in {"DOMAIN", "REPORT"}:
        valid = isinstance(domain, str) and bool(domain) and prefix is None and isinstance(selected, str) and bool(selected)
    else:
        valid = all(isinstance(value, str) and bool(value) for value in (domain, prefix, selected))
    if not valid:
        fail(f"{label} nullable")


def _validate_safe_identifiers(item: dict[str, Any], fail: Any, label: str) -> None:
    domain = item.get("domain")
    prefix = item.get("prefix")
    selected = item.get("selected_root")
    if domain is not None and (not isinstance(domain, str) or not _is_safe_domain(domain)):
        fail(f"{label} domain output")
    if prefix is not None and (
        not isinstance(prefix, str) or prefix != _sanitize_identifier(prefix, "prefix")
    ):
        fail(f"{label} prefix output")
    if selected is not None and not _safe_repo_relative_posix_path(selected):
        fail(f"{label} selected_root output")


def _allowed_terminals(mode: str) -> set[tuple[str, int, str]]:
    common = {
        ("INVALID_ARGUMENT", 2, "NO_CAPABILITY"),
        ("INTERNAL_ERROR", 5, "NO_CAPABILITY"),
        ("STRUCTURE_INVALID", 1, "NO_CAPABILITY"),
    }
    if mode == "offline":
        return common | {
            ("NO_DATA", 0, "STRUCTURE_ONLY"),
            ("NO_DATA", 4, "NO_CAPABILITY"),
            ("STRUCTURE_ONLY", 0, "STRUCTURE_ONLY"),
        }
    if mode == "diagnostic":
        return common | {
            ("NO_DATA", 0, "DIAGNOSTIC_ONLY"),
            ("NO_DATA", 4, "NO_CAPABILITY"),
            ("STALE", 0, "DIAGNOSTIC_ONLY"),
            ("PASS", 0, "DIAGNOSTIC_ONLY"),
        }
    if mode == "strict":
        return common | {
            ("NO_DATA", 4, "NO_CAPABILITY"),
            ("STALE", 3, "NO_CAPABILITY"),
            ("PASS", 0, "FRESH_FIXTURE_GATE"),
        }
    return common | {
        ("RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN"),
        ("PASS", 0, "REFRESH_NOT_REQUIRED"),
    }


class CliArgumentError(Exception):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        raise CliArgumentError((message or "help requested").strip())

    def print_help(self, file: Any = None) -> None:
        super().print_help(file=sys.stderr if file is None else file)


def _mode_hint(argv: Sequence[str]) -> Mode:
    hint = Mode.DIAGNOSTIC
    for index, value in enumerate(argv):
        if value.startswith("--mode="):
            try:
                hint = Mode(value.split("=", 1)[1])
            except ValueError:
                return Mode.DIAGNOSTIC
        elif value == "--mode":
            if index + 1 >= len(argv):
                return Mode.DIAGNOSTIC
            try:
                hint = Mode(argv[index + 1])
            except ValueError:
                return Mode.DIAGNOSTIC
    return hint


def cli_main(tool: str, argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = JsonArgumentParser(description=f"Canonical {tool} fixture gate", allow_abbrev=False)
    positional = "site_root" if tool == "validate_fixtures" else "site_memory_root"
    parser.add_argument(positional, nargs="?", default=str(DEFAULT_SITE_ROOT))
    parser.add_argument("--mode", choices=[mode.value for mode in Mode], default=None)
    parser.add_argument("--require-data", action="store_true")
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--out")
    if tool == "validate_fixtures":
        parser.add_argument("--strict-review", action="store_true")
    else:
        parser.add_argument("--recent-days", type=int, default=30)
        parser.add_argument("--strict-fresh", action="store_true")
    try:
        for index, value in enumerate(argv):
            if value == "--out=" or (
                value == "--out" and index + 1 < len(argv) and argv[index + 1] == ""
            ):
                raise CliArgumentError("--out requires a non-empty value")
        args = parser.parse_args(argv)
        explicit_mode = Mode(args.mode) if args.mode else None
        alias = bool(getattr(args, "strict_review", False) or getattr(args, "strict_fresh", False))
        if alias and explicit_mode not in {None, Mode.STRICT}:
            raise CliArgumentError("strict compatibility alias conflicts with --mode")
        mode = Mode.STRICT if alias else explicit_mode or Mode.DIAGNOSTIC
        recent_days = getattr(args, "recent_days", 30)
        if recent_days <= 0:
            raise CliArgumentError("--recent-days must be positive")
        if args.out is not None and not args.out:
            raise CliArgumentError("--out requires a non-empty value")
        if args.out is not None and mode is not Mode.REFRESH:
            raise CliArgumentError("--out is valid only with --mode refresh")
        result = run_gate(
            site_root=Path(getattr(args, positional)),
            tool=tool,
            mode=mode,
            require_data=args.require_data or alias,
            recent_days=recent_days,
            domains=args.domain,
            out=Path(args.out) if args.out is not None else None,
        )
    except CliArgumentError:
        mode = _mode_hint(argv)
        result = invalid_argument_result(tool, mode)
        print("INVALID_ARGUMENT: argument parsing failed", file=sys.stderr)
    except PublicationStop:
        raise
    except Exception:
        mode = _mode_hint(argv)
        result = _internal_result(tool, mode)
        print("INTERNAL_ERROR", file=sys.stderr)
    print(result.serialize())
    return result.exit_code
