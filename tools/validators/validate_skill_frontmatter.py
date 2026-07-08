#!/usr/bin/env python3
"""Validate SKILL.md YAML frontmatter for local loadability."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_yaml(frontmatter: str) -> tuple[dict | None, str | None]:
    try:
        import yaml  # type: ignore
    except Exception:
        meta: dict[str, str] = {}
        for line in frontmatter.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if key in {"name", "description"} and value.strip():
                meta[key] = value.strip()
        return meta, None

    try:
        meta = yaml.safe_load(frontmatter)
    except Exception as exc:  # pragma: no cover - exact parser messages vary
        return None, repr(exc)
    if not isinstance(meta, dict):
        return None, "frontmatter is not object"
    return meta, None


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n"):
        return ["missing opening ---"]
    try:
        end = text.index("\n---", 4)
    except ValueError:
        return ["missing closing ---"]

    meta, error = load_yaml(text[4:end])
    if error:
        errors.append(error)
    if not isinstance(meta, dict):
        return errors or ["frontmatter is not object"]
    for key in ("name", "description"):
        if key not in meta:
            errors.append(f"missing {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all SKILL.md frontmatter")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    root = Path(args.repo_root)
    failures: list[tuple[str, str]] = []
    count = 0
    for path in sorted(root.rglob("SKILL.md")):
        count += 1
        for error in validate_skill(path):
            failures.append((str(path), error))

    if failures:
        for path, error in failures:
            print("FAIL", path, error)
        return 1
    print(f"PASS all SKILL.md frontmatter ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
