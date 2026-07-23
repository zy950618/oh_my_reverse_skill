#!/usr/bin/env python3
"""Build the repository Capability Matrix from one finite, evidence-bound schema."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


CATALOG_KEYS = {"id", "title", "evidence"}
EVIDENCE_FIELDS = {"kind", "path", "sha256", "symbol_or_command", "claim"}
KINDS = {"producer", "consumer", "test", "external_dependency", "documentation"}
AXIS_KINDS = ("producer", "consumer", "test", "external_dependency", "documentation")
HARD_CODES = {
    "duplicate_authority", "duplicate_evidence", "duplicate_legacy_disposition",
    "evidence_directory", "evidence_hash_missing", "evidence_hash_stale",
    "evidence_missing", "evidence_path_escape", "evidence_symlink_escape",
    "evidence_binding_missing", "malformed_evidence", "missing_command", "missing_legacy_disposition",
    "path_escape", "unknown_capability", "wrapper_target_mismatch", "wrapper_target_missing",
}
COMMAND_FILES = ("README.md", "INSTALL.md", "USAGE.md", "SKILL.md")
SCRIPT_SUFFIXES = (".py", ".js", ".mjs", ".cjs", ".sh")
DISCOVERY_IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
}
SECRET_RE = re.compile(r"(?i)(?:token|password|secret|api[_-]?key)=([^\s]+)")
SECRET_OPTION_RE = re.compile(r"(?i)^--?(?:token|password|secret|api[_-]?key)$")


class MatrixError(ValueError):
    """A deterministic input-contract failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_schema(path: Path) -> dict[str, Any]:
    """Load the YAML schema. The checked-in schema uses JSON, a strict YAML subset."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MatrixError(f"schema is not strict JSON-compatible YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise MatrixError("schema root must be an object")
    return data


def finding(code: str, message: str, *, source_path: str = "tools/capabilities/schema.yaml",
            line: int = 0, capability_id: str | None = None, hard: bool | None = None) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "code": code,
        "hard": code in HARD_CODES if hard is None else hard,
        "line": line,
        "message": message,
        "source_path": source_path,
    }


def _inside_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_repository_path(root: Path, raw: str) -> tuple[Path | None, str | None]:
    root = root.resolve()
    if not raw or "\x00" in raw:
        return None, "evidence_path_escape"
    posix = PurePosixPath(raw.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        return None, "evidence_path_escape"
    lexical = root.joinpath(*posix.parts)
    try:
        resolved = lexical.resolve(strict=False)
    except OSError:
        return None, "evidence_path_escape"
    if not _inside_root(root, resolved):
        return None, "evidence_symlink_escape"
    return lexical, None


def _concrete_symbol(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(
        marker in value for marker in ("TODO", "<...>", "...", "${")
    )


def _python_symbols(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    except (OSError, UnicodeError, SyntaxError):
        return set()
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _ignored_discovery_path(path: Path, root: Path) -> bool:
    return any(part in DISCOVERY_IGNORED_DIRS for part in path.relative_to(root).parts)


def _script_roots(root: Path) -> set[str]:
    """Return stable top-level directories containing repository scripts."""
    roots: set[str] = set()
    for path in root.rglob("*"):
        if _ignored_discovery_path(path, root):
            continue
        if path.is_file() and path.suffix in SCRIPT_SUFFIXES:
            relative = path.relative_to(root).parts
            if len(relative) > 1:
                roots.add(relative[0])
    return roots


def _python_wrapper_target(root: Path, path: Path) -> str | None:
    """Find only a single literal runpy forwarding target."""
    if path.name.startswith("test_") or "tests" in path.relative_to(root).parts:
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    except (OSError, UnicodeError, SyntaxError, ValueError):
        return None
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.While)) for node in tree.body):
        return None
    top_level_guards = [node for node in tree.body if isinstance(node, ast.If)]
    if top_level_guards and any(
        not (
            isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Eq)
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == "__main__"
        )
        for node in top_level_guards
    ):
        return None
    targets: list[str] = []
    forwarding_calls = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "runpy" and node.func.attr == "run_path"):
            continue
        forwarding_calls += 1
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            return None
        target = node.args[0].value.replace("\\", "/")
        candidate, issue = resolve_repository_path(root, target)
        if issue or candidate is None or not candidate.is_file() or candidate.suffix not in SCRIPT_SUFFIXES:
            return None
        targets.append(target)
    if forwarding_calls != 1 or len(set(targets)) != 1:
        return None
    return targets[0]


def discover_wrappers(root: Path) -> list[dict[str, Any]]:
    """Mechanically discover conservative Python runpy forwarding wrappers."""
    discovered: list[dict[str, Any]] = []
    for path in root.rglob("*.py"):
        if _ignored_discovery_path(path, root):
            continue
        target = _python_wrapper_target(root, path)
        if target is not None:
            discovered.append({
                "path": path.relative_to(root).as_posix(),
                "target": target,
                "line": 1,
            })
    return sorted(discovered, key=lambda item: (item["path"], item["target"], item["line"]))


def _binding_exists(path: Path, kind: str, binding: str) -> bool:
    """Prove that an evidence entrypoint is present in the exact hashed file."""
    if path.suffix == ".py" and kind in {"producer", "test"}:
        return binding in _python_symbols(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    if kind == "consumer":
        normalized_text = re.sub(r"\s+", " ", text.replace("\\\n", " "))
        normalized_binding = re.sub(r"\s+", " ", binding).strip()
        return normalized_binding in normalized_text
    if path.suffix in {".js", ".mjs", ".cjs", ".sh"}:
        return bool(re.search(rf"(?<![A-Za-z0-9_$]){re.escape(binding)}(?![A-Za-z0-9_$])", text))
    return True


def validate_evidence(root: Path, capability_id: str, item: Any) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    if not isinstance(item, dict) or set(item) != EVIDENCE_FIELDS or item.get("kind") not in KINDS:
        return None, [finding("malformed_evidence", "evidence must contain exactly the required fields and an allowed kind", capability_id=capability_id)]
    normalized = {key: item[key] for key in sorted(EVIDENCE_FIELDS)}
    kind = item["kind"]
    if not all(isinstance(item.get(key), str) and item[key].strip() for key in ("path", "symbol_or_command", "claim")):
        issues.append(finding("malformed_evidence", "path, symbol_or_command, and claim must be non-empty strings", capability_id=capability_id))
        return None, issues
    if kind == "external_dependency":
        metadata = item["symbol_or_command"] + " " + item["claim"]
        has_source = bool(re.search(r"(?i)\bsource\s*=\s*\S+", metadata))
        has_version = bool(re.search(r"(?i)\b(?:version\s*=\s*\S+|unlocked\b)", metadata))
        if item["sha256"] is not None or not (has_source and has_version):
            issues.append(finding("malformed_evidence", "external evidence requires sha256=null and explicit source plus version or unlocked metadata", capability_id=capability_id))
            return None, issues
        return normalized, issues
    if not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
        issues.append(finding("evidence_hash_missing", "repository evidence requires a lowercase SHA-256", capability_id=capability_id))
        return None, issues
    path, path_issue = resolve_repository_path(root, item["path"])
    if path_issue:
        issues.append(finding(path_issue, f"evidence path is outside repository: {item['path']}", capability_id=capability_id))
        return None, issues
    assert path is not None
    if not path.exists():
        issues.append(finding("evidence_missing", f"evidence path does not exist: {item['path']}", capability_id=capability_id))
    elif not path.is_file():
        issues.append(finding("evidence_directory", f"evidence path is not a regular file: {item['path']}", capability_id=capability_id))
    elif sha256_file(path) != item["sha256"]:
        issues.append(finding("evidence_hash_stale", f"evidence hash is stale: {item['path']}", capability_id=capability_id))
    if kind in {"producer", "consumer", "test"} and not _concrete_symbol(item["symbol_or_command"]):
        issues.append(finding("malformed_evidence", f"{kind} requires a concrete symbol or command", capability_id=capability_id))
    if kind == "producer" and path is not None and path.is_file() and path.suffix not in SCRIPT_SUFFIXES:
        issues.append(finding("malformed_evidence", "producer must be an executable script file", capability_id=capability_id))
    if kind == "consumer" and path is not None and path.is_file() and path.suffix not in SCRIPT_SUFFIXES + (".yml", ".yaml"):
        issues.append(finding("malformed_evidence", "consumer must be a caller, bundled script, workflow, or tested integration edge", capability_id=capability_id))
    if kind == "test" and path is not None and path.is_file() and not (path.suffix == ".py" and (path.name.startswith("test_") or "/tests/" in "/" + item["path"])):
        issues.append(finding("malformed_evidence", "test evidence must point to an automated test file", capability_id=capability_id))
    if kind in {"producer", "consumer", "test"} and path is not None and path.is_file() and not issues:
        if not _binding_exists(path, kind, item["symbol_or_command"]):
            issues.append(finding(
                "evidence_binding_missing",
                f"{kind} binding is absent from hashed evidence file: {item['symbol_or_command']}",
                capability_id=capability_id,
            ))
    return (normalized if not issues else None), issues


def validate_catalog(schema: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = schema.get("catalog")
    if not isinstance(entries, list):
        raise MatrixError("catalog must be a list")
    declared = schema.get("allowed_capability_ids")
    if not isinstance(declared, list) or not all(isinstance(value, str) and value for value in declared):
        raise MatrixError("allowed_capability_ids must be a non-empty string list")
    if len(declared) != len(set(declared)):
        raise MatrixError("duplicate capability id in allowed_capability_ids")
    seen: set[str] = set()
    records: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for raw in entries:
        if not isinstance(raw, dict) or set(raw) != CATALOG_KEYS:
            raise MatrixError("each catalog entry must contain exactly id, title, and evidence")
        capability_id = raw["id"]
        if capability_id not in declared:
            findings.append(finding("unknown_capability", f"unknown capability id: {capability_id}", capability_id=str(capability_id)))
            continue
        if capability_id in seen:
            raise MatrixError(f"duplicate catalog id: {capability_id}")
        seen.add(capability_id)
        if not isinstance(raw["title"], str) or not raw["title"].strip() or not isinstance(raw["evidence"], list):
            raise MatrixError(f"invalid catalog entry: {capability_id}")
        valid: list[dict[str, Any]] = []
        evidence_seen: set[tuple[Any, ...]] = set()
        for item in raw["evidence"]:
            normalized, evidence_findings = validate_evidence(root, capability_id, item)
            findings.extend(evidence_findings)
            if normalized:
                identity = tuple(normalized.get(key) for key in ("kind", "path", "symbol_or_command", "claim"))
                if identity in evidence_seen:
                    findings.append(finding("duplicate_evidence", "duplicate evidence binding", capability_id=capability_id))
                else:
                    evidence_seen.add(identity)
                    valid.append(normalized)
        grouped = {kind: sorted((e for e in valid if e["kind"] == kind), key=lambda e: (e["path"], e["symbol_or_command"], e["claim"])) for kind in AXIS_KINDS}
        capability_findings = [item for item in findings if item["capability_id"] == capability_id]
        records.append({"id": capability_id, "title": raw["title"], "evidence": grouped, "findings": capability_findings})
    missing = sorted(set(declared) - seen)
    if missing:
        raise MatrixError("catalog is missing allowed ids: " + ", ".join(missing))
    return sorted(records, key=lambda item: item["id"]), findings


def grade_capability(record: dict[str, Any]) -> dict[str, Any]:
    evidence = record["evidence"]
    axes = {
        "I": bool(evidence["producer"]),
        "T": bool(evidence["test"]),
        "D": bool(evidence["documentation"]),
        "E": bool(evidence["external_dependency"]),
        "U": bool(record["findings"]) or not (bool(evidence["producer"]) and bool(evidence["test"])),
    }
    if axes["I"] and axes["T"]:
        grade = "I+T"
    elif axes["I"]:
        grade = "I-only"
    elif axes["T"]:
        grade = "T-only"
    elif axes["D"] or axes["E"]:
        grade = "D/E-only"
    else:
        grade = "U"
        axes["U"] = True
    if evidence["producer"] and evidence["consumer"] and evidence["test"]:
        integration_status = "INTEGRATED"
    elif evidence["producer"] and evidence["test"]:
        integration_status = "IMPLEMENTED_TESTED_UNCONSUMED"
    elif evidence["producer"]:
        integration_status = "IMPLEMENTED_UNPROVEN"
    elif evidence["test"]:
        integration_status = "TEST_ONLY"
    else:
        integration_status = "UNIMPLEMENTED"
    return {**record, "axes": axes, "display_grade": grade, "integration_status": integration_status}


def discover_documents(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if _ignored_discovery_path(path, root):
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.name in COMMAND_FILES or relative.endswith(".contract.md") or (relative.startswith(".github/workflows/") and path.suffix in {".yml", ".yaml"}):
            result.append(path)
    return sorted(result, key=lambda item: item.relative_to(root).as_posix())


def _is_placeholder(command: str) -> bool:
    return (
        bool(re.search(r"(?:<[^>]+>|\$\{|\bTODO\b|(?:^|\s)\.\.\.(?:\s|$))", command))
        or command.lstrip().startswith("#")
        or bool(re.search(r"(?:^|\s)--help(?:\s|$)", command))
    )


def _command_path(argv: list[str], script_roots: set[str] | None = None) -> str | None:
    if not argv:
        return None
    while argv and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", argv[0]):
        argv = argv[1:]
    if not argv:
        return None
    if argv[0] in {"python", "python3", "node", "bash", "sh"}:
        index = 1
        while index < len(argv) and argv[index] in {"-B", "-E", "-I", "-O", "-OO", "-s", "-S", "-u"}:
            index += 1
        if index >= len(argv) or argv[index] in {"-", "-m", "-c", "--version", "--help"}:
            return None
        return argv[index]
    if argv[0].startswith("./"):
        return argv[0]
    if script_roots and len(PurePosixPath(argv[0].replace("\\", "/")).parts) > 1:
        relative = PurePosixPath(argv[0].replace("\\", "/"))
        if relative.parts[0] in script_roots and relative.suffix in SCRIPT_SUFFIXES:
            return argv[0]
    return None


def _extract_markdown_commands(path: Path) -> Iterable[tuple[int, str]]:
    in_fence = False
    shell_fence = False
    explicit = False
    pending: list[str] = []
    pending_line = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                language = stripped[3:].strip().lower()
                shell_fence = language in {"", "bash", "sh", "shell", "console", "powershell"}
                in_fence = True
            else:
                in_fence = shell_fence = False
            continue
        if re.match(r"^#{1,6}\s+.*(?:command|commands|命令|用法|usage)", stripped, re.I):
            explicit = True
            continue
        if explicit and stripped.startswith("#"):
            explicit = False
        if (in_fence and shell_fence) or explicit:
            candidate = re.sub(r"^\s*(?:\$|>)\s*", "", line).strip()
            if candidate and not candidate.startswith("#"):
                if not pending:
                    pending_line = number
                pending.append(candidate[:-1].rstrip() if candidate.endswith("\\") else candidate)
                if not candidate.endswith("\\"):
                    yield pending_line, " ".join(pending)
                    pending = []
    if pending:
        yield pending_line, " ".join(pending)


def _extract_workflow_commands(path: Path) -> Iterable[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent, value = len(match.group(1)), match.group(2).strip()
        if value not in {"|", ">", "|-", ">-"}:
            if value:
                yield index + 1, value.strip("'\"")
            index += 1
            continue
        index += 1
        pending: list[str] = []
        pending_line = 0
        heredoc: str | None = None
        while index < len(lines):
            current = lines[index]
            if current.strip() and len(current) - len(current.lstrip()) <= indent:
                break
            stripped_current = current.strip()
            if heredoc is not None:
                if stripped_current == heredoc:
                    heredoc = None
                index += 1
                continue
            if current.strip() and not current.lstrip().startswith("#"):
                candidate = stripped_current
                if not pending:
                    pending_line = index + 1
                pending.append(candidate[:-1].rstrip() if candidate.endswith("\\") else candidate)
                if not candidate.endswith("\\"):
                    yield pending_line, " ".join(pending)
                    pending = []
                    try:
                        parsed = shlex.split(candidate, posix=True)
                    except ValueError:
                        parsed = []
                    marker_match = re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?", candidate)
                    if marker_match:
                        heredoc = marker_match.group(1)
            index += 1
        if pending:
            yield pending_line, " ".join(pending)


def _redact_argv(argv: list[str]) -> list[str]:
    redacted: list[str] = []
    hide_next = False
    for arg in argv:
        if hide_next:
            redacted.append("<redacted>")
            hide_next = False
        else:
            cleaned = SECRET_RE.sub(lambda match: match.group(0).split("=", 1)[0] + "=<redacted>", arg)
            redacted.append(cleaned)
            hide_next = bool(SECRET_OPTION_RE.fullmatch(arg))
    return redacted


def scan_document_commands(root: Path, documents: list[Path] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    commands: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    script_roots = _script_roots(root)
    for path in documents or discover_documents(root):
        relative = path.relative_to(root).as_posix()
        extracted = _extract_workflow_commands(path) if relative.startswith(".github/workflows/") else _extract_markdown_commands(path)
        for line, command in extracted:
            placeholder = _is_placeholder(command) or command in {"set -e", "set -eu", "set -euo pipefail"}
            try:
                argv = shlex.split(command.replace("\\", "/"), posix=True)
            except ValueError:
                commands.append({"argv": [], "executable": False, "line": line, "source_path": relative})
                findings.append(finding("ambiguous_placeholder", "command could not be parsed and was retained as documentation", source_path=relative, line=line, hard=False))
                continue
            target = _command_path(argv, script_roots)
            executable = bool(target) and not placeholder
            commands.append({"argv": _redact_argv(argv), "executable": executable, "line": line, "source_path": relative})
            if not executable or target is None:
                continue
            candidate, issue = resolve_repository_path(root, target)
            if issue:
                findings.append(finding("path_escape", f"command target escapes repository: {target}", source_path=relative, line=line))
            elif candidate is None or not candidate.is_file():
                findings.append(finding("missing_command", f"command target is missing: {target}", source_path=relative, line=line))
    key = lambda item: (item["source_path"], item["line"], item.get("code", ""), item.get("argv", []))
    return sorted(commands, key=key), sorted(findings, key=key)


def validate_legacy(
    schema: dict[str, Any],
    root: Path,
    discovered: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_entries = schema.get("legacy_entries", [])
    if not isinstance(raw_entries, list):
        raise MatrixError("legacy_entries must be a list")
    entries: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    authorities: dict[str, list[str]] = {}
    seen: set[str] = set()
    declared_by_path: dict[str, list[dict[str, Any]]] = {}
    for raw in raw_entries:
        if not isinstance(raw, dict) or set(raw) != {"path", "target", "disposition"}:
            raise MatrixError("legacy entry must contain exactly path, target, and disposition")
        declared_by_path.setdefault(raw["path"], []).append(raw)

    for raw in raw_entries:
        path, target, disposition = raw["path"], raw["target"], raw["disposition"]
        duplicate = path in seen
        if duplicate:
            findings.append(finding("duplicate_legacy_disposition", f"legacy path has multiple dispositions: {path}"))
        seen.add(path)
        if disposition not in {"compatible_wrapper", "unified_migration"}:
            findings.append(finding("missing_legacy_disposition", f"legacy path lacks a valid disposition: {path}"))
        path_candidate, path_issue = resolve_repository_path(root, path)
        target_candidate, target_issue = resolve_repository_path(root, target)
        for candidate, issue, value, label in (
            (path_candidate, path_issue, path, "legacy"),
            (target_candidate, target_issue, target, "target"),
        ):
            if issue:
                findings.append(finding("path_escape", f"{label} path escapes repository: {value}"))
            elif candidate is None or not candidate.is_file():
                findings.append(finding("wrapper_target_missing", f"{label} path is missing: {value}"))
        if (
            disposition == "compatible_wrapper"
            and not duplicate
            and not path_issue
            and not target_issue
            and path_candidate is not None
            and target_candidate is not None
            and path_candidate.is_file()
            and target_candidate.is_file()
        ):
            try:
                wrapper_text = path_candidate.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                wrapper_text = ""
            target_posix = PurePosixPath(target)
            target_markers = {target, target_posix.name, target_posix.stem}
            if not any(marker in wrapper_text for marker in target_markers):
                findings.append(finding("wrapper_target_mismatch", f"wrapper does not reference canonical target: {path} -> {target}"))
            else:
                authorities.setdefault(target, []).append(path)
        if not duplicate and disposition in {"compatible_wrapper", "unified_migration"}:
            entries.append({"disposition": disposition, "path": path, "target": target})

    for wrapper in discovered or discover_wrappers(root):
        path, target = wrapper["path"], wrapper["target"]
        declarations = declared_by_path.get(path, [])
        matching = [item for item in declarations if item.get("target") == target]
        if not matching:
            findings.append(finding(
                "missing_legacy_disposition",
                f"discovered wrapper lacks a matching disposition: {path} -> {target}",
                source_path=path,
                line=wrapper.get("line", 0),
            ))
            authorities.setdefault(target, []).append(path)
        elif any(item.get("disposition") == "unified_migration" for item in matching):
            findings.append(finding(
                "wrapper_target_mismatch",
                f"active wrapper cannot be unified_migration: {path} -> {target}",
                source_path=path,
                line=wrapper.get("line", 0),
            ))
        elif any(item.get("disposition") == "compatible_wrapper" for item in matching):
            authorities.setdefault(target, []).append(path)

    for target, wrappers in authorities.items():
        unique_wrappers = sorted(set(wrappers))
        if len(unique_wrappers) > 1:
            findings.append(finding("duplicate_authority", f"multiple wrappers claim canonical target {target}: {', '.join(unique_wrappers)}"))
    return sorted(entries, key=lambda item: item["path"]), sorted(findings, key=lambda item: (item["source_path"], item["line"], item["code"]))


def build_model(schema: dict[str, Any], root: Path, documents: list[Path] | None = None) -> dict[str, Any]:
    capabilities, evidence_findings = validate_catalog(schema, root)
    commands, command_findings = scan_document_commands(root, documents)
    legacy, legacy_findings = validate_legacy(schema, root, discover_wrappers(root))
    all_findings = evidence_findings + command_findings + legacy_findings
    all_findings.sort(key=lambda item: (item["source_path"], item["line"], item["code"], item["capability_id"] or ""))
    graded = [grade_capability(record) for record in capabilities]
    return {
        "capabilities": graded,
        "command_scan": {"commands": commands, "documents_scanned": len(documents or discover_documents(root))},
        "findings": all_findings,
        "generator": "tools/capabilities/capability_matrix.py",
        "legacy_entries": legacy,
        "schema_version": schema.get("schema_version"),
        "shared_infrastructure_only": True,
        "summary": {"capability_count": len(graded), "hard_finding_count": sum(1 for item in all_findings if item["hard"]), "finding_count": len(all_findings)},
    }


def render_json(model: dict[str, Any]) -> bytes:
    return (json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def render_markdown(model: dict[str, Any]) -> bytes:
    lines = ["# Capability Matrix", "", "Canonical shared-infrastructure report. It does not claim active Skill integration or external-service success.", "", "| Capability | I | T | D | E | U | Grade | Integration |", "|---|:---:|:---:|:---:|:---:|:---:|---|---|"]
    for item in model["capabilities"]:
        axes = item["axes"]
        marks = [("yes" if axes[key] else "no") for key in ("I", "T", "D", "E", "U")]
        lines.append(f"| `{item['id']}` | " + " | ".join(marks) + f" | {item['display_grade']} | {item['integration_status']} |")
    lines.extend(["", "## Findings", ""])
    if model["findings"]:
        for item in model["findings"]:
            severity = "HARD" if item["hard"] else "INFO"
            lines.append(f"- {severity} `{item['code']}` {item['source_path']}:{item['line']} — {item['message']}")
    else:
        lines.append("- No findings.")
    lines.extend(["", "## Legacy dispositions", ""])
    if model["legacy_entries"]:
        for item in model["legacy_entries"]:
            lines.append(f"- `{item['path']}` → `{item['target']}`: `{item['disposition']}`")
    else:
        lines.append("- No legacy entries are declared by this catalog.")
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_reports(model: dict[str, Any], root: Path) -> None:
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "capability-matrix.json").write_bytes(render_json(model))
    (reports / "capability-matrix.md").write_bytes(render_markdown(model))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default="tools/capabilities/schema.yaml")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        schema_path = Path(args.schema)
        if not schema_path.is_absolute():
            schema_path = root / schema_path
        model = build_model(load_schema(schema_path), root)
        write_reports(model, root)
    except (MatrixError, OSError, UnicodeError) as exc:
        print(f"capability-matrix: {exc}", file=sys.stderr)
        return 2
    hard = model["summary"]["hard_finding_count"]
    print(f"capability-matrix: {len(model['capabilities'])} capabilities, {hard} hard findings")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
