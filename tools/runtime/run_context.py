"""Run-scoped command provenance using only the Python standard library."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence


class ProvenanceError(ValueError):
    """A provenance value is invalid."""


_RFC3339_OFFSET = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?[+-]\d{2}:\d{2}$"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_NAME = re.compile(
    r"(?i)(?:^|[-_.])(authorization|cookie|secret|token|api[-_]?key|password|passwd)(?:$|[-_.])"
)
_SENSITIVE_INLINE = re.compile(
    r"(?i)(?:authorization\s*:|cookie\s*:|bearer\s+|"
    r"(?:secret|token|api[-_]?key|password|passwd)\s*[=:])"
)
_URL_QUERY = re.compile(r"[?&]([^=&\s]+)=([^&\s]*)")


def utc_now() -> str:
    """Return a strict RFC3339 timestamp with an explicit UTC offset."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def validate_timestamp(value: object) -> str:
    if not isinstance(value, str) or not _RFC3339_OFFSET.fullmatch(value):
        raise ProvenanceError("invalid provenance timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ProvenanceError("invalid provenance timestamp") from None
    if parsed.utcoffset() is None:
        raise ProvenanceError("invalid provenance timestamp")
    return value


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise ProvenanceError("hash input must be bytes")
    return hashlib.sha256(value).hexdigest()


def _validate_identifier(name: str, value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ProvenanceError(f"invalid {name}")
    return value


def _contains_sensitive_text(value: str) -> bool:
    if _SENSITIVE_INLINE.search(value):
        return True
    for match in _URL_QUERY.finditer(value):
        if _SENSITIVE_NAME.search(match.group(1)):
            return True
    return False


def reject_sensitive_argv(argv: Sequence[str]) -> None:
    """Reject command arguments that could persist credentials.

    Errors intentionally do not include the rejected argument.
    """
    previous_sensitive_option = False
    for item in argv:
        if not isinstance(item, str) or "\x00" in item:
            raise ProvenanceError("invalid command argument")
        option_name = item.split("=", 1)[0].lstrip("-")
        if previous_sensitive_option or _SENSITIVE_NAME.search(option_name):
            raise ProvenanceError("sensitive command data rejected")
        if _contains_sensitive_text(item):
            raise ProvenanceError("sensitive command data rejected")
        previous_sensitive_option = bool(
            item.startswith("-") and _SENSITIVE_NAME.search(option_name)
        )


def validate_input_hashes(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ProvenanceError("invalid input hashes")
    result: dict[str, str] = {}
    for key, digest in value.items():
        if not isinstance(key, str) or not key or _contains_sensitive_text(key):
            raise ProvenanceError("invalid input hashes")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ProvenanceError("invalid input hashes")
        result[key] = digest
    return dict(sorted(result.items()))


@dataclass(frozen=True)
class CommandRecord:
    run_id: str
    producer: str
    target: str
    input_hashes: dict[str, str]
    argv: list[str]
    cwd: str
    start_time: str
    end_time: str
    exit_code: int
    stdout_sha256: str
    stderr_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "producer": self.producer,
            "target": self.target,
            "input_hashes": dict(self.input_hashes),
            "argv": list(self.argv),
            "cwd": self.cwd,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "exit_code": self.exit_code,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
        }


_COMMAND_KEYS = tuple(CommandRecord.__dataclass_fields__)


def validate_command_record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or tuple(value) != _COMMAND_KEYS:
        raise ProvenanceError("invalid command record")
    run_id = _validate_identifier("run_id", value["run_id"])
    producer = _validate_identifier("producer", value["producer"])
    target = _validate_identifier("target", value["target"])
    argv = value["argv"]
    if not isinstance(argv, list) or not argv:
        raise ProvenanceError("invalid command record")
    reject_sensitive_argv(argv)
    cwd = _validate_identifier("cwd", value["cwd"])
    start = validate_timestamp(value["start_time"])
    end = validate_timestamp(value["end_time"])
    if datetime.fromisoformat(end) < datetime.fromisoformat(start):
        raise ProvenanceError("invalid command time order")
    exit_code = value["exit_code"]
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ProvenanceError("invalid command record")
    for key in ("stdout_sha256", "stderr_sha256"):
        if not isinstance(value[key], str) or not _SHA256.fullmatch(value[key]):
            raise ProvenanceError("invalid command record")
    return {
        "run_id": run_id,
        "producer": producer,
        "target": target,
        "input_hashes": validate_input_hashes(value["input_hashes"]),
        "argv": list(argv),
        "cwd": cwd,
        "start_time": start,
        "end_time": end,
        "exit_code": exit_code,
        "stdout_sha256": value["stdout_sha256"],
        "stderr_sha256": value["stderr_sha256"],
    }


class RunContext:
    """Collect command records for one caller-defined run.

    This is deliberately not a command allowlist or orchestration layer.
    """

    def __init__(self, run_id: str, producer: str, target: str) -> None:
        self.run_id = _validate_identifier("run_id", run_id)
        self.producer = _validate_identifier("producer", producer)
        self.target = _validate_identifier("target", target)
        self._commands: list[CommandRecord] = []

    @property
    def commands(self) -> tuple[CommandRecord, ...]:
        return tuple(self._commands)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: os.PathLike[str] | str,
        input_hashes: Mapping[str, str],
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        args = list(argv)
        if not args:
            raise ProvenanceError("command argv must not be empty")
        reject_sensitive_argv(args)
        hashes = validate_input_hashes(input_hashes)
        cwd_path = Path(cwd).resolve(strict=True)
        if not cwd_path.is_dir():
            raise ProvenanceError("command cwd must be a directory")
        started = utc_now()
        completed = subprocess.run(
            args,
            cwd=cwd_path,
            env=None if env is None else dict(env),
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        ended = utc_now()
        record = CommandRecord(
            run_id=self.run_id,
            producer=self.producer,
            target=self.target,
            input_hashes=hashes,
            argv=args,
            cwd=str(cwd_path),
            start_time=started,
            end_time=ended,
            exit_code=completed.returncode,
            stdout_sha256=sha256_bytes(completed.stdout),
            stderr_sha256=sha256_bytes(completed.stderr),
        )
        validate_command_record(record.to_dict())
        self._commands.append(record)
        return completed

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "producer": self.producer,
            "target": self.target,
            "commands": [record.to_dict() for record in self._commands],
        }
