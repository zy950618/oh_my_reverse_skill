from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "99-SKILLS治理" / "28-final-cleanup-ledger.md"
CLASSIFICATION = ROOT / "99-SKILLS治理" / "32-cleanup-candidate-classification.md"
ARCHIVE_ROOT = ROOT / "public-range-evidence" / "_archive" / "manual-review"
PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    "playwright-report",
    "coverage",
    "dist",
    "build",
    "tmp",
    "temp",
    ".tmp",
    "cache",
    ".cache",
}
SUFFIXES = {".tmp", ".bak", ".old", ".orig", ".log"}


def is_candidate(path: Path) -> bool:
    if ".git" in path.parts:
        return False
    if "_archive" in {part.lower() for part in path.parts}:
        return False
    if path.name in PATTERNS:
        return True
    return path.is_file() and path.suffix.lower() in SUFFIXES


def scan() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if is_candidate(p)), key=lambda p: p.as_posix())


def classify(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if path.name in {"__pycache__", ".pytest_cache"} or path.suffix.lower() == ".pyc":
        return "DELETE"
    if path.name in {"cache", ".cache"}:
        return "ARCHIVE"
    if path.suffix.lower() == ".log":
        if rel.startswith("public-range-evidence/") or rel.startswith("public-range-labs/"):
            return "ARCHIVE"
        return "UNKNOWN_REVIEW_REQUIRED"
    if path.suffix.lower() in {".tmp", ".bak", ".old", ".orig"}:
        return "ARCHIVE"
    if path.name in {"tmp", "temp", ".tmp", "coverage", "playwright-report", "dist", "build"}:
        return "ARCHIVE"
    return "UNKNOWN_REVIEW_REQUIRED"


def classify_all(candidates: list[Path]) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "classification": classify(path),
            "action": "delete" if classify(path) == "DELETE" else "archive",
        }
        for path in candidates
    ]


def ensure_within_root(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise RuntimeError(f"refusing path outside repo root: {path}")
    return resolved


def archive_path(path: Path, run_dir: Path) -> Path:
    rel = path.relative_to(ROOT)
    return run_dir / rel


def apply_actions(candidates: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
    deleted: list[Path] = []
    archived: list[Path] = []
    manual_review: list[Path] = []
    run_dir = ARCHIVE_ROOT / datetime.now(timezone.utc).strftime("cleanup-%Y%m%dT%H%M%SZ")
    manifest: list[dict[str, str]] = []
    for path in candidates:
        ensure_within_root(path)
        action = classify(path)
        if action == "DELETE":
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            deleted.append(path)
            manifest.append({"source": path.relative_to(ROOT).as_posix(), "classification": action, "action": "deleted"})
            continue
        destination = archive_path(path, run_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.move(str(path), str(destination))
        archived.append(destination)
        if action == "UNKNOWN_REVIEW_REQUIRED":
            manual_review.append(destination)
        manifest.append({
            "source": path.relative_to(ROOT).as_posix(),
            "archive": destination.relative_to(ROOT).as_posix(),
            "classification": action,
            "action": "archived",
        })
    if manifest:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return deleted, archived, manual_review


def write_classification(classified: list[dict[str, str]]) -> None:
    CLASSIFICATION.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(f"| `{item['path']}` | {item['classification']} | {item['action']} |" for item in classified)
    CLASSIFICATION.write_text(
        "# Cleanup Candidate Classification\n\n"
        "| path | classification | planned_action |\n"
        "|---|---|---|\n"
        f"{rows}\n",
        encoding="utf-8",
    )


def write_ledger(candidates: list[Path], mode: str, deleted: list[Path], archived: list[Path], manual_review: list[Path]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rel_candidates = [p.relative_to(ROOT).as_posix() for p in candidates]
    rel_deleted = [p.relative_to(ROOT).as_posix() for p in deleted]
    rel_archived = [p.relative_to(ROOT).as_posix() for p in archived]
    rel_manual = [p.relative_to(ROOT).as_posix() for p in manual_review]
    content = f"""# Final Cleanup Ledger

## Cleanup Run

timestamp: {datetime.now(timezone.utc).isoformat()}
mode: {mode}

## Removed

{json.dumps(rel_deleted, ensure_ascii=False, indent=2)}

## Archived

{json.dumps(rel_archived, ensure_ascii=False, indent=2)}

## Kept As Evidence

- Existing modified and untracked files outside cleanup candidate patterns were preserved.
- Evidence-like logs and unknown candidates were archived under `public-range-evidence/_archive/manual-review/`.

## Cleanup Candidates

{json.dumps(rel_candidates, ensure_ascii=False, indent=2)}

## Manual Review

{json.dumps(rel_manual, ensure_ascii=False, indent=2)}

## Migrated To Memory

- not applicable

## Still Unverified

- archived manual-review evidence requires later human review before permanent deletion.

## Remaining Reason

Cleanup candidates are handled by deletion or archive. Archive is used instead of silent deletion when evidence value is possible.
"""
    LEDGER.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservative workspace cleanup checker.")
    parser.add_argument("--plan", action="store_true", help="write classification plan")
    parser.add_argument("--check", action="store_true", help="scan only")
    parser.add_argument("--apply", action="store_true", help="write cleanup ledger")
    args = parser.parse_args()

    if not args.check and not args.apply and not args.plan:
        parser.error("choose --plan, --check, or --apply")

    candidates = scan()
    classified = classify_all(candidates)
    deleted: list[Path] = []
    archived: list[Path] = []
    manual_review: list[Path] = []

    if args.plan:
        write_classification(classified)

    if args.apply:
        write_classification(classified)
        deleted, archived, manual_review = apply_actions(candidates)
        write_ledger(candidates, "apply-classified", deleted, archived, manual_review)

    remaining = scan()
    unclassified = [item for item in classified if item["classification"] not in {
        "DELETE", "ARCHIVE", "KEEP_REFERENCED", "KEEP_USER_EVIDENCE", "KEEP_RELEASE_ARTIFACT", "UNKNOWN_REVIEW_REQUIRED",
    }]

    print(json.dumps({
        "status": "pass" if not unclassified and (not args.check or not remaining) else "fail",
        "candidate_count": len(candidates),
        "remaining_candidate_count": len(remaining),
        "unclassified_count": len(unclassified),
        "deleted_count": len(deleted),
        "archived_count": len(archived),
        "manual_review_count": len(manual_review),
        "ledger": LEDGER.relative_to(ROOT).as_posix(),
        "classification": CLASSIFICATION.relative_to(ROOT).as_posix(),
        "manual_review_archive": ARCHIVE_ROOT.relative_to(ROOT).as_posix(),
    }, ensure_ascii=False, indent=2))
    return 0 if not unclassified and (not args.check or not remaining) else 1


if __name__ == "__main__":
    raise SystemExit(main())
