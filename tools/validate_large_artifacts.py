from __future__ import annotations

import json
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = next(ROOT.glob("99-SKILLS*/"), ROOT / "99-SKILLS治理") / "49-large-artifact-scan.md"

MODEL_SUFFIXES = {".pt", ".pth", ".onnx", ".safetensors", ".pkl", ".joblib"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".gz", ".tgz", ".7z"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".ppm", ".webp", ".bmp", ".svg"}
REGISTERING_NAMES = {
    "package_manifest.json",
    "model_package_manifest.json",
    "model_registry.json",
    "dataset_manifest.json",
    "action_manifest.json",
}
ALLOWED_SMALL_SAMPLE_PARTS = {"sample_images", "samples", "fixtures", "sample_labels", "reports", "manifests"}
CHECKPOINT_PARTS = {"checkpoints", "checkpoint", "models"}


def git_paths(staged: bool = False) -> list[Path]:
    if staged:
        raw = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"], cwd=ROOT)
        paths: list[Path] = []
        for item in raw.split(b"\0"):
            if not item:
                continue
            path = ROOT / item.decode("utf-8", errors="replace")
            if path.exists() and path.is_file():
                paths.append(path)
        return sorted(set(paths), key=lambda item: item.as_posix())

    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "-uall"], cwd=ROOT)
    paths: list[Path] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        text = item.decode("utf-8", errors="replace")
        if len(text) < 4:
            continue
        path = ROOT / text[3:]
        if path.exists() and path.is_file():
            paths.append(path)
    return sorted(set(paths), key=lambda item: item.as_posix())


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_manifest_corpus(paths: list[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.name.lower() in REGISTERING_NAMES or path.suffix.lower() in {".md", ".yaml", ".yml"}:
            try:
                chunks.append(path.read_text(encoding="utf-8-sig", errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


def is_manifest_registered(path: Path, corpus: str) -> bool:
    relative = rel(path)
    return relative in corpus or relative.replace("/", "\\") in corpus or path.name in corpus


def classify(path: Path, corpus: str) -> dict[str, object] | None:
    size = path.stat().st_size
    suffix = path.suffix.lower()
    parts = {part.lower() for part in path.relative_to(ROOT).parts}
    relative = rel(path)

    large_tier = None
    if size > 5 * 1024 * 1024:
        large_tier = "gt_5mb"
    elif size > 1024 * 1024:
        large_tier = "gt_1mb"

    kind = None
    if suffix in MODEL_SUFFIXES:
        kind = "model_artifact"
    elif suffix in ARCHIVE_SUFFIXES:
        kind = "archive_artifact"
    elif suffix in IMAGE_SUFFIXES and size > 1024 * 1024:
        kind = "dataset_image"
    elif large_tier:
        kind = "large_file"
    elif parts & CHECKPOINT_PARTS and suffix == ".json":
        kind = "training_checkpoint_metadata"

    if not kind:
        return None

    registered = is_manifest_registered(path, corpus)
    action = "stage"
    reason = "registered small fixture or manifest-addressed artifact"
    if parts & CHECKPOINT_PARTS:
        action = "ignore"
        reason = "training checkpoint/intermediate output should not be staged directly"
    elif suffix in MODEL_SUFFIXES and not registered:
        action = "ignore"
        reason = "model binary/checkpoint is not registered in package manifest"
    elif suffix in ARCHIVE_SUFFIXES:
        action = "ignore"
        reason = "compressed artifact should not be staged directly"
    elif large_tier == "gt_5mb" and not registered:
        action = "manual_review"
        reason = "large artifact over 5MB is not manifest registered"
    elif suffix in IMAGE_SUFFIXES and size > 1024 * 1024 and not (parts & ALLOWED_SMALL_SAMPLE_PARTS):
        action = "ignore"
        reason = "large image dataset artifact should be represented by manifest/sample subset"

    return {
        "path": relative,
        "size_bytes": size,
        "large_tier": large_tier,
        "kind": kind,
        "manifest_registered": registered,
        "action": action,
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate visible or staged large/model/dataset artifacts.")
    parser.add_argument("--staged", action="store_true", help="scan only staged files from the git index")
    args = parser.parse_args()

    paths = git_paths(staged=args.staged)
    corpus = build_manifest_corpus(paths)
    items = [item for path in paths if (item := classify(path, corpus))]
    blockers = [item for item in items if item["action"] == "manual_review"]
    payload = {
        "tool": "validate_large_artifacts",
        "scope": "staged" if args.staged else "visible_status",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not blockers else "FAIL",
        "scanned_file_count": len(paths),
        "large_files": sum(1 for item in items if item["large_tier"] in {"gt_1mb", "gt_5mb"}),
        "gt_5mb_files": sum(1 for item in items if item["large_tier"] == "gt_5mb"),
        "model_artifacts": sum(1 for item in items if item["kind"] == "model_artifact"),
        "dataset_artifacts": sum(1 for item in items if item["kind"] == "dataset_image"),
        "ignore_recommendations": sum(1 for item in items if item["action"] == "ignore"),
        "manual_review_count": len(blockers),
        "items": items[:300],
    }
    if not args.staged and paths:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            "# Large Artifact Scan\n\n"
            f"checked_at: {payload['checked_at']}\n\n"
            f"status: {payload['status']}\n\n"
            f"scanned_file_count: {payload['scanned_file_count']}\n\n"
            f"large_files: {payload['large_files']}\n\n"
            f"gt_5mb_files: {payload['gt_5mb_files']}\n\n"
            f"model_artifacts: {payload['model_artifacts']}\n\n"
            f"dataset_artifacts: {payload['dataset_artifacts']}\n\n"
            f"ignore_recommendations: {payload['ignore_recommendations']}\n\n"
            f"manual_review_count: {payload['manual_review_count']}\n\n"
            "## Items\n\n"
            + json.dumps(payload["items"], ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
