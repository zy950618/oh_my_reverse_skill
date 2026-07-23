"""Deterministic artifact provenance manifests with an external trust anchor."""

from __future__ import annotations

import json
import os
import re
import stat
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence
from urllib.parse import parse_qsl, urlsplit

from run_context import (
    ProvenanceError,
    sha256_bytes,
    utc_now,
    validate_command_record,
    validate_input_hashes,
    validate_timestamp,
)


SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_KEY = re.compile(
    r"(?i)(?:^|[-_.])(authorization|cookie|set-cookie|secret|token|"
    r"api[-_]?key|password|passwd)(?:$|[-_.])"
)
_SENSITIVE_TEXT = re.compile(
    r"(?i)(?:authorization\s*:|cookie\s*:|set-cookie\s*:|bearer\s+|"
    r"(?:secret|token|api[-_]?key|password|passwd)\s*[=:])"
)
_ARTIFACT_KEYS = (
    "path",
    "sha256",
    "producer_run_id",
    "producer",
    "target",
    "input_hashes",
    "created_at",
)
_MANIFEST_KEYS = ("schema_version", "runs", "artifacts")


def _reject_constant(_value: str) -> None:
    raise ProvenanceError("non-finite JSON number rejected")


def _sensitive_key(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if _SENSITIVE_KEY.search(value):
        return True
    normalized = re.sub(r"[^a-z0-9]", "", value.casefold())
    return normalized in {
        "authorization",
        "cookie",
        "setcookie",
        "secret",
        "token",
        "accesstoken",
        "refreshtoken",
        "apikey",
        "password",
        "passwd",
    }


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProvenanceError("duplicate JSON key rejected")
        result[key] = value
    return result


def strict_json_loads(data: bytes) -> object:
    if not isinstance(data, bytes):
        raise ProvenanceError("manifest input must be bytes")
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except UnicodeDecodeError:
        raise ProvenanceError("manifest is not strict UTF-8") from None
    except json.JSONDecodeError:
        raise ProvenanceError("manifest is not strict JSON") from None


def _contains_secret(value: object, key: str | None = None) -> bool:
    if key is not None and _sensitive_key(key):
        return True
    if isinstance(value, dict):
        return any(_contains_secret(child, str(child_key)) for child_key, child in value.items())
    if isinstance(value, list):
        return any(_contains_secret(child) for child in value)
    if not isinstance(value, str):
        return False
    if _SENSITIVE_TEXT.search(value):
        return True
    try:
        query = urlsplit(value).query
    except ValueError:
        return True
    return any(_sensitive_key(name) for name, _ in parse_qsl(query, keep_blank_values=True))


def reject_secrets(value: object) -> None:
    if _contains_secret(value):
        raise ProvenanceError("sensitive provenance data rejected")


def redact_mapping(value: Mapping[str, object]) -> dict[str, object]:
    """Return a deterministic fixed-redaction copy for caller-owned metadata."""
    result: dict[str, object] = {}
    for key, child in value.items():
        if _sensitive_key(str(key)) or _contains_secret(child):
            result[str(key)] = "[REDACTED]"
        else:
            result[str(key)] = child
    return result


def canonical_json_bytes(value: object) -> bytes:
    reject_secrets(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=False,
        )
        return text.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise ProvenanceError("manifest is not canonically serializable") from None


def _relative_file(repo_root: os.PathLike[str] | str, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ProvenanceError("invalid artifact path")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative_path:
        raise ProvenanceError("artifact path escapes repository")
    root = Path(repo_root).resolve(strict=True)
    candidate = root.joinpath(*pure.parts)
    try:
        current = root
        for part in pure.parts[:-1]:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise ProvenanceError("artifact is not a contained regular file")
        file_stat = candidate.lstat()
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except ProvenanceError:
        raise
    except (FileNotFoundError, OSError, ValueError):
        raise ProvenanceError("artifact is not a contained regular file") from None
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise ProvenanceError("artifact is not a contained regular file")
    return resolved


def hash_file(repo_root: os.PathLike[str] | str, relative_path: str) -> str:
    path = _relative_file(repo_root, relative_path)
    digest = __import__("hashlib").sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_artifact_record(
    repo_root: os.PathLike[str] | str,
    relative_path: str,
    *,
    producer_run_id: str,
    producer: str,
    target: str,
    input_hashes: Mapping[str, str],
    created_at: str | None = None,
) -> dict[str, object]:
    record = {
        "path": relative_path,
        "sha256": hash_file(repo_root, relative_path),
        "producer_run_id": producer_run_id,
        "producer": producer,
        "target": target,
        "input_hashes": validate_input_hashes(input_hashes),
        "created_at": created_at or utc_now(),
    }
    validate_artifact_record(record, repo_root)
    return record


def validate_artifact_record(
    value: object, repo_root: os.PathLike[str] | str, *, verify_hash: bool = True
) -> dict[str, object]:
    if not isinstance(value, dict) or tuple(value) != _ARTIFACT_KEYS:
        raise ProvenanceError("invalid artifact record")
    reject_secrets(value)
    for name in ("producer_run_id", "producer", "target"):
        if not isinstance(value[name], str) or not value[name]:
            raise ProvenanceError("invalid artifact record")
    if not isinstance(value["sha256"], str) or not _SHA256.fullmatch(value["sha256"]):
        raise ProvenanceError("invalid artifact record")
    validate_timestamp(value["created_at"])
    hashes = validate_input_hashes(value["input_hashes"])
    _relative_file(repo_root, value["path"])
    if verify_hash and hash_file(repo_root, value["path"]) != value["sha256"]:
        raise ProvenanceError("artifact hash mismatch")
    return {
        "path": value["path"],
        "sha256": value["sha256"],
        "producer_run_id": value["producer_run_id"],
        "producer": value["producer"],
        "target": value["target"],
        "input_hashes": hashes,
        "created_at": value["created_at"],
    }


def build_manifest(
    runs: Sequence[Mapping[str, object]],
    artifacts: Sequence[Mapping[str, object]],
    repo_root: os.PathLike[str] | str,
) -> bytes:
    normalized_runs: list[dict[str, object]] = []
    known_runs: dict[str, tuple[str, str]] = {}
    for run in runs:
        if tuple(run) != ("run_id", "producer", "target", "commands"):
            raise ProvenanceError("invalid run record")
        run_id, producer, target = run["run_id"], run["producer"], run["target"]
        if not all(isinstance(item, str) and item for item in (run_id, producer, target)):
            raise ProvenanceError("invalid run record")
        commands = run["commands"]
        if not isinstance(commands, list):
            raise ProvenanceError("invalid run record")
        normalized_commands = [validate_command_record(command) for command in commands]
        for command in normalized_commands:
            if (command["run_id"], command["producer"], command["target"]) != (
                run_id,
                producer,
                target,
            ):
                raise ProvenanceError("command binding mismatch")
        if run_id in known_runs:
            raise ProvenanceError("duplicate run id")
        known_runs[run_id] = (producer, target)
        normalized_runs.append(
            {"run_id": run_id, "producer": producer, "target": target, "commands": normalized_commands}
        )
    normalized_artifacts = [validate_artifact_record(item, repo_root) for item in artifacts]
    for artifact in normalized_artifacts:
        binding = known_runs.get(artifact["producer_run_id"])
        if binding != (artifact["producer"], artifact["target"]):
            raise ProvenanceError("artifact binding mismatch")
    return canonical_json_bytes(
        {
            "schema_version": SCHEMA_VERSION,
            "runs": normalized_runs,
            "artifacts": normalized_artifacts,
        }
    )


def validate_manifest(
    manifest_bytes: bytes,
    repo_root: os.PathLike[str] | str,
    *,
    trusted_manifest_sha256: str,
) -> dict[str, object]:
    if not isinstance(trusted_manifest_sha256, str) or not _SHA256.fullmatch(
        trusted_manifest_sha256
    ):
        raise ProvenanceError("trusted manifest digest required")
    if sha256_bytes(manifest_bytes) != trusted_manifest_sha256:
        raise ProvenanceError("trusted manifest digest mismatch")
    parsed = strict_json_loads(manifest_bytes)
    if not isinstance(parsed, dict) or tuple(parsed) != _MANIFEST_KEYS:
        raise ProvenanceError("invalid manifest schema")
    if parsed["schema_version"] != SCHEMA_VERSION:
        raise ProvenanceError("invalid manifest schema")
    rebuilt = build_manifest(parsed["runs"], parsed["artifacts"], repo_root)
    if rebuilt != manifest_bytes:
        raise ProvenanceError("manifest is not canonical JSON")
    return parsed
