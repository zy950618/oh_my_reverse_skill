#!/usr/bin/env python3
"""Aggregate replay diffs into one fail-closed consistency result."""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from field_rules import load_meta
from fixture_layout import select_fixture_layout
from snapshot_diff import diff_snapshot


@dataclass(frozen=True)
class ConsistencyResult:
    status: str
    exit_code: int
    total: int
    selected: int
    replayed: int
    compared: int
    fatal_error_count: int
    status_mismatch_count: int
    no_data: bool
    consistency_rate: float
    threshold: float | None
    failure_kind: str | None
    report_artifact: str | None
    trend_artifact: str | None
    comparable_fields: int = 0
    matched_fields: int = 0
    structure_ok: int = 0
    empty_snapshot_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrendInvalidError(ValueError):
    pass


class InvalidArgumentsError(ValueError):
    pass


class CanonicalArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InvalidArgumentsError(message)


def serialize_json(value: object, *, indent: int | None = None) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
        separators=None if indent is not None else (",", ":"),
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _strict_json_loads(document: str) -> Any:
    return json.loads(document, parse_constant=_reject_json_constant)


def _result(
    status: str,
    exit_code: int,
    failure_kind: str | None,
    *,
    threshold: float | None,
    no_data: bool = False,
    total: int = 0,
    selected: int = 0,
    replayed: int = 0,
    compared: int = 0,
    fatal_error_count: int = 0,
    status_mismatch_count: int = 0,
    consistency_rate: float = 0.0,
    comparable_fields: int = 0,
    matched_fields: int = 0,
    structure_ok: int = 0,
    empty_snapshot_count: int = 0,
) -> ConsistencyResult:
    return ConsistencyResult(
        status=status,
        exit_code=exit_code,
        total=total,
        selected=selected,
        replayed=replayed,
        compared=compared,
        fatal_error_count=fatal_error_count,
        status_mismatch_count=status_mismatch_count,
        no_data=no_data,
        consistency_rate=consistency_rate,
        threshold=threshold,
        failure_kind=failure_kind,
        report_artifact=None,
        trend_artifact=None,
        comparable_fields=comparable_fields,
        matched_fields=matched_fields,
        structure_ok=structure_ok,
        empty_snapshot_count=empty_snapshot_count,
    )


def _emit(result: ConsistencyResult) -> int:
    print(serialize_json(result.to_dict()))
    return result.exit_code


def _read_object(path: Path, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = _strict_json_loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"{label}: {type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return None, f"{label}: root is not an object"
    return value, None


def _read_trend(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entries": []}
    try:
        value = _strict_json_loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise TrendInvalidError(f"trend unreadable or malformed: {exc}") from exc
    if not isinstance(value, dict):
        raise TrendInvalidError("trend root is not an object")
    if "entries" not in value or not isinstance(value["entries"], list):
        raise TrendInvalidError("trend entries is missing or not a list")
    return value


def _canonical_result(
    *,
    threshold: float,
    total: int,
    replayed: int,
    compared: int,
    fatal_error_count: int,
    status_mismatch_count: int,
    comparable_fields: int,
    matched_fields: int,
    structure_ok: int,
    empty_snapshot_count: int,
) -> ConsistencyResult:
    rate = round(matched_fields / comparable_fields, 4) if comparable_fields else 0.0
    common = dict(
        threshold=threshold,
        total=total,
        selected=total,
        replayed=replayed,
        compared=compared,
        fatal_error_count=fatal_error_count,
        status_mismatch_count=status_mismatch_count,
        consistency_rate=rate,
        comparable_fields=comparable_fields,
        matched_fields=matched_fields,
        structure_ok=structure_ok,
        empty_snapshot_count=empty_snapshot_count,
    )
    if fatal_error_count or replayed != total:
        return _result("FAIL", 3, "FATAL_ENDPOINT", **common)
    if total == 0 or comparable_fields == 0:
        return _result("NO_DATA", 4, "NO_DATA", no_data=True, **common)
    if rate >= threshold:
        return _result("PASS", 0, None, **common)
    if rate >= 0.80:
        return _result("WARN", 3, "THRESHOLD", **common)
    return _result("FAIL", 3, "THRESHOLD", **common)


def render_report(domain: str, results: list[dict[str, Any]], overall: dict[str, Any]) -> str:
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# 一致性重放报告 — {domain}",
        "",
        f"- 生成时间: {date}",
        f"- selected: {overall['selected']}",
        f"- replayed: {overall['replayed']}",
        f"- compared: {overall['compared']}",
        f"- fatal errors: {overall['fatal_error_count']}",
        f"- HTTP status mismatches: {overall['status_mismatch_count']}",
        f"- consistency rate: {overall['consistency_rate']:.2%}",
        f"- status: {overall['status']} (exit {overall['exit_code']})",
        "",
        "## Canonical Result",
        "",
        "```json",
        serialize_json(overall),
        "```",
        "",
        "## Endpoint Records",
        "",
        "| Endpoint | Result | Fields | Matched | Rate |",
        "|---|---|---:|---:|---:|",
    ]
    for item in results:
        if "errors" in item:
            detail = "; ".join(item["errors"]).replace("|", "\\|")
            lines.append(f"| `{item['endpoint']}` | ERROR: {detail} | 0 | 0 | 0.0% |")
            continue
        status = "STATUS_MISMATCH" if not item.get("status_match", False) else "COMPARED"
        lines.append(
            f"| `{item['endpoint']}` | {status} | {item['total_fields']} | "
            f"{item['matched']} | {item['consistency_rate']:.1%} |"
        )
    return "\n".join(lines) + "\n"


def _trend_document(history: dict[str, Any], result: ConsistencyResult) -> dict[str, Any]:
    updated = dict(history)
    entries = list(history["entries"])
    entry = result.to_dict()
    entry["date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    entries.append(entry)
    updated["entries"] = entries[-200:]
    return updated


def _stage_text(target: Path, content: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    staged = Path(raw_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if staged.read_text(encoding="utf-8") != content:
            raise OSError(f"staged content verification failed for {target}")
        return staged
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        staged.unlink(missing_ok=True)
        raise


def _restore_target(target: Path, previous: bytes | None) -> None:
    if previous is None:
        target.unlink(missing_ok=True)
        return
    fd, raw_path = tempfile.mkstemp(prefix=f".{target.name}.rollback.", suffix=".tmp", dir=target.parent)
    staged = Path(raw_path)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(previous)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)


def _publish_artifacts(
    report_file: Path,
    report_text: str,
    trend_file: Path,
    trend_text: str,
) -> None:
    staged: list[Path] = []
    previous_report = report_file.read_bytes() if report_file.exists() else None
    published_report = False
    try:
        staged_report = _stage_text(report_file, report_text)
        staged.append(staged_report)
        staged_trend = _stage_text(trend_file, trend_text)
        staged.append(staged_trend)
        os.replace(staged_report, report_file)
        published_report = True
        staged.remove(staged_report)
        os.replace(staged_trend, trend_file)
        staged.remove(staged_trend)
    except Exception:
        if published_report:
            try:
                _restore_target(report_file, previous_report)
            except Exception as rollback_exc:
                print(f"artifact rollback failed: {rollback_exc}", file=sys.stderr)
        raise
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


def _collect_endpoint(req_file: Path, snap_dir: Path, actual_dir: Path) -> tuple[dict[str, Any], bool]:
    prefix = req_file.stem[:-4]
    resp_file = snap_dir / f"{prefix}.resp.json"
    actual_file = actual_dir / f"{prefix}.actual.json"
    meta_file = snap_dir / f"{prefix}.meta.yaml"
    errors: list[str] = []

    _, request_error = _read_object(req_file, "request")
    if request_error:
        errors.append(request_error)
    response, response_error = _read_object(resp_file, "response")
    if response_error:
        errors.append(response_error)
    actual, actual_error = _read_object(actual_file, "actual")
    replayed = actual is not None
    if actual_error:
        errors.append(actual_error)

    meta: dict[str, Any] = {}
    if meta_file.exists():
        if not callable(load_meta):
            errors.append("metadata: parser unavailable")
        else:
            try:
                loaded_meta = load_meta(meta_file)
                if not isinstance(loaded_meta, Mapping):
                    errors.append("metadata: root is not a mapping")
                else:
                    meta = dict(loaded_meta)
            except Exception as exc:
                errors.append(f"metadata: {type(exc).__name__}: {exc}")

    if errors:
        return {"endpoint": prefix, "errors": errors}, replayed
    try:
        diff = diff_snapshot(response, actual, meta)  # type: ignore[arg-type]
        if not isinstance(diff, dict):
            raise TypeError("diff result root is not an object")
    except Exception as exc:
        return {
            "endpoint": prefix,
            "errors": [f"diff: {type(exc).__name__}: {exc}"],
        }, replayed
    diff["endpoint"] = prefix
    return diff, replayed


def _argument_vector(argv: list[str]) -> list[str]:
    """Keep negative non-finite threshold tokens attached for argparse."""
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--threshold" and index + 1 < len(argv):
            normalized.append(f"--threshold={argv[index + 1]}")
            index += 2
        else:
            normalized.append(argv[index])
            index += 1
    return normalized


def main() -> int:
    parser = CanonicalArgumentParser(description="聚合 diff 出 markdown 报告 + trend.json")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--threshold", type=float, default=0.90)
    try:
        args = parser.parse_args(_argument_vector(sys.argv[1:]))
    except InvalidArgumentsError as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return _emit(_result("REFUSED", 2, "INVALID_ARGUMENT", threshold=None))

    threshold = args.threshold
    if not math.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        result = _result(
            "REFUSED",
            2,
            "INVALID_ARGUMENT",
            threshold=threshold if math.isfinite(threshold) else None,
        )
        print(f"invalid threshold argument: {threshold!r}", file=sys.stderr)
        return _emit(result)

    fixtures_dir = SITE_ROOT / args.domain / "fixtures"
    selected_root, snap_dir = select_fixture_layout(fixtures_dir)
    if not selected_root.is_dir():
        return _emit(_result("NO_DATA", 4, "NO_DATA", threshold=threshold, no_data=True))
    if not snap_dir.is_dir():
        print(f"selected snapshots directory is missing or invalid: {snap_dir}", file=sys.stderr)
        return _emit(_result("ERROR", 1, "LAYOUT_INVALID", threshold=threshold))

    req_files = sorted(snap_dir.glob("*.req.json"))
    reports_dir = selected_root / "reports"
    report_file = reports_dir / (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d") + "-replay.md"
    )
    trend_file = reports_dir / "trend.json"
    try:
        trend = _read_trend(trend_file)
    except TrendInvalidError as exc:
        print(str(exc), file=sys.stderr)
        return _emit(
            _result(
                "ERROR",
                5,
                "TREND_INVALID",
                threshold=threshold,
                total=len(req_files),
                selected=len(req_files),
            )
        )

    results: list[dict[str, Any]] = []
    replayed = compared = fatal = status_mismatches = 0
    matched_fields = comparable_fields = structure_ok = empty_count = 0
    actual_dir = selected_root / "actual"
    for req_file in req_files:
        endpoint, was_replayed = _collect_endpoint(req_file, snap_dir, actual_dir)
        results.append(endpoint)
        replayed += int(was_replayed)
        if "errors" in endpoint:
            fatal += 1
            print(f"{endpoint['endpoint']}: {'; '.join(endpoint['errors'])}", file=sys.stderr)
            continue
        compared += 1
        fields = int(endpoint.get("total_fields", 0))
        comparable_fields += fields
        matched_fields += int(endpoint.get("matched", 0))
        if endpoint.get("empty_snapshot"):
            empty_count += 1
        if endpoint.get("structure_ok"):
            structure_ok += 1
        if not endpoint.get("status_match", False):
            status_mismatches += 1
            fatal += 1

    result = _canonical_result(
        threshold=threshold,
        total=len(req_files),
        replayed=replayed,
        compared=compared,
        fatal_error_count=fatal,
        status_mismatch_count=status_mismatches,
        comparable_fields=comparable_fields,
        matched_fields=matched_fields,
        structure_ok=structure_ok,
        empty_snapshot_count=empty_count,
    )
    report_rel = report_file.relative_to(selected_root).as_posix()
    trend_rel = trend_file.relative_to(selected_root).as_posix()
    published_result = replace(
        result,
        report_artifact=report_rel,
        trend_artifact=trend_rel,
    )
    try:
        report_text = render_report(args.domain, results, published_result.to_dict())
        trend_text = serialize_json(_trend_document(trend, published_result), indent=2) + "\n"
        _publish_artifacts(report_file, report_text, trend_file, trend_text)
    except Exception as exc:
        print(f"artifact write failed: {exc}", file=sys.stderr)
        return _emit(replace(result, status="ERROR", exit_code=5, no_data=False,
                             failure_kind="ARTIFACT_WRITE"))
    return _emit(published_result)


if __name__ == "__main__":
    sys.exit(main())
