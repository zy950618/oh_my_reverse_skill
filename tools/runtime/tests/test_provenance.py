from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME))

from artifact_manifest import (  # noqa: E402
    build_manifest,
    canonical_json_bytes,
    create_artifact_record,
    redact_mapping,
    strict_json_loads,
    validate_artifact_record,
    validate_manifest,
)
from run_context import (  # noqa: E402
    ProvenanceError,
    RunContext,
    sha256_bytes,
    validate_timestamp,
)


FIXED_TIME = "2026-07-23T12:34:56.123456+00:00"
EMPTY_HASH = hashlib.sha256(b"").hexdigest()


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "input.bin").write_bytes(b"\x00input\xff")
        (self.root / "artifact.bin").write_bytes(b"\x00result\xff")
        self.inputs = {"input.bin": hashlib.sha256(b"\x00input\xff").hexdigest()}

    def tearDown(self):
        self.temp.cleanup()

    def run_context(self):
        return RunContext("run-001", "unit-test", "local-artifact")

    def artifact(self, context):
        return create_artifact_record(
            self.root,
            "artifact.bin",
            producer_run_id=context.run_id,
            producer=context.producer,
            target=context.target,
            input_hashes=self.inputs,
            created_at=FIXED_TIME,
        )

    def manifest(self, context):
        return build_manifest([context.to_dict()], [self.artifact(context)], self.root)

    def test_success_and_nonzero_commands_hash_raw_bytes(self):
        context = self.run_context()
        success = context.run(
            [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'\\x00ok\\xff')"],
            cwd=self.root,
            input_hashes=self.inputs,
        )
        failure = context.run(
            [sys.executable, "-c", "import sys;sys.stderr.buffer.write(b'bad');sys.exit(7)"],
            cwd=self.root,
            input_hashes=self.inputs,
        )
        self.assertEqual(success.returncode, 0)
        self.assertEqual(failure.returncode, 7)
        self.assertEqual(context.commands[0].stdout_sha256, sha256_bytes(b"\x00ok\xff"))
        self.assertEqual(context.commands[1].stderr_sha256, sha256_bytes(b"bad"))
        self.assertEqual(context.commands[1].exit_code, 7)
        self.assertEqual(context.commands[0].input_hashes, self.inputs)
        validate_timestamp(context.commands[0].start_time)
        self.assertRegex(context.commands[0].start_time, r"\+00:00$")

    def test_integration_create_and_validate_manifest(self):
        context = self.run_context()
        context.run(
            [sys.executable, "-c", "print('generated')"],
            cwd=self.root,
            input_hashes=self.inputs,
        )
        data = self.manifest(context)
        trusted = hashlib.sha256(data).hexdigest()
        parsed = validate_manifest(data, self.root, trusted_manifest_sha256=trusted)
        self.assertEqual(parsed["runs"][0]["commands"][0]["run_id"], "run-001")
        self.assertEqual(parsed["artifacts"][0]["producer"], "unit-test")

    def test_missing_input_and_invalid_timestamp_fail(self):
        context = self.run_context()
        with self.assertRaises(FileNotFoundError):
            context.run(
                [sys.executable, "-c", "pass"],
                cwd=self.root / "missing",
                input_hashes=self.inputs,
            )
        for value in ("2026-07-23T12:00:00", "2026-07-23 12:00:00+00:00", "bad"):
            with self.subTest(value=value), self.assertRaises(ProvenanceError):
                validate_timestamp(value)

    def test_artifact_tamper_fails(self):
        context = self.run_context()
        data = self.manifest(context)
        trusted = hashlib.sha256(data).hexdigest()
        (self.root / "artifact.bin").write_bytes(b"tampered")
        with self.assertRaisesRegex(ProvenanceError, "artifact hash mismatch"):
            validate_manifest(data, self.root, trusted_manifest_sha256=trusted)

    def test_trusted_digest_mismatch_fails(self):
        data = self.manifest(self.run_context())
        with self.assertRaisesRegex(ProvenanceError, "trusted manifest digest mismatch"):
            validate_manifest(data, self.root, trusted_manifest_sha256="0" * 64)

    def test_path_escape_directory_and_symlink_fail(self):
        context = self.run_context()
        cases = ["../artifact.bin", "/artifact.bin", "directory"]
        (self.root / "directory").mkdir()
        for relative in cases:
            with self.subTest(relative=relative), self.assertRaises(ProvenanceError):
                create_artifact_record(
                    self.root,
                    relative,
                    producer_run_id=context.run_id,
                    producer=context.producer,
                    target=context.target,
                    input_hashes=self.inputs,
                )
        if hasattr(os, "symlink"):
            (self.root / "link").symlink_to(self.root / "artifact.bin")
            with self.assertRaises(ProvenanceError):
                create_artifact_record(
                    self.root,
                    "link",
                    producer_run_id=context.run_id,
                    producer=context.producer,
                    target=context.target,
                    input_hashes=self.inputs,
                )

    def test_verify_hash_false_still_validates_artifact_path(self):
        context = self.run_context()
        valid = self.artifact(context)
        valid["sha256"] = "0" * 64
        self.assertEqual(
            validate_artifact_record(valid, self.root, verify_hash=False)["path"],
            "artifact.bin",
        )
        with self.assertRaisesRegex(ProvenanceError, "artifact hash mismatch"):
            validate_artifact_record(valid, self.root)

        cases = ["../artifact.bin", "/artifact.bin", "missing", "directory"]
        (self.root / "directory").mkdir()
        for relative in cases:
            invalid = dict(valid, path=relative)
            with self.subTest(relative=relative), self.assertRaises(ProvenanceError):
                validate_artifact_record(invalid, self.root, verify_hash=False)
        if hasattr(os, "symlink"):
            (self.root / "link").symlink_to(self.root / "artifact.bin")
            invalid = dict(valid, path="link")
            with self.assertRaises(ProvenanceError):
                validate_artifact_record(invalid, self.root, verify_hash=False)

    def test_intermediate_symlink_path_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        real_dir = self.root / "real-dir"
        real_dir.mkdir()
        (real_dir / "nested.bin").write_bytes(b"nested")
        (self.root / "linked-dir").symlink_to(real_dir, target_is_directory=True)
        context = self.run_context()
        record = {
            "path": "linked-dir/nested.bin",
            "sha256": hashlib.sha256(b"nested").hexdigest(),
            "producer_run_id": context.run_id,
            "producer": context.producer,
            "target": context.target,
            "input_hashes": self.inputs,
            "created_at": FIXED_TIME,
        }
        with self.assertRaises(ProvenanceError):
            create_artifact_record(
                self.root,
                record["path"],
                producer_run_id=context.run_id,
                producer=context.producer,
                target=context.target,
                input_hashes=self.inputs,
            )
        with self.assertRaises(ProvenanceError):
            validate_artifact_record(record, self.root, verify_hash=False)

        synthetic = "synthetic-credential-value"
        cases = [
            ["tool", "--token", synthetic],
            ["tool", f"--authorization=Bearer {synthetic}"],
            ["tool", f"https://invalid.local/x?api_key={synthetic}"],
            ["tool", f"https://invalid.local/x?accessToken={synthetic}"],
            ["tool", f"Cookie: sid={synthetic}"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                with self.assertRaises(ProvenanceError) as caught:
                    self.run_context().run(argv, cwd=self.root, input_hashes=self.inputs)
                self.assertNotIn(synthetic, str(caught.exception))
        with self.assertRaises(ProvenanceError) as caught:
            canonical_json_bytes({"authorization": synthetic})
        self.assertNotIn(synthetic, str(caught.exception))
        self.assertEqual(redact_mapping({"token": synthetic}), {"token": "[REDACTED]"})
        self.assertEqual(
            redact_mapping({"accessToken": synthetic}), {"accessToken": "[REDACTED]"}
        )

    def test_strict_json_rejects_malformed_duplicate_nonfinite_and_utf8(self):
        cases = [
            b'{"a":1,"a":2}',
            b'{"a":NaN}',
            b'{"a":Infinity}',
            b'{"a":',
            b'{"a":"\xff"}',
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ProvenanceError):
                strict_json_loads(data)
        with self.assertRaises(ProvenanceError):
            canonical_json_bytes({"value": "\ud800"})

    def test_deterministic_bytes_and_noncanonical_rejected(self):
        context = self.run_context()
        first = self.manifest(context)
        second = self.manifest(context)
        self.assertEqual(first, second)
        parsed = json.loads(first)
        noncanonical = json.dumps(parsed, indent=2).encode()
        trusted = hashlib.sha256(noncanonical).hexdigest()
        with self.assertRaisesRegex(ProvenanceError, "canonical"):
            validate_manifest(noncanonical, self.root, trusted_manifest_sha256=trusted)

    def test_binding_mismatch_and_missing_artifact_fail(self):
        context = self.run_context()
        artifact = self.artifact(context)
        artifact["target"] = "other-target"
        with self.assertRaisesRegex(ProvenanceError, "binding mismatch"):
            build_manifest([context.to_dict()], [artifact], self.root)
        (self.root / "artifact.bin").unlink()
        with self.assertRaises(ProvenanceError):
            self.artifact(context)

    def test_input_hashes_required_and_hash_exact_bytes(self):
        context = self.run_context()
        with self.assertRaises(ProvenanceError):
            context.run([sys.executable, "-c", "pass"], cwd=self.root, input_hashes=None)
        artifact = self.artifact(context)
        del artifact["input_hashes"]
        with self.assertRaises(ProvenanceError):
            build_manifest([context.to_dict()], [artifact], self.root)
        self.assertEqual(
            create_artifact_record(
                self.root,
                "artifact.bin",
                producer_run_id=context.run_id,
                producer=context.producer,
                target=context.target,
                input_hashes=self.inputs,
                created_at=FIXED_TIME,
            )["sha256"],
            hashlib.sha256(b"\x00result\xff").hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
