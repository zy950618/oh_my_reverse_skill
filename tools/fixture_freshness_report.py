#!/usr/bin/env python3
"""Report fixture freshness and review status for site memory.

Default mode is report-only so historical repositories can surface stale
fixtures without hiding the result. Use --strict-fresh for release gates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


TODO_MARKERS = (
    "TODO",
    "auto-extracted",
    "Review and edit before committing",
)


def parse_expiry(text: str) -> datetime | None:
    match = re.search(r'expires_at["\']?\s*:\s*["\']?([0-9T:\-Z+.]+)', text)
    if not match:
        return None
    raw = match.group(1).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def has_review_placeholder(text: str) -> bool:
    lower = text.lower()
    return any(marker.lower() in lower for marker in TODO_MARKERS)


def domain_report(domain_dir: Path, now: datetime, recent_days: int) -> dict:
    fixtures = domain_dir / "fixtures"
    snapshots = fixtures / "snapshots"
    reports = fixtures / "reports"
    entry = {
        "domain": domain_dir.name,
        "fixtures_present": fixtures.is_dir(),
        "snapshot_triplets": 0,
        "expired_count": 0,
        "review_pending_count": 0,
        "missing_expiry_count": 0,
        "recent_report": False,
        "latest_report": None,
        "source_freshness": "missing",
    }
    if not fixtures.is_dir():
        return entry

    if snapshots.is_dir():
        for req in snapshots.glob("*.req.json"):
            prefix = req.stem[:-4]
            if (snapshots / f"{prefix}.resp.json").is_file() and (snapshots / f"{prefix}.meta.yaml").is_file():
                entry["snapshot_triplets"] += 1

        for meta in snapshots.glob("*.meta.yaml"):
            text = meta.read_text(encoding="utf-8-sig", errors="replace")
            expires = parse_expiry(text)
            if expires is None:
                entry["missing_expiry_count"] += 1
            elif expires <= now:
                entry["expired_count"] += 1
            if has_review_placeholder(text):
                entry["review_pending_count"] += 1

    if reports.is_dir():
        recent_cutoff = now - timedelta(days=recent_days)
        latest_mtime: datetime | None = None
        latest_name: str | None = None
        for report in reports.glob("*-replay.md"):
            mtime = datetime.fromtimestamp(report.stat().st_mtime, tz=timezone.utc)
            if latest_mtime is None or mtime > latest_mtime:
                latest_mtime = mtime
                latest_name = report.name
            if mtime >= recent_cutoff:
                entry["recent_report"] = True
        entry["latest_report"] = latest_name

    if entry["snapshot_triplets"] == 0:
        entry["source_freshness"] = "missing"
    elif entry["expired_count"] or entry["review_pending_count"] or entry["missing_expiry_count"] or not entry["recent_report"]:
        entry["source_freshness"] = "stale"
    else:
        entry["source_freshness"] = "fresh"
    return entry


def build_report(root: Path, recent_days: int) -> dict:
    now = datetime.now(timezone.utc)
    domains = []
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("_"):
                domains.append(domain_report(child, now, recent_days))
    totals = {
        "domains": len(domains),
        "snapshot_triplets": sum(d["snapshot_triplets"] for d in domains),
        "expired_count": sum(d["expired_count"] for d in domains),
        "review_pending_count": sum(d["review_pending_count"] for d in domains),
        "missing_expiry_count": sum(d["missing_expiry_count"] for d in domains),
        "fresh_domains": sum(1 for d in domains if d["source_freshness"] == "fresh"),
        "stale_domains": sum(1 for d in domains if d["source_freshness"] == "stale"),
        "missing_domains": sum(1 for d in domains if d["source_freshness"] == "missing"),
    }
    status = "PASS" if totals["domains"] and totals["stale_domains"] == 0 and totals["missing_domains"] == 0 else "STALE"
    return {
        "tool": "fixture_freshness_report",
        "checked_at": now.isoformat(),
        "recent_days": recent_days,
        "status": status,
        "totals": totals,
        "domains": domains,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report site fixture freshness")
    parser.add_argument("site_memory_root", nargs="?", default="站点经验库")
    parser.add_argument("--recent-days", type=int, default=30)
    parser.add_argument("--strict-fresh", action="store_true", help="exit 1 when any domain is stale or missing")
    args = parser.parse_args()

    report = build_report(Path(args.site_memory_root), args.recent_days)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict_fresh and report["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
