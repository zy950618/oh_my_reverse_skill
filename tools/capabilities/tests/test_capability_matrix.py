from __future__ import annotations

import fnmatch
import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "capability_matrix.py"
SPEC = importlib.util.spec_from_file_location("capability_matrix", MODULE_PATH)
matrix = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(matrix)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CapabilityMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "tools/tests").mkdir(parents=True)
        (self.root / "docs").mkdir()
        self.producer = self.root / "tools/run.py"
        self.producer.write_text("def main():\n    return 0\n", encoding="utf-8")
        self.test_file = self.root / "tools/tests/test_run.py"
        self.test_file.write_text("def test_main():\n    assert True\n", encoding="utf-8")
        self.doc = self.root / "docs/README.md"
        self.doc.write_text("# Commands\n\n```bash\npython3 tools/run.py --help\n```\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def evidence(self, kind: str, path: str, symbol: str, claim: str = "bound evidence") -> dict:
        target = self.root / path
        return {"kind": kind, "path": path, "sha256": digest(target), "symbol_or_command": symbol, "claim": claim}

    def schema(self, evidence: list[dict] | None = None) -> dict:
        return {
            "schema_version": 1,
            "allowed_capability_ids": ["cap"],
            "catalog": [{"id": "cap", "title": "Capability", "evidence": evidence or []}],
            "legacy_entries": [],
        }

    def test_independent_axes_and_missing_producer_or_test_downgrade(self) -> None:
        evidence = [
            self.evidence("producer", "tools/run.py", "main"),
            self.evidence("documentation", "docs/README.md", "Generate and validate"),
        ]
        records, findings = matrix.validate_catalog(self.schema(evidence), self.root)
        graded = matrix.grade_capability(records[0])
        self.assertFalse(findings)
        self.assertEqual({"I": True, "T": False, "D": True, "E": False, "U": True}, graded["axes"])
        self.assertEqual("I-only", graded["display_grade"])
        self.assertEqual("IMPLEMENTED_UNPROVEN", graded["integration_status"])

    def test_external_only_never_sets_implementation_or_tests(self) -> None:
        external = {"kind": "external_dependency", "path": "example-tool", "sha256": None,
                    "symbol_or_command": "source=https://example.invalid version=1.2.3", "claim": "external only"}
        records, _ = matrix.validate_catalog(self.schema([external]), self.root)
        graded = matrix.grade_capability(records[0])
        self.assertEqual({"I": False, "T": False, "D": False, "E": True, "U": True}, graded["axes"])
        self.assertEqual("D/E-only", graded["display_grade"])

    def test_bound_test_sets_only_test_axis(self) -> None:
        records, _ = matrix.validate_catalog(self.schema([self.evidence("test", "tools/tests/test_run.py", "test_main")]), self.root)
        self.assertEqual("T-only", matrix.grade_capability(records[0])["display_grade"])

    def test_producer_and_test_symbols_are_bound_to_hashed_file(self) -> None:
        evidence = [
            self.evidence("producer", "tools/run.py", "missing_main"),
            self.evidence("test", "tools/tests/test_run.py", "MissingTests"),
        ]
        records, findings = matrix.validate_catalog(self.schema(evidence), self.root)
        self.assertEqual([], records[0]["evidence"]["producer"])
        self.assertEqual([], records[0]["evidence"]["test"])
        self.assertEqual({"evidence_binding_missing"}, {item["code"] for item in findings})
        self.assertTrue(all(item["hard"] for item in findings))

    def test_consumer_command_must_exist_in_hashed_caller(self) -> None:
        workflow = self.root / "caller.yml"
        workflow.write_text("run: python3 tools/run.py --mode strict\n", encoding="utf-8")
        valid = self.evidence("consumer", "caller.yml", "python3 tools/run.py --mode strict")
        invalid = self.evidence("consumer", "caller.yml", "python3 tools/other.py")
        records, findings = matrix.validate_catalog(self.schema([valid, invalid]), self.root)
        self.assertEqual([valid], records[0]["evidence"]["consumer"])
        self.assertEqual(["evidence_binding_missing"], [item["code"] for item in findings])

    def test_external_dependency_requires_source_and_version_or_unlocked(self) -> None:
        missing_version = {"kind": "external_dependency", "path": "tool", "sha256": None,
                           "symbol_or_command": "source=https://example.invalid", "claim": "external"}
        missing_source = {"kind": "external_dependency", "path": "tool", "sha256": None,
                          "symbol_or_command": "version=1.0", "claim": "external"}
        records, findings = matrix.validate_catalog(self.schema([missing_version, missing_source]), self.root)
        self.assertEqual([], records[0]["evidence"]["external_dependency"])
        self.assertEqual(2, len(findings))

    def test_stale_and_missing_hash_fail_closed(self) -> None:
        stale = self.evidence("producer", "tools/run.py", "main")
        stale["sha256"] = "0" * 64
        missing_hash = self.evidence("test", "tools/tests/test_run.py", "test_main")
        missing_hash["sha256"] = None
        records, findings = matrix.validate_catalog(self.schema([stale, missing_hash]), self.root)
        self.assertEqual([], records[0]["evidence"]["producer"])
        self.assertEqual({"evidence_hash_missing", "evidence_hash_stale"}, {item["code"] for item in findings})
        self.assertTrue(matrix.grade_capability(records[0])["axes"]["U"])

    def test_dangling_path_and_directory_are_hard(self) -> None:
        missing = {"kind": "producer", "path": "tools/missing.py", "sha256": "0" * 64,
                   "symbol_or_command": "main", "claim": "missing"}
        directory = {"kind": "producer", "path": "tools", "sha256": "0" * 64,
                     "symbol_or_command": "main", "claim": "directory"}
        _, findings = matrix.validate_catalog(self.schema([missing, directory]), self.root)
        self.assertEqual({"evidence_missing", "evidence_directory"}, {item["code"] for item in findings})
        self.assertTrue(all(item["hard"] for item in findings))

    def test_path_escape_and_symlink_escape(self) -> None:
        escaped = {"kind": "producer", "path": "../escape.py", "sha256": "0" * 64,
                   "symbol_or_command": "main", "claim": "escape"}
        outside = Path(self.temp.name).parent / "outside-matrix.py"
        outside.write_text("pass\n", encoding="utf-8")
        link = self.root / "tools/link.py"
        try:
            link.symlink_to(outside)
            linked = {"kind": "producer", "path": "tools/link.py", "sha256": digest(outside),
                      "symbol_or_command": "main", "claim": "link escape"}
            _, findings = matrix.validate_catalog(self.schema([escaped, linked]), self.root)
            self.assertEqual({"evidence_path_escape", "evidence_symlink_escape"}, {item["code"] for item in findings})
        finally:
            outside.unlink(missing_ok=True)

    def test_unknown_and_duplicate_catalog_ids_are_rejected(self) -> None:
        unknown = self.schema()
        unknown["catalog"][0]["id"] = "unknown"
        with self.assertRaises(matrix.MatrixError):
            matrix.validate_catalog(unknown, self.root)
        duplicate = self.schema()
        duplicate["catalog"].append(dict(duplicate["catalog"][0]))
        with self.assertRaises(matrix.MatrixError):
            matrix.validate_catalog(duplicate, self.root)

    def test_malformed_and_duplicate_evidence(self) -> None:
        item = self.evidence("producer", "tools/run.py", "main")
        records, findings = matrix.validate_catalog(self.schema([item, dict(item), {"kind": "producer"}]), self.root)
        self.assertEqual(1, len(records[0]["evidence"]["producer"]))
        self.assertEqual({"duplicate_evidence", "malformed_evidence"}, {entry["code"] for entry in findings})

    def test_placeholder_is_documentation_but_real_missing_command_fails(self) -> None:
        self.doc.write_text(
            "# Usage\n```bash\npython3 tools/<script>.py --out ${OUT}\npython3 tools/missing.py --run\npython3 tools/run.py --help\n```\n",
            encoding="utf-8",
        )
        commands, findings = matrix.scan_document_commands(self.root, [self.doc])
        self.assertEqual([False, True, False], [item["executable"] for item in commands])
        self.assertEqual(["missing_command"], [item["code"] for item in findings])

    def test_bare_repository_script_command_is_scanned(self) -> None:
        self.doc.write_text("# Usage\n```bash\ntools/run.py --mode strict\ntools/missing.py --run\n```\n", encoding="utf-8")
        commands, findings = matrix.scan_document_commands(self.root, [self.doc])
        self.assertEqual([True, True], [item["executable"] for item in commands])
        self.assertEqual(["missing_command"], [item["code"] for item in findings])

    def test_document_path_with_script_suffix_is_not_a_command_without_script_root(self) -> None:
        self.doc.write_text("# Usage\n```\nintermediate/modules/module_0.js\n```\n", encoding="utf-8")
        commands, findings = matrix.scan_document_commands(self.root, [self.doc])
        self.assertFalse(commands[0]["executable"])
        self.assertFalse(findings)

    def test_workflow_heredoc_body_is_not_scanned_as_commands(self) -> None:
        workflow = self.root / ".github/workflows/workflow.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "jobs:\n  gate:\n    steps:\n      - name: heredoc\n        run: |\n"
            "          python3 - <<'PY'\n"
            "            import json\n"
            "            print(json.dumps({}))\n"
            "          PY\n"
            "          python3 tools/run.py\n",
            encoding="utf-8",
        )
        commands, findings = matrix.scan_document_commands(self.root, [workflow])
        self.assertEqual([["python3", "-", "<<PY"], ["python3", "tools/run.py"]], [item["argv"] for item in commands])
        self.assertFalse(findings)

    def test_discovered_wrapper_requires_disposition(self) -> None:
        wrapper = self.root / "tools/old.py"
        wrapper.write_text("import runpy\nrunpy.run_path('tools/run.py')\n", encoding="utf-8")
        entries, findings = matrix.validate_legacy(self.schema(), self.root)
        self.assertEqual([], entries)
        self.assertIn("missing_legacy_disposition", {item["code"] for item in findings})

    def test_declared_wrapper_can_close_mechanical_discovery(self) -> None:
        wrapper = self.root / "tools/old.py"
        wrapper.write_text("import runpy\nrunpy.run_path('tools/run.py')\n", encoding="utf-8")
        schema = self.schema()
        schema["legacy_entries"] = [{"path": "tools/old.py", "target": "tools/run.py", "disposition": "compatible_wrapper"}]
        entries, findings = matrix.validate_legacy(schema, self.root)
        self.assertEqual([{"disposition": "compatible_wrapper", "path": "tools/old.py", "target": "tools/run.py"}], entries)
        self.assertFalse(findings)

    def test_discovered_wrappers_detect_duplicate_authority(self) -> None:
        for name in ("old_a.py", "old_b.py"):
            (self.root / "tools" / name).write_text("import runpy\nrunpy.run_path('tools/run.py')\n", encoding="utf-8")
        _, findings = matrix.validate_legacy(self.schema(), self.root)
        self.assertIn("duplicate_authority", {item["code"] for item in findings})

    def test_declared_wrapper_must_match_mechanical_target(self) -> None:
        (self.root / "tools/old.py").write_text("import runpy\nrunpy.run_path('tools/run.py')\n", encoding="utf-8")
        (self.root / "tools/other.py").write_text("def main():\n    return 1\n", encoding="utf-8")
        schema = self.schema()
        schema["legacy_entries"] = [{"path": "tools/old.py", "target": "tools/other.py", "disposition": "compatible_wrapper"}]
        _, findings = matrix.validate_legacy(schema, self.root)
        self.assertIn("wrapper_target_mismatch", {item["code"] for item in findings})

    def test_normal_script_is_not_discovered_as_wrapper(self) -> None:
        script = self.root / "tools/normal.py"
        script.write_text("import runpy\ndef main():\n    return runpy.run_path('tools/run.py')\n", encoding="utf-8")
        self.assertEqual([], matrix.discover_wrappers(self.root))


    def test_multiline_command_preserves_argv_and_resolves_target(self) -> None:
        self.doc.write_text("# Usage\n```bash\npython3 tools/run.py \\\n  --mode strict \\\n  --output result.json\n```\n", encoding="utf-8")
        commands, findings = matrix.scan_document_commands(self.root, [self.doc])
        self.assertFalse(findings)
        self.assertEqual(["python3", "tools/run.py", "--mode", "strict", "--output", "result.json"], commands[0]["argv"])

    def test_multiline_workflow_command_preserves_argv(self) -> None:
        workflow = self.root / ".github/workflows/workflow.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "jobs:\n  gate:\n    steps:\n      - name: gate\n        run: |\n"
            "          python3 tools/run.py \\\n"
            "            --mode strict \\\n"
            "            --output result.json\n",
            encoding="utf-8",
        )
        commands, findings = matrix.scan_document_commands(self.root, [workflow])
        self.assertFalse(findings)
        self.assertEqual(["python3", "tools/run.py", "--mode", "strict", "--output", "result.json"], commands[0]["argv"])

    def test_wrapper_target_error_duplicate_authority_and_disposition(self) -> None:
        schema = self.schema()
        schema["legacy_entries"] = [
            {"path": "tools/old-a.py", "target": "tools/missing.py", "disposition": "compatible_wrapper"},
            {"path": "tools/old-b.py", "target": "tools/missing.py", "disposition": "invalid"},
        ]
        (self.root / "tools/old-a.py").write_text("pass\n", encoding="utf-8")
        _, findings = matrix.validate_legacy(schema, self.root)
        codes = {item["code"] for item in findings}
        self.assertEqual(["missing_legacy_disposition", "wrapper_target_missing"], sorted(codes & {"wrapper_target_missing", "missing_legacy_disposition"}))

    def test_duplicate_and_missing_legacy_disposition(self) -> None:
        (self.root / "tools/old.py").write_text("pass\n", encoding="utf-8")
        schema = self.schema()
        schema["legacy_entries"] = [
            {"path": "tools/old.py", "target": "tools/run.py", "disposition": "compatible_wrapper"},
            {"path": "tools/old.py", "target": "tools/run.py", "disposition": "unified_migration"},
        ]
        _, findings = matrix.validate_legacy(schema, self.root)
        self.assertIn("duplicate_legacy_disposition", {item["code"] for item in findings})

    def test_wrapper_must_reference_declared_target(self) -> None:
        (self.root / "tools/old.py").write_text("def main():\n    return 0\n", encoding="utf-8")
        schema = self.schema()
        schema["legacy_entries"] = [
            {"path": "tools/old.py", "target": "tools/run.py", "disposition": "compatible_wrapper"},
        ]
        _, findings = matrix.validate_legacy(schema, self.root)
        self.assertIn("wrapper_target_mismatch", {item["code"] for item in findings})

    def test_conflicting_legacy_dispositions_do_not_enter_normalized_report(self) -> None:
        (self.root / "tools/old.py").write_text("pass\n", encoding="utf-8")
        schema = self.schema()
        schema["legacy_entries"] = [
            {"path": "tools/old.py", "target": "tools/run.py", "disposition": "compatible_wrapper"},
            {"path": "tools/old.py", "target": "tools/run.py", "disposition": "unified_migration"},
        ]
        entries, _ = matrix.validate_legacy(schema, self.root)
        self.assertEqual([{"disposition": "compatible_wrapper", "path": "tools/old.py", "target": "tools/run.py"}], entries)

    def test_integration_status_requires_bound_consumer(self) -> None:
        workflow = self.root / "caller.yml"
        workflow.write_text("run: python3 tools/run.py\n", encoding="utf-8")
        evidence = [
            self.evidence("producer", "tools/run.py", "main"),
            self.evidence("consumer", "caller.yml", "python3 tools/run.py"),
            self.evidence("test", "tools/tests/test_run.py", "test_main"),
        ]
        records, findings = matrix.validate_catalog(self.schema(evidence), self.root)
        self.assertFalse(findings)
        self.assertEqual("INTEGRATED", matrix.grade_capability(records[0])["integration_status"])

    def test_secret_redaction(self) -> None:
        self.doc.write_text("# Usage\n```bash\npython3 tools/run.py --token=visible token=secret --api-key exposed\n```\n", encoding="utf-8")
        commands, _ = matrix.scan_document_commands(self.root, [self.doc])
        serialized = json.dumps(commands)
        self.assertNotIn("visible", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("exposed", serialized)
        self.assertIn("<redacted>", serialized)

    def test_strict_byte_stability(self) -> None:
        evidence = [self.evidence("producer", "tools/run.py", "main"), self.evidence("test", "tools/tests/test_run.py", "test_main")]
        model_a = matrix.build_model(self.schema(evidence), self.root, [self.doc])
        model_b = matrix.build_model(self.schema(evidence), self.root, [self.doc])
        self.assertEqual(matrix.render_json(model_a), matrix.render_json(model_b))
        self.assertEqual(matrix.render_markdown(model_a), matrix.render_markdown(model_b))
        self.assertTrue(matrix.render_json(model_a).endswith(b"\n"))
        self.assertFalse(matrix.render_json(model_a).endswith(b"\n\n"))

    def test_cli_emits_reports_and_nonzero_on_hard_failure(self) -> None:
        schema_path = self.root / "schema.yaml"
        schema_path.write_text(json.dumps(self.schema()), encoding="utf-8")
        code = matrix.main(["--schema", str(schema_path), "--repo-root", str(self.root)])
        self.assertEqual(0, code)
        self.assertTrue((self.root / "reports/capability-matrix.json").is_file())
        self.doc.write_text("# Usage\n```bash\npython3 tools/missing.py\n```\n", encoding="utf-8")
        code = matrix.main(["--schema", str(schema_path), "--repo-root", str(self.root)])
        self.assertEqual(1, code)
        report = json.loads((self.root / "reports/capability-matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(1, report["summary"]["hard_finding_count"])

    def test_workflow_wires_tests_generator_and_diff_gate(self) -> None:
        workflow = Path(__file__).parents[3] / ".github/workflows/capability-matrix.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("unittest discover", text)
        self.assertIn("tools/capabilities/capability_matrix.py", text)
        self.assertIn("git diff --exit-code", text)

    def test_workflow_paths_cover_all_schema_bound_executable_evidence(self) -> None:
        repo_root = Path(__file__).parents[3]
        workflow = (repo_root / ".github/workflows/capability-matrix.yml").read_text(encoding="utf-8")
        schema = json.loads((repo_root / "tools/capabilities/schema.yaml").read_text(encoding="utf-8"))
        executable_paths = {
            evidence["path"]
            for capability in schema["catalog"]
            for evidence in capability["evidence"]
            if evidence["kind"] in {"producer", "consumer", "test"}
        }

        for event in ("push", "pull_request"):
            match = re.search(
                rf"(?m)^  {event}:\n    paths:\n(?P<paths>(?:      - .*\n)+)",
                workflow,
            )
            self.assertIsNotNone(match, f"missing {event}.paths")
            patterns = [
                json.loads(line.split("-", 1)[1].strip())
                for line in match.group("paths").splitlines()
            ]
            uncovered = sorted(
                path
                for path in executable_paths
                if not any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
            )
            self.assertEqual([], uncovered, f"{event}.paths misses executable evidence")


if __name__ == "__main__":
    unittest.main()
