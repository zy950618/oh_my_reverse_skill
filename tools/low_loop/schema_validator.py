"""Small, fail-closed JSON Schema subset used by the Low-LOOP V3 schemas.

This module is a library.  It deliberately contains no process, state, Git, or
command-line integration.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


SCHEMA_ROOT = (
    Path(__file__).resolve().parents[2]
    / "1-业务流程层"
    / "web-h5-loop-engineering"
    / "schemas"
)

_ANNOTATIONS = {
    "$schema", "$id", "title", "description", "default", "examples",
    "deprecated", "readOnly", "writeOnly", "$comment",
}
_VALIDATION_KEYWORDS = {
    "$defs", "$ref", "type", "properties", "required",
    "additionalProperties", "const", "enum", "minLength", "minimum",
    "pattern", "items", "minItems", "uniqueItems", "allOf", "if", "then",
    "format",
}
KNOWN_KEYWORDS = frozenset(_ANNOTATIONS | _VALIDATION_KEYWORDS)


class SchemaCompilationError(ValueError):
    """The schema bundle is unsafe, unsupported, or malformed."""


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    schema_path: str
    instance_pointer: str


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON, rejecting non-finite numbers."""

    _assert_json_value(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def _assert_json_value(value: Any) -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if _is_number(value):
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            _assert_json_value(item)
        return
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def sha256_hex(value: Any) -> str:
    """Return the lowercase SHA-256 of a value's canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 of bytes."""

    return hashlib.sha256(data).hexdigest()


def _pointer_token(value: Any) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _pointer(parts: Iterable[Any]) -> str:
    return "".join("/" + _pointer_token(part) for part in parts)


def _schema_location(document: Path, parts: tuple[Any, ...]) -> str:
    return document.name + "#" + _pointer(parts)


def _is_integer(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or (math.isfinite(value) and value.is_integer()))
    )


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
    )


class SchemaBundle:
    """Compile and validate a local bundle containing the supported subset."""

    def __init__(self, root: str | Path = SCHEMA_ROOT):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise SchemaCompilationError(f"schema root is not a directory: {root}")
        self._documents: dict[Path, Any] = {}
        self._ids: dict[str, str] = {}
        self._compiled: set[Path] = set()

    def compile_all(self) -> tuple[Path, ...]:
        paths = sorted(self.root.glob("*.json"), key=lambda path: path.name)
        if not paths:
            raise SchemaCompilationError("schema bundle contains no .json files")
        for path in paths:
            self._load(path)
        for path in tuple(sorted(self._documents, key=lambda item: item.name)):
            self._compile_document(path)
        self._reject_ref_cycles()
        return tuple(sorted(self._documents, key=lambda item: item.name))

    def compile(self, schema: str | Path) -> Path:
        path = self._resolve_entry(schema)
        self._load(path)
        self._compile_document(path)
        self._reject_ref_cycles()
        return path

    def validate(self, schema: str | Path, instance: Any) -> list[ValidationIssue]:
        path = self.compile(schema)
        issues: list[ValidationIssue] = []
        self._validate_node(self._documents[path], path, (), instance, (), issues)
        return issues

    def _resolve_entry(self, schema: str | Path) -> Path:
        candidate = Path(schema)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            if candidate.parent != Path(".") or candidate.suffix != ".json":
                raise SchemaCompilationError(f"entry must be a sibling .json name: {schema}")
            resolved = (self.root / candidate).resolve()
        self._require_inside_root(resolved)
        if not resolved.is_file():
            raise SchemaCompilationError(f"missing schema: {schema}")
        return resolved

    def _require_inside_root(self, path: Path) -> None:
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise SchemaCompilationError(f"schema path escapes root: {path}") from exc

    def _load(self, path: Path) -> Any:
        resolved = path.resolve()
        self._require_inside_root(resolved)
        if not resolved.is_file():
            raise SchemaCompilationError(f"missing schema target: {path.name}")
        if resolved in self._documents:
            return self._documents[resolved]
        try:
            with resolved.open("r", encoding="utf-8") as handle:
                document = json.load(
                    handle,
                    parse_constant=lambda value: (_ for _ in ()).throw(
                        ValueError(f"non-finite number {value}")
                    ),
                )
        except (OSError, UnicodeError, ValueError) as exc:
            raise SchemaCompilationError(f"cannot load schema {path.name}: {exc}") from exc
        if not isinstance(document, dict):
            raise SchemaCompilationError(f"schema document must be an object: {path.name}")
        self._documents[resolved] = document
        return document

    def _compile_document(self, path: Path) -> None:
        if path in self._compiled:
            return
        compiled_before = self._compiled.copy()
        ids_before = self._ids.copy()
        self._compiled.add(path)
        try:
            self._compile_node(self._documents[path], path, ())
        except Exception:
            self._compiled = compiled_before
            self._ids = ids_before
            raise

    def _compile_node(self, node: Any, document: Path, parts: tuple[Any, ...]) -> None:
        if not isinstance(node, dict):
            raise SchemaCompilationError(
                f"schema must be an object at {_schema_location(document, parts)}"
            )
        unknown = sorted(set(node) - KNOWN_KEYWORDS)
        if unknown:
            raise SchemaCompilationError(
                f"unknown schema keyword {unknown[0]!r} at "
                f"{_schema_location(document, parts)}"
            )
        schema_id = node.get("$id")
        if schema_id is not None:
            if not isinstance(schema_id, str) or not schema_id:
                raise SchemaCompilationError("$id must be a non-empty string")
            location = _schema_location(document, parts)
            previous = self._ids.get(schema_id)
            if previous is not None and previous != location:
                raise SchemaCompilationError(f"duplicate schema $id: {schema_id}")
            self._ids[schema_id] = location

        self._check_keyword_shapes(node, document, parts)
        if "$ref" in node:
            self._resolve_ref(document, node["$ref"])
        for keyword in ("$defs", "properties"):
            for name, child in node.get(keyword, {}).items():
                self._compile_node(child, document, parts + (keyword, name))
        if isinstance(node.get("additionalProperties"), dict):
            self._compile_node(
                node["additionalProperties"], document, parts + ("additionalProperties",)
            )
        if "items" in node:
            self._compile_node(node["items"], document, parts + ("items",))
        for keyword in ("allOf",):
            for index, child in enumerate(node.get(keyword, [])):
                self._compile_node(child, document, parts + (keyword, index))
        for keyword in ("if", "then"):
            if keyword in node:
                self._compile_node(node[keyword], document, parts + (keyword,))

    def _check_keyword_shapes(
        self, node: dict[str, Any], document: Path, parts: tuple[Any, ...]
    ) -> None:
        where = _schema_location(document, parts)
        mappings = ("$defs", "properties")
        for keyword in mappings:
            if keyword in node and not isinstance(node[keyword], dict):
                raise SchemaCompilationError(f"{keyword} must be an object at {where}")
        if "$ref" in node and not isinstance(node["$ref"], str):
            raise SchemaCompilationError(f"$ref must be a string at {where}")
        if "type" in node:
            value = node["type"]
            types = value if isinstance(value, list) else [value]
            allowed = {"null", "boolean", "object", "array", "number", "integer", "string"}
            if not types or any(not isinstance(item, str) or item not in allowed for item in types):
                raise SchemaCompilationError(f"unsupported type at {where}")
        for keyword in ("required", "allOf"):
            if keyword in node and not isinstance(node[keyword], list):
                raise SchemaCompilationError(f"{keyword} must be an array at {where}")
        if "required" in node and any(not isinstance(item, str) for item in node["required"]):
            raise SchemaCompilationError(f"required entries must be strings at {where}")
        additional = node.get("additionalProperties", False)
        if "additionalProperties" in node and not (
            additional is False or isinstance(additional, dict)
        ):
            raise SchemaCompilationError(f"additionalProperties must be false or a schema at {where}")
        for keyword in ("minLength", "minItems"):
            if keyword in node and (not _is_integer(node[keyword]) or node[keyword] < 0):
                raise SchemaCompilationError(f"{keyword} must be a non-negative integer at {where}")
        if "minimum" in node and not _is_number(node["minimum"]):
            raise SchemaCompilationError(f"minimum must be a finite number at {where}")
        if "pattern" in node:
            if not isinstance(node["pattern"], str):
                raise SchemaCompilationError(f"pattern must be a string at {where}")
            try:
                re.compile(node["pattern"])
            except re.error as exc:
                raise SchemaCompilationError(f"invalid pattern at {where}: {exc}") from exc
        if "uniqueItems" in node and not isinstance(node["uniqueItems"], bool):
            raise SchemaCompilationError(f"uniqueItems must be boolean at {where}")
        if "format" in node and node["format"] != "date-time":
            raise SchemaCompilationError(f"unsupported format at {where}")
        if "enum" in node and not isinstance(node["enum"], list):
            raise SchemaCompilationError(f"enum must be an array at {where}")

    def _resolve_ref(self, document: Path, ref: str) -> tuple[Path, tuple[str, ...], Any]:
        split = urlsplit(ref)
        if split.scheme or split.netloc or split.query:
            raise SchemaCompilationError(f"remote or qualified $ref rejected: {ref}")
        raw_path, marker, fragment = ref.partition("#")
        if marker and "#" in fragment:
            raise SchemaCompilationError(f"malformed $ref fragment: {ref}")
        if raw_path:
            candidate = Path(raw_path)
            if candidate.is_absolute():
                raise SchemaCompilationError(f"absolute $ref rejected: {ref}")
            if candidate.parent != Path(".") or candidate.suffix != ".json":
                raise SchemaCompilationError(f"non-sibling or non-json $ref rejected: {ref}")
            target_document = (document.parent / candidate).resolve()
            self._require_inside_root(target_document)
        else:
            target_document = document
        target = self._load(target_document)
        self._compile_document(target_document)
        tokens: tuple[str, ...] = ()
        if marker:
            if not fragment.startswith("/$defs/"):
                raise SchemaCompilationError(f"malformed $ref fragment: {ref}")
            encoded = fragment[1:].split("/")
            decoded: list[str] = []
            for token in encoded:
                if re.search(r"~(?![01])", token):
                    raise SchemaCompilationError(f"malformed $ref fragment: {ref}")
                decoded.append(token.replace("~1", "/").replace("~0", "~"))
            tokens = tuple(decoded)
            for token in tokens:
                if not isinstance(target, dict) or token not in target:
                    raise SchemaCompilationError(f"missing $ref target: {ref}")
                target = target[token]
        elif not raw_path:
            raise SchemaCompilationError(f"empty $ref rejected: {ref}")
        if not isinstance(target, dict):
            raise SchemaCompilationError(f"$ref target is not a schema: {ref}")
        return target_document, tokens, target

    def _ref_edges(self) -> dict[tuple[Path, tuple[Any, ...]], set[tuple[Path, tuple[Any, ...]]]]:
        edges: dict[tuple[Path, tuple[Any, ...]], set[tuple[Path, tuple[Any, ...]]]] = {}

        def visit(node: dict[str, Any], document: Path, parts: tuple[Any, ...]) -> None:
            key = (document, parts)
            edges.setdefault(key, set())
            if "$ref" in node:
                target_document, tokens, _ = self._resolve_ref(document, node["$ref"])
                edges[key].add((target_document, tokens))
            for keyword in ("$defs", "properties"):
                for name, child in node.get(keyword, {}).items():
                    visit(child, document, parts + (keyword, name))
            if isinstance(node.get("additionalProperties"), dict):
                visit(node["additionalProperties"], document, parts + ("additionalProperties",))
            if "items" in node:
                visit(node["items"], document, parts + ("items",))
            for index, child in enumerate(node.get("allOf", [])):
                visit(child, document, parts + ("allOf", index))
            for keyword in ("if", "then"):
                if keyword in node:
                    visit(node[keyword], document, parts + (keyword,))

        for document in sorted(self._documents, key=lambda item: item.name):
            visit(self._documents[document], document, ())
        return edges

    def _reject_ref_cycles(self) -> None:
        edges = self._ref_edges()
        active: set[tuple[Path, tuple[Any, ...]]] = set()
        done: set[tuple[Path, tuple[Any, ...]]] = set()

        def walk(node: tuple[Path, tuple[Any, ...]]) -> None:
            if node in active:
                raise SchemaCompilationError("$ref cycle detected")
            if node in done:
                return
            active.add(node)
            for target in edges.get(node, ()):
                walk(target)
            active.remove(node)
            done.add(node)

        for node in sorted(edges, key=lambda item: (item[0].name, repr(item[1]))):
            walk(node)

    def _validate_node(
        self,
        node: dict[str, Any],
        document: Path,
        schema_parts: tuple[Any, ...],
        instance: Any,
        instance_parts: tuple[Any, ...],
        issues: list[ValidationIssue],
    ) -> None:
        if "$ref" in node:
            target_document, tokens, target = self._resolve_ref(document, node["$ref"])
            self._validate_node(target, target_document, tokens, instance, instance_parts, issues)

        expected = node.get("type")
        if expected is not None:
            types = expected if isinstance(expected, list) else [expected]
            if not any(self._matches_type(instance, kind) for kind in types):
                self._issue(issues, "type", f"expected type {expected!r}", document,
                            schema_parts + ("type",), instance_parts)
                return

        if "const" in node and not self._json_equal(instance, node["const"]):
            self._issue(issues, "const", "value does not equal const", document,
                        schema_parts + ("const",), instance_parts)
        if "enum" in node and not any(self._json_equal(instance, item) for item in node["enum"]):
            self._issue(issues, "enum", "value is not in enum", document,
                        schema_parts + ("enum",), instance_parts)
        if isinstance(instance, str):
            if len(instance) < node.get("minLength", 0):
                self._issue(issues, "minLength", "string is too short", document,
                            schema_parts + ("minLength",), instance_parts)
            if "pattern" in node and re.search(node["pattern"], instance) is None:
                self._issue(issues, "pattern", "string does not match pattern", document,
                            schema_parts + ("pattern",), instance_parts)
            if node.get("format") == "date-time" and not self._valid_datetime(instance):
                self._issue(issues, "format", "string is not a date-time with timezone", document,
                            schema_parts + ("format",), instance_parts)
        if _is_number(instance) and "minimum" in node and instance < node["minimum"]:
            self._issue(issues, "minimum", "number is below minimum", document,
                        schema_parts + ("minimum",), instance_parts)
        if isinstance(instance, dict):
            required = node.get("required", [])
            for name in required:
                if name not in instance:
                    self._issue(issues, "required", f"missing required property {name!r}",
                                document, schema_parts + ("required",), instance_parts + (name,))
            properties = node.get("properties", {})
            for name in sorted(instance):
                if name in properties:
                    self._validate_node(properties[name], document,
                                        schema_parts + ("properties", name), instance[name],
                                        instance_parts + (name,), issues)
                elif node.get("additionalProperties") is False:
                    self._issue(issues, "additionalProperties",
                                f"unexpected property {name!r}", document,
                                schema_parts + ("additionalProperties",), instance_parts + (name,))
                elif isinstance(node.get("additionalProperties"), dict):
                    self._validate_node(node["additionalProperties"], document,
                                        schema_parts + ("additionalProperties",), instance[name],
                                        instance_parts + (name,), issues)
        if isinstance(instance, list):
            if len(instance) < node.get("minItems", 0):
                self._issue(issues, "minItems", "array has too few items", document,
                            schema_parts + ("minItems",), instance_parts)
            if node.get("uniqueItems"):
                for right in range(len(instance)):
                    if any(self._json_equal(instance[left], instance[right]) for left in range(right)):
                        self._issue(issues, "uniqueItems", "array items are not unique", document,
                                    schema_parts + ("uniqueItems",), instance_parts + (right,))
                        break
            if "items" in node:
                for index, item in enumerate(instance):
                    self._validate_node(node["items"], document, schema_parts + ("items",),
                                        item, instance_parts + (index,), issues)
        for index, subschema in enumerate(node.get("allOf", [])):
            self._validate_node(subschema, document, schema_parts + ("allOf", index),
                                instance, instance_parts, issues)
        if "if" in node and "then" in node:
            probe: list[ValidationIssue] = []
            self._validate_node(node["if"], document, schema_parts + ("if",),
                                instance, instance_parts, probe)
            if not probe:
                self._validate_node(node["then"], document, schema_parts + ("then",),
                                    instance, instance_parts, issues)

    @staticmethod
    def _matches_type(value: Any, kind: str) -> bool:
        return {
            "null": value is None,
            "boolean": isinstance(value, bool),
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "number": _is_number(value),
            "integer": _is_integer(value),
            "string": isinstance(value, str),
        }[kind]

    @classmethod
    def _json_equal(cls, left: Any, right: Any) -> bool:
        if isinstance(left, bool) or isinstance(right, bool):
            return type(left) is type(right) and left == right
        if _is_number(left) and _is_number(right):
            return left == right
        if isinstance(left, dict) and isinstance(right, dict):
            return left.keys() == right.keys() and all(
                cls._json_equal(left[key], right[key]) for key in left
            )
        if isinstance(left, list) and isinstance(right, list):
            return len(left) == len(right) and all(
                cls._json_equal(a, b) for a, b in zip(left, right)
            )
        return type(left) is type(right) and left == right

    @staticmethod
    def _valid_datetime(value: str) -> bool:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})", value) is None:
            return False
        try:
            parsed = _datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None and parsed.utcoffset() is not None
        except ValueError:
            return False

    @staticmethod
    def _issue(
        issues: list[ValidationIssue], code: str, message: str, document: Path,
        schema_parts: tuple[Any, ...], instance_parts: tuple[Any, ...]
    ) -> None:
        issues.append(ValidationIssue(
            code=code,
            message=message,
            schema_path=_schema_location(document, schema_parts),
            instance_pointer=_pointer(instance_parts),
        ))


def load_adopted_bundle() -> SchemaBundle:
    bundle = SchemaBundle(SCHEMA_ROOT)
    bundle.compile_all()
    return bundle
