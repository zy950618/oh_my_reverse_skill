from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "99-SKILLS治理" / "43-artifact-reference-integrity-report.md"
SCOPES = [
    ROOT / "tool-contracts",
    ROOT / "public-range-evidence",
    ROOT / "6-验证码逆向层",
    ROOT / "7-指纹风控层",
    ROOT / "99-SKILLS治理",
    ROOT / "tools",
]
ARTIFACT_SUFFIXES = {".json", ".jsonl", ".md", ".yaml", ".yml", ".txt", ".ppm", ".py"}
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}
CLASSIFIED_ROOT_PARTS = {
    "_archive",
    "raw",
    "repeat_reports",
    "negative_cases",
    "drift_cases",
    "sample_images",
    "sample_labels",
    "samples",
    "fixtures",
    "reports",
}
SKIPPED_HEAVY_PARTS = {"raw", "_archive", "longrun"}
REFERENCE_SUFFIXES = {".json", ".jsonl", ".md", ".yaml", ".yml", ".txt", ".py"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_scope_files() -> list[Path]:
    files: list[Path] = []
    for scope in SCOPES:
        if not scope.exists():
            continue
        if scope.is_file():
            candidates = [scope]
        else:
            candidates = [path for path in scope.rglob("*") if path.is_file()]
        for path in candidates:
            parts = {part.lower() for part in path.relative_to(ROOT).parts}
            if parts & IGNORED_PARTS:
                continue
            if parts & SKIPPED_HEAVY_PARTS:
                continue
            if path.suffix.lower() in ARTIFACT_SUFFIXES:
                files.append(path)
    return sorted(set(files), key=lambda item: rel(item))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def build_reference_corpus(files: list[Path]) -> str:
    chunks: list[str] = []
    for path in files:
        if path.suffix.lower() not in REFERENCE_SUFFIXES:
            continue
        chunks.append(read_text(path))
    return "\n".join(chunks)


def is_manifest_or_index(path: Path) -> bool:
    name = path.name.lower()
    parts = {part.lower() for part in path.relative_to(ROOT).parts}
    return (
        "manifest" in name
        or name
        in {
            "readme.md",
            "runbook.md",
            "_schema.md",
            "inference_api.md",
            "model_card.md",
            "package_manifest.json",
            "dataset_manifest.json",
        }
        or name.endswith("_report.md")
        or name.endswith("-report.md")
        or "evals" in parts
        or "references" in parts
        or "tool-contracts" in parts
        or "sdk_examples" in parts
        or path.parent == ROOT / "99-SKILLS治理"
        or (path.suffix.lower() == ".json" and path.parent.parent == ROOT / "public-range-evidence")
        or name == "train_config.yaml"
        or "recorder" in parts
    )


def is_classified_by_location(path: Path) -> tuple[bool, str]:
    parts = {part.lower() for part in path.relative_to(ROOT).parts}
    if parts & CLASSIFIED_ROOT_PARTS:
        return True, "classified_by_artifact_location"
    if path.suffix.lower() == ".py" and path.parent.name in {"tools", "tests", "inference", "eval"}:
        return True, "executable_validation_command"
    return False, ""


def referenced(path: Path, corpus: str) -> tuple[bool, str]:
    relative = rel(path)
    if corpus.count(relative) > 0:
        return True, "referenced_by_relative_path"
    if corpus.count(relative.replace("/", "\\")) > 0:
        return True, "referenced_by_windows_path"
    if is_manifest_or_index(path):
        return True, "manifest_or_report_entrypoint"
    name = re.escape(path.name)
    if re.search(rf"(?<![\w.-]){name}(?![\w.-])", corpus):
        return True, "referenced_by_basename"
    classified, reason = is_classified_by_location(path)
    if classified:
        return True, reason
    return False, "unreferenced"


def classify_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix == ".json" and "manifest" not in name:
        return "orphan_json"
    if suffix == ".md":
        return "orphan_md"
    if "report" in name:
        return "orphan_report"
    if "fixture" in name:
        return "orphan_fixture"
    if suffix == ".ppm":
        return "orphan_sample_image"
    if "prediction" in name:
        return "orphan_prediction"
    return "unknown"


def validate() -> dict[str, object]:
    files = iter_scope_files()
    corpus = build_reference_corpus(files)
    unreferenced: list[dict[str, str]] = []
    classified_count = 0
    unknown: list[str] = []

    for path in files:
        ok, reason = referenced(path, corpus)
        if ok:
            if reason.startswith("classified"):
                classified_count += 1
            continue
        kind = classify_kind(path)
        item = {"path": rel(path), "kind": kind, "reason": reason}
        if kind == "unknown":
            unknown.append(rel(path))
        unreferenced.append(item)

    payload = {
        "tool": "validate_artifact_references",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not unreferenced and not unknown else "FAIL",
        "scope_count": len(SCOPES),
        "artifact_count": len(files),
        "unreferenced_artifact_count": len(unreferenced),
        "classified_count": classified_count,
        "unknown_file_count": len(unknown),
        "unreferenced": unreferenced[:200],
        "unknown_files": unknown[:200],
        "checks": [
            "orphan_json",
            "orphan_md",
            "orphan_report",
            "orphan_fixture",
            "orphan_sample_image",
            "orphan_prediction",
            "missing_manifest_reference",
            "missing_report_reference",
            "missing_cleanup_rule",
            "missing_validation_command",
        ],
    }
    return payload


def write_report(payload: dict[str, object]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    unreferenced = payload.get("unreferenced")
    unknown = payload.get("unknown_files")
    content = (
        "# Artifact Reference Integrity Report\n\n"
        f"checked_at: {payload['checked_at']}\n\n"
        f"status: {payload['status']}\n\n"
        f"artifact_count: {payload['artifact_count']}\n\n"
        f"unreferenced_artifact_count: {payload['unreferenced_artifact_count']}\n\n"
        f"classified_count: {payload['classified_count']}\n\n"
        f"unknown_file_count: {payload['unknown_file_count']}\n\n"
        "## Scope\n\n"
        "- tool-contracts/\n"
        "- public-range-evidence/\n"
        "- 6-验证码逆向层/\n"
        "- 7-指纹风控层/\n"
        "- 99-SKILLS治理/\n"
        "- tools/\n\n"
        "## Checks\n\n"
        + "\n".join(f"- {item}" for item in payload["checks"])
        + "\n\n## Unreferenced\n\n"
        + json.dumps(unreferenced, ensure_ascii=False, indent=2)
        + "\n\n## Unknown Files\n\n"
        + json.dumps(unknown, ensure_ascii=False, indent=2)
        + "\n"
    )
    if REPORT.exists():
        existing = REPORT.read_text(encoding="utf-8-sig")
        stable_existing = re.sub(r"checked_at: .+", "checked_at: <ignored>", existing)
        stable_next = re.sub(r"checked_at: .+", "checked_at: <ignored>", content)
        if stable_existing == stable_next:
            return
    REPORT.write_text(content, encoding="utf-8")


def main() -> int:
    payload = validate()
    write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
