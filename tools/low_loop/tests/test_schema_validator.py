import json
import math
import os
from pathlib import Path
import tempfile
import unittest


from tools.low_loop.schema_validator import (
    KNOWN_KEYWORDS,
    SCHEMA_ROOT,
    SchemaBundle,
    SchemaCompilationError,
    canonical_json_bytes,
    sha256_bytes,
    sha256_hex,
)


class CanonicalJsonTests(unittest.TestCase):
    def test_golden_vectors_and_key_order(self):
        value = {"z": "雪", "a": [True, None, 2]}
        expected = b'{"a":[true,null,2],"z":"\xe9\x9b\xaa"}'
        self.assertEqual(canonical_json_bytes(value), expected)
        self.assertEqual(canonical_json_bytes(value), canonical_json_bytes({"a": [True, None, 2], "z": "雪"}))
        golden = "5bb6c888500955677a4fd114a7d752f2efbdcc47e6f9ce2843c247b4a6eac32f"
        self.assertEqual(sha256_hex(value), golden)
        self.assertEqual(sha256_bytes(expected), golden)
        self.assertRegex(golden, r"^[a-f0-9]{64}$")

    def test_non_finite_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_json_bytes({"bad": value})


class RepositorySchemaTests(unittest.TestCase):
    def test_all_nine_schemas_compile_and_keywords_are_recognized(self):
        bundle = SchemaBundle(SCHEMA_ROOT)
        compiled = bundle.compile_all()
        self.assertEqual(len(compiled), 9)

        seen = set()
        schema_keywords = set(KNOWN_KEYWORDS)

        def visit(node):
            if not isinstance(node, dict):
                return
            seen.update(node)
            for keyword in ("$defs", "properties"):
                for child in node.get(keyword, {}).values():
                    visit(child)
            if isinstance(node.get("additionalProperties"), dict):
                visit(node["additionalProperties"])
            if "items" in node:
                visit(node["items"])
            for child in node.get("allOf", []):
                visit(child)
            for keyword in ("if", "then"):
                if keyword in node:
                    visit(node[keyword])

        for path in compiled:
            visit(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(seen - schema_keywords, set())
        self.assertTrue({"$ref", "type", "additionalProperties", "format", "if", "then"} <= seen)

    def test_representative_task_spec_passes(self):
        sha = "a" * 64
        path_rule = {"path": "tools/low_loop/schema_validator.py", "reason": "bounded"}
        validation = {"validation_id": "v1", "assertion": "passes", "judge_id": "j1"}
        task = {
            "standard_version": "3.0.0-candidate", "schema_version": "3.0.0",
            "task_id": "V3-LCL-08", "title": "validator", "topic": "schema",
            "objective": "validate structure", "non_goals": ["execution"], "base_sha": sha,
            "dependencies": [],
            "context": {"repository_id": "repo", "worktree_id": "wt", "trust_class": "TASKSPEC", "facts": []},
            "roots": {"read_roots": ["."], "write_roots": ["tools/low_loop"], "execute_roots": ["python3"], "output_roots": ["tools/low_loop"]},
            "allowed_paths": [path_rule], "forbidden_paths": [{"path": ".git", "reason": "forbidden"}],
            "commands": [],
            "required_outputs": [{"output_id": "o1", "path": path_rule["path"], "media_type": "text/x-python", "description": "library"}],
            "validations": {"positive": [validation], "negative": [validation], "adversarial": [validation]},
            "frozen_judges": [{"judge_id": "j1", "version": "1", "sha256": sha, "frozen_at": "2026-07-11T00:00:00Z"}],
            "grant_ids": [],
            "budgets": {"max_rounds": 1, "max_attempts": 1, "max_wall_time_seconds": 60, "max_tokens": 1, "max_artifacts": 2},
            "stop_conditions": [{"condition_id": "s1", "kind": "SAFETY_BOUNDARY", "threshold": 1, "action": "STOP"}],
            "rollback": {"strategy": "none", "preconditions": [], "recovery_artifact_ids": [], "requires_grant_operation": "rollback_commit"},
            "implementation_status": "MANUAL_ORCHESTRATED_LEDGER_ONLY", "capability_ceiling": "structure_only",
        }
        self.assertEqual(SchemaBundle(SCHEMA_ROOT).validate("task-spec.schema.json", task), [])


class SyntheticValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_validation_failures_and_escaped_pointers(self):
        schema = {
            "type": "object", "additionalProperties": False,
            "required": ["need"],
            "properties": {
                "need": {"const": "yes"},
                "kind": {"enum": ["A"]},
                "count": {"type": "integer", "minimum": 2},
                "name": {"type": "string", "minLength": 2, "pattern": "^[A-Z]+$"},
                "when": {"type": "string", "format": "date-time"},
                "items": {"type": "array", "uniqueItems": True},
                "a/b~c": {"type": "string"},
            },
        }
        self.write("main.json", schema)
        instance = {"kind": "B", "count": True, "name": "x", "when": "2026-01-01T00:00:00", "items": [1, 1.0], "a/b~c": 3, "extra": 1}
        issues = SchemaBundle(self.root).validate("main.json", instance)
        codes = {issue.code for issue in issues}
        self.assertTrue({"required", "additionalProperties", "type", "enum", "minLength", "pattern", "format", "uniqueItems"} <= codes)
        pointers = {issue.instance_pointer for issue in issues}
        self.assertIn("/need", pointers)
        self.assertIn("/a~1b~0c", pointers)
        self.assertIn("/items/1", pointers)
        self.assertTrue(all(issue.schema_path and issue.message for issue in issues))

        instance["count"] = 1
        issues = SchemaBundle(self.root).validate("main.json", instance)
        self.assertTrue(any(issue.code == "minimum" and issue.instance_pointer == "/count" for issue in issues))

    def test_integer_accepts_integral_json_numbers_only(self):
        self.write("main.json", {"type": "integer"})
        bundle = SchemaBundle(self.root)

        for value in (1, 1.0, -0.0):
            with self.subTest(accepted=value):
                self.assertEqual(bundle.validate("main.json", value), [])
        for value in (True, False, 1.5, -2.25):
            with self.subTest(rejected=value):
                issues = bundle.validate("main.json", value)
                self.assertEqual([issue.code for issue in issues], ["type"])

    def test_internal_sibling_refs_and_conditional(self):
        self.write("defs.json", {"$defs": {"word": {"type": "string", "minLength": 1}}})
        self.write("main.json", {
            "type": "object", "additionalProperties": False,
            "required": ["local", "sibling", "mode", "flag"],
            "properties": {
                "local": {"$ref": "#/$defs/n"},
                "sibling": {"$ref": "defs.json#/$defs/word"},
                "mode": {"enum": ["review", "normal"]}, "flag": {"type": "boolean"},
            },
            "allOf": [{"if": {"properties": {"mode": {"const": "review"}}, "required": ["mode"]}, "then": {"properties": {"flag": {"const": True}}}}],
            "$defs": {"n": {"type": "integer", "minimum": 1}},
        })
        bundle = SchemaBundle(self.root)
        self.assertEqual(bundle.validate("main.json", {"local": 1, "sibling": "x", "mode": "normal", "flag": False}), [])
        issues = bundle.validate("main.json", {"local": 1, "sibling": "x", "mode": "review", "flag": False})
        self.assertTrue(any(issue.code == "const" and issue.instance_pointer == "/flag" for issue in issues))

    def test_fail_closed_refs_keywords_ids_and_cycles(self):
        cases = {
            "unknown": {"mystery": 1},
            "remote": {"$ref": "https://example.test/schema.json"},
            "absolute": {"$ref": "/tmp/schema.json"},
            "traversal": {"$ref": "../schema.json"},
            "missing": {"$ref": "missing.json"},
            "malformed": {"$ref": "#/$defs"},
        }
        for label, schema in cases.items():
            with self.subTest(label=label):
                case_root = self.root / label
                case_root.mkdir()
                (case_root / "main.json").write_text(json.dumps(schema), encoding="utf-8")
                with self.assertRaises(SchemaCompilationError):
                    SchemaBundle(case_root).compile_all()

        duplicate_root = self.root / "duplicate"
        duplicate_root.mkdir()
        for name in ("a.json", "b.json"):
            (duplicate_root / name).write_text(json.dumps({"$id": "same"}), encoding="utf-8")
        with self.assertRaises(SchemaCompilationError):
            SchemaBundle(duplicate_root).compile_all()

        cycle_root = self.root / "cycle"
        cycle_root.mkdir()
        (cycle_root / "a.json").write_text(json.dumps({"$ref": "b.json"}), encoding="utf-8")
        (cycle_root / "b.json").write_text(json.dumps({"$ref": "a.json"}), encoding="utf-8")
        with self.assertRaises(SchemaCompilationError):
            SchemaBundle(cycle_root).compile_all()

    def test_failed_compilation_is_not_cached(self):
        self.write("main.json", {"$id": "main", "mystery": 1})

        for method_name in ("compile", "compile_all"):
            bundle = SchemaBundle(self.root)
            for attempt in (1, 2):
                with self.subTest(method=method_name, attempt=attempt), self.assertRaisesRegex(
                    SchemaCompilationError, "unknown schema keyword"
                ):
                    if method_name == "compile":
                        bundle.compile("main.json")
                    else:
                        bundle.compile_all()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_symlink_escape_rejected(self):
        outside = self.root.parent / (self.root.name + "-outside.json")
        outside.write_text("{}", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        os.symlink(outside, self.root / "escape.json")
        self.write("main.json", {"$ref": "escape.json"})
        with self.assertRaises(SchemaCompilationError):
            SchemaBundle(self.root).compile_all()


if __name__ == "__main__":
    unittest.main()
