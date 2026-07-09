#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "skills-manifest.json"
VALID_GATE_MODES = {"active", "advisory", "experimental", "excluded"}


class ManifestError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ManifestError(f"cannot read manifest: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ManifestError("manifest root must be an object")
    return payload


def load_manifest(path: Path | str = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest_path = Path(path)
    payload = _read_json(manifest_path)
    payload["_manifest_path"] = str(manifest_path.resolve())
    payload["_repo_root"] = str(manifest_path.resolve().parent)
    return payload


def manifest_repo_root(manifest: dict[str, Any]) -> Path:
    return Path(str(manifest.get("_repo_root") or REPO_ROOT)).resolve()


def layer_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = manifest.get("layers")
    if not isinstance(layers, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in layers:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            out[item["id"]] = item
    return out


def layer_thresholds(manifest: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for layer_id, item in layer_map(manifest).items():
        value = item.get("threshold")
        if isinstance(value, int):
            out[layer_id] = value
    return out


def layer_gate_modes(manifest: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for layer_id, item in layer_map(manifest).items():
        value = item.get("gate_mode")
        if isinstance(value, str):
            out[layer_id] = value
    return out


def skill_entries(manifest: dict[str, Any], installable_only: bool = False) -> list[dict[str, Any]]:
    skills = manifest.get("skills")
    if not isinstance(skills, list):
        return []
    entries = [item for item in skills if isinstance(item, dict)]
    if installable_only:
        entries = [item for item in entries if item.get("installable") is True]
    return entries


def skill_paths(manifest: dict[str, Any], installable_only: bool = False) -> list[Path]:
    root = manifest_repo_root(manifest)
    return [root / str(item["path"]) for item in skill_entries(manifest, installable_only) if isinstance(item.get("path"), str)]


def _observed_skill_paths(repo_root: Path) -> set[str]:
    skip = {".git", ".agent-control", ".claude", ".ci-out", ".ci-out-review", ".venv", "venv", "env", "node_modules", "dist", "coverage", "__pycache__"}
    observed: set[str] = set()
    for path in repo_root.rglob("SKILL.md"):
        try:
            rel_parts = path.relative_to(repo_root).parts
        except ValueError:
            continue
        if any(part in skip for part in rel_parts):
            continue
        observed.add(Path(*rel_parts[:-1]).as_posix())
    return observed


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    repo_root = manifest_repo_root(manifest)
    if manifest.get("manifest_version") != 1:
        errors.append("manifest_version must be 1")

    layers = layer_map(manifest)
    if not layers:
        errors.append("layers must be a non-empty list")
    for layer_id, item in layers.items():
        path = item.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"layer {layer_id}: missing path")
        elif not (repo_root / path).is_dir():
            errors.append(f"layer {layer_id}: path does not exist: {path}")
        threshold = item.get("threshold")
        if not isinstance(threshold, int) or threshold < 0 or threshold > 100:
            errors.append(f"layer {layer_id}: threshold must be 0..100")
        mode = item.get("gate_mode")
        if mode not in VALID_GATE_MODES:
            errors.append(f"layer {layer_id}: invalid gate_mode: {mode}")

    names: set[str] = set()
    paths: set[str] = set()
    manifest_paths: set[str] = set()
    entries = skill_entries(manifest)
    if not entries:
        errors.append("skills must be a non-empty list")
    for idx, item in enumerate(entries):
        name = item.get("name")
        path = item.get("path")
        layer = item.get("layer")
        label = str(name or f"skills[{idx}]")
        if not isinstance(name, str) or not name:
            errors.append(f"{label}: missing name")
        elif name in names:
            errors.append(f"{label}: duplicate name")
        else:
            names.add(name)
        if not isinstance(path, str) or not path:
            errors.append(f"{label}: missing path")
            continue
        if path in paths:
            errors.append(f"{label}: duplicate path: {path}")
        paths.add(path)
        manifest_paths.add(Path(path).as_posix())
        skill_dir = repo_root / path
        if not (skill_dir / "SKILL.md").is_file():
            errors.append(f"{label}: missing SKILL.md at {path}")
        if name and skill_dir.name != name:
            errors.append(f"{label}: name does not match directory basename {skill_dir.name}")
        installable = item.get("installable")
        if not isinstance(installable, bool):
            errors.append(f"{label}: installable must be a boolean")
        if layer not in layers:
            errors.append(f"{label}: unknown layer {layer}")
        else:
            layer_path = Path(str(layers[layer]["path"]))
            try:
                Path(path).relative_to(layer_path)
            except ValueError:
                errors.append(f"{label}: path is outside layer path {layer_path.as_posix()}")

    observed = _observed_skill_paths(repo_root)
    missing_from_manifest = sorted(observed - manifest_paths)
    missing_from_tree = sorted(manifest_paths - observed)
    if missing_from_manifest:
        errors.append("observed SKILL.md dirs missing from manifest: " + ", ".join(missing_from_manifest))
    if missing_from_tree:
        errors.append("manifest skill dirs missing from observed tree: " + ", ".join(missing_from_tree))
    return errors


def _load_or_exit(path: Path) -> dict[str, Any]:
    try:
        return load_manifest(path)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)


def _validate_or_exit(manifest: dict[str, Any]) -> None:
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = _load_or_exit(args.manifest)
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: skills-manifest.json is valid")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    manifest = _load_or_exit(args.manifest)
    _validate_or_exit(manifest)
    layers = layer_map(manifest)
    counts = {layer_id: 0 for layer_id in layers}
    for item in skill_entries(manifest):
        counts[str(item["layer"])] = counts.get(str(item["layer"]), 0) + 1
    payload = {
        "manifest_version": manifest["manifest_version"],
        "skill_count": len(skill_entries(manifest)),
        "installable_count": len(skill_entries(manifest, installable_only=True)),
        "layers": [
            {
                "id": layer_id,
                "path": item["path"],
                "threshold": item["threshold"],
                "gate_mode": item["gate_mode"],
                "skill_count": counts.get(layer_id, 0),
            }
            for layer_id, item in layers.items()
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_list_layers(args: argparse.Namespace) -> int:
    manifest = _load_or_exit(args.manifest)
    _validate_or_exit(manifest)
    for item in layer_map(manifest).values():
        ci = item.get("ci") if isinstance(item.get("ci"), dict) else {}
        if args.skill_bench and ci.get("skill_bench") is not True:
            continue
        if args.consistency_score and ci.get("consistency_score") is not True:
            continue
        print(item["path"])
    return 0


def cmd_list_skills(args: argparse.Namespace) -> int:
    manifest = _load_or_exit(args.manifest)
    _validate_or_exit(manifest)
    entries = skill_entries(manifest, installable_only=args.installable)
    if args.paths:
        key = "path"
    elif args.names:
        key = "name"
    else:
        key = "path"
    for item in entries:
        print(item[key])
    return 0


def _bash_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def cmd_emit_install(args: argparse.Namespace) -> int:
    manifest = _load_or_exit(args.manifest)
    _validate_or_exit(manifest)
    repo = args.repo
    dst = args.dst
    entries = skill_entries(manifest, installable_only=True)
    if args.shell == "bash":
        print(f"REPO={_bash_quote(repo)}")
        print(f"DST={_bash_quote(dst)}")
        print('mkdir -p "$DST"')
        for item in entries:
            print(f'ln -snf "$REPO/{item["path"]}" "$DST/{item["name"]}"')
    elif args.shell == "powershell":
        print(f"$REPO = {_powershell_quote(repo)}")
        print(f"$DST = {_powershell_quote(dst)}")
        print("New-Item -ItemType Directory -Path $DST -Force | Out-Null")
        for item in entries:
            rel_path = str(item["path"]).replace("/", "\\")
            name = item["name"]
            print(f"New-Item -ItemType Junction -Path (Join-Path $DST {_powershell_quote(name)}) -Target (Join-Path $REPO {_powershell_quote(rel_path)}) -Force")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and validate the SKILLS manifest")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="manifest path")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate manifest against the worktree")
    validate.set_defaults(func=cmd_validate)

    summary = sub.add_parser("summary", help="print manifest summary JSON")
    summary.set_defaults(func=cmd_summary)

    list_layers = sub.add_parser("list-layers", help="print layer paths")
    list_layers.add_argument("--skill-bench", action="store_true", help="only layers enabled for skill bench")
    list_layers.add_argument("--consistency-score", action="store_true", help="only layers enabled for consistency scoring")
    list_layers.set_defaults(func=cmd_list_layers)

    list_skills = sub.add_parser("list-skills", help="print skill paths or names")
    group = list_skills.add_mutually_exclusive_group()
    group.add_argument("--paths", action="store_true", help="print skill paths")
    group.add_argument("--names", action="store_true", help="print skill names")
    list_skills.add_argument("--installable", action="store_true", help="only installable skills")
    list_skills.set_defaults(func=cmd_list_skills)

    emit_install = sub.add_parser("emit-install", help="print install commands without executing them")
    emit_install.add_argument("--shell", choices=("bash", "powershell"), required=True)
    emit_install.add_argument("--repo", required=True, help="repository path to use in emitted commands")
    emit_install.add_argument("--dst", required=True, help="destination skills directory to use in emitted commands")
    emit_install.set_defaults(func=cmd_emit_install)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
