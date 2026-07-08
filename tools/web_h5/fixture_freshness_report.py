#!/usr/bin/env python3
"""Report fixture freshness and review status for site memory.

Default mode is report-only so historical repositories can surface stale
fixtures without hiding the result. Use --strict-fresh for release gates.

Fixture classes:
  active: fixtures/active/snapshots, must be fresh and reviewed for gates.
  historical: fixtures/historical/snapshots, may be stale and is reported only.
  archive: 站点经验库/_archive/**, may be stale and is excluded from gates.
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


def _snapshot_report(snapshots: Path, reports: Path, now: datetime, recent_days: int) -> dict:
    entry = {
        "snapshot_triplets": 0,
        "expired_count": 0,
        "review_pending_count": 0,
        "missing_expiry_count": 0,
        "recent_report": False,
        "latest_report": None,
        "source_freshness": "missing",
    }
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
            if has_review_placeholder(text) or "review_status: pending" in text.lower():
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


def domain_report(domain_dir: Path, now: datetime, recent_days: int) -> dict:
    fixtures = domain_dir / "fixtures"
    active_root = fixtures / "active" if (fixtures / "active").is_dir() else fixtures
    historical_root = fixtures / "historical"
    active = _snapshot_report(active_root / "snapshots", active_root / "reports", now, recent_days)
    historical = _snapshot_report(historical_root / "snapshots", historical_root / "reports", now, recent_days)
    entry = {
        "domain": domain_dir.name,
        "fixtures_present": fixtures.is_dir(),
        "active": active,
        "historical": historical,
        "snapshot_triplets": active["snapshot_triplets"],
        "expired_count": active["expired_count"],
        "review_pending_count": active["review_pending_count"],
        "missing_expiry_count": active["missing_expiry_count"],
        "recent_report": active["recent_report"],
        "latest_report": active["latest_report"],
        "source_freshness": active["source_freshness"],
    }
    if not fixtures.is_dir():
        return entry
    return entry


def archive_report(root: Path) -> dict:
    archive_root = root / "_archive"
    snapshot_triplets = 0
    manifests = 0
    if archive_root.is_dir():
        manifests = len(list(archive_root.rglob("manifest*.json")))
        for req in archive_root.rglob("*.req.json"):
            prefix = req.stem[:-4]
            if (req.parent / f"{prefix}.resp.json").is_file() and (req.parent / f"{prefix}.meta.yaml").is_file():
                snapshot_triplets += 1
    return {
        "root": str(archive_root),
        "snapshot_triplets": snapshot_triplets,
        "manifest_count": manifests,
        "participates_in_gate": False,
    }


def build_report(root: Path, recent_days: int) -> dict:
    now = datetime.now(timezone.utc)
    domains = []
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and not child.name.startswith("_"):
                item = domain_report(child, now, recent_days)
                if item["fixtures_present"]:
                    domains.append(item)
    active_domains = [d for d in domains if d["active"]["snapshot_triplets"] > 0]
    historical_domains = [d for d in domains if d["historical"]["snapshot_triplets"] > 0]
    archive = archive_report(root)
    totals = {
        "domains": len(domains),
        "active_domains": len(active_domains),
        "active_snapshot_triplets": sum(d["active"]["snapshot_triplets"] for d in domains),
        "active_expired_count": sum(d["active"]["expired_count"] for d in domains),
        "active_review_pending_count": sum(d["active"]["review_pending_count"] for d in domains),
        "active_missing_expiry_count": sum(d["active"]["missing_expiry_count"] for d in domains),
        "active_fresh_domains": sum(1 for d in active_domains if d["active"]["source_freshness"] == "fresh"),
        "active_stale_domains": sum(1 for d in active_domains if d["active"]["source_freshness"] == "stale"),
        "historical_domains": len(historical_domains),
        "historical_snapshot_triplets": sum(d["historical"]["snapshot_triplets"] for d in domains),
        "archive_snapshot_triplets": archive["snapshot_triplets"],
        "archive_manifest_count": archive["manifest_count"],
    }
    status = "PASS" if totals["active_snapshot_triplets"] and totals["active_stale_domains"] == 0 else "STALE"
    return {
        "tool": "fixture_freshness_report",
        "checked_at": now.isoformat(),
        "recent_days": recent_days,
        "status": status,
        "totals": totals,
        "archive": archive,
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
