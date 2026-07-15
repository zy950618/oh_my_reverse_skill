from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAYER_DIR = REPO_ROOT / "tools" / "replayer"
sys.path.insert(0, str(REPLAYER_DIR))

import snapshot_replay


def write_request(snapshots: Path, prefix: str, content: str | None = None) -> None:
    snapshots.mkdir(parents=True, exist_ok=True)
    if content is None:
        content = json.dumps({
            "method": "GET",
            "url": f"https://example.test/{prefix}",
        })
    (snapshots / f"{prefix}.req.json").write_text(content, encoding="utf-8")


def response(status: int, error: str | None = None) -> dict:
    meta = {"body_encoding": "json"}
    if error:
        meta["error"] = error
    return {"status": status, "headers": {}, "body": {}, "_meta": meta}


class SnapshotReplayResultTests(unittest.TestCase):
    def run_cli_args(
        self,
        site_root: Path,
        argv: list[str],
    ) -> tuple[int, dict, str, str, mock.Mock]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        send = mock.Mock()
        with (
            mock.patch.object(snapshot_replay, "SITE_ROOT", site_root),
            mock.patch.object(snapshot_replay, "send_request", send),
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = snapshot_replay.main()
        raw = stdout.getvalue()
        result = json.loads(raw)
        self.assertEqual(exit_code, result["exit_code"])
        self.assertEqual(raw.count("\n"), 1)
        self.assert_invariants(result)
        return exit_code, result, raw, stderr.getvalue(), send

    def run_replay(
        self,
        site_root: Path,
        *extra_args: str,
        replies: list[dict] | None = None,
    ) -> tuple[int, dict, str, str, mock.Mock]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        send = mock.Mock(side_effect=replies or [])
        argv = [
            "snapshot_replay.py",
            "--domain",
            "example.test",
            "--target",
            "https://adapter.test",
            *extra_args,
        ]
        with (
            mock.patch.object(snapshot_replay, "SITE_ROOT", site_root),
            mock.patch.object(snapshot_replay, "send_request", send),
            mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = snapshot_replay.main()
        raw = stdout.getvalue()
        result = json.loads(raw)
        self.assertEqual(exit_code, result["exit_code"])
        self.assertEqual(raw.strip(), json.dumps(result, ensure_ascii=False, sort_keys=True))
        self.assert_invariants(result)
        return exit_code, result, raw, stderr.getvalue(), send

    def assert_invariants(self, result: dict) -> None:
        required = {
            "status",
            "exit_code",
            "total",
            "selected",
            "replayed",
            "failed",
            "expired",
            "no_data",
            "actual_artifacts",
        }
        self.assertTrue(required.issubset(result))
        self.assertGreaterEqual(result["total"], result["selected"])
        self.assertEqual(result["actual_artifacts"], sorted(result["actual_artifacts"]))
        self.assertEqual(len(result["actual_artifacts"]), result["replayed"])

        status = result["status"]
        if status not in {"NO_DATA", "REFUSED"}:
            self.assertEqual(
                result["selected"], result["replayed"] + result["failed"]
            )
        if status == "PASS":
            self.assertEqual(result["exit_code"], 0)
            self.assertGreater(result["selected"], 0)
            self.assertEqual(result["failed"], 0)
            self.assertEqual(result["replayed"], result["selected"])
            self.assertFalse(result["no_data"])
        elif status == "PARTIAL_FAILURE":
            self.assertEqual(result["exit_code"], 3)
            self.assertGreater(result["replayed"], 0)
            self.assertGreater(result["failed"], 0)
        elif status == "FAILURE":
            self.assertEqual(result["exit_code"], 3)
            self.assertEqual(result["replayed"], 0)
            self.assertEqual(result["failed"], result["selected"])
        elif status == "NO_DATA":
            self.assertEqual(result["exit_code"], 4)
            self.assertTrue(result["no_data"])
            self.assertEqual(result["selected"], 0)
            self.assertEqual(result["replayed"], 0)
            self.assertEqual(result["failed"], 0)
            self.assertEqual(result["actual_artifacts"], [])
        elif status == "REFUSED":
            self.assertEqual(result["exit_code"], 2)
            self.assertFalse(result["no_data"])
            self.assertEqual(result["actual_artifacts"], [])
        else:
            self.fail(f"unexpected status: {status}")

    def test_all_success_and_stable_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "example.test" / "fixtures" / "active" / "snapshots"
            write_request(snapshots, "GET-z")
            write_request(snapshots, "GET-a")

            exit_code, result, _, stderr, send = self.run_replay(
                site_root,
                replies=[response(200), response(201)],
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["total"], 2)
            self.assertEqual(result["selected"], 2)
            self.assertEqual(result["actual_artifacts"], [
                "actual/GET-a.actual.json",
                "actual/GET-z.actual.json",
            ])
            self.assertEqual(stderr, "")
            self.assertEqual(send.call_count, 2)

    def test_http_error_responses_are_replayed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "example.test" / "fixtures" / "snapshots"
            write_request(snapshots, "GET-404")
            write_request(snapshots, "GET-500")

            _, result, _, _, _ = self.run_replay(
                site_root,
                replies=[response(404), response(500)],
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["replayed"], 2)

    def test_mixed_transport_failure_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-a")
            write_request(fixtures / "snapshots", "GET-b")

            exit_code, result, _, stderr, _ = self.run_replay(
                site_root,
                replies=[response(200), response(0, "offline")],
            )

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "PARTIAL_FAILURE")
            self.assertEqual(result["replayed"], 1)
            self.assertEqual(result["failed"], 1)
            self.assertIn("offline", stderr)
            self.assertTrue((fixtures / "actual" / "GET-a.actual.json").is_file())
            self.assertFalse((fixtures / "actual" / "GET-b.actual.json").exists())

    def test_all_transport_failures_are_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-a")
            write_request(fixtures / "snapshots", "GET-b")

            exit_code, result, _, _, _ = self.run_replay(
                site_root,
                replies=[response(0, "a failed"), response(0, "b failed")],
            )

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(result["failed"], 2)
            self.assertFalse((fixtures / "actual").exists())

    def test_parse_failure_is_single_json_with_stderr_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-bad", "{not-json")

            exit_code, result, raw, stderr, send = self.run_replay(site_root)

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(result["failed"], 1)
            self.assertEqual(raw.count("\n"), 1)
            self.assertIn("ERROR parse GET-bad.req.json", stderr)
            send.assert_not_called()
            self.assertFalse((fixtures / "actual").exists())

    def test_invalid_request_shapes_are_replay_failures(self) -> None:
        invalid_documents = [
            "[]",
            json.dumps({"method": "GET", "url": 7}),
            json.dumps({
                "method": "GET",
                "url": "https://example.test/data",
                "headers": [],
            }),
        ]
        for content in invalid_documents:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                fixtures = site_root / "example.test" / "fixtures"
                write_request(fixtures / "snapshots", "GET-bad", content)

                exit_code, result, _, stderr, send = self.run_replay(site_root)

                self.assertEqual(exit_code, 3)
                self.assertEqual(result["status"], "FAILURE")
                self.assertEqual(result["selected"], 1)
                self.assertEqual(result["failed"], 1)
                self.assertIn("ERROR request shape GET-bad.req.json", stderr)
                send.assert_not_called()
                self.assertFalse((fixtures / "actual").exists())

    def test_invalid_request_shape_can_be_partial_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-a-good")
            write_request(fixtures / "snapshots", "GET-b-bad", "[]")

            exit_code, result, _, _, send = self.run_replay(
                site_root,
                replies=[response(200)],
            )

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "PARTIAL_FAILURE")
            self.assertEqual(result["selected"], 2)
            self.assertEqual(result["replayed"], 1)
            self.assertEqual(result["failed"], 1)
            send.assert_called_once()

    def test_metadata_is_normalized_and_native_expiry_is_counted(self) -> None:
        expired_values = [
            ["not", "a", "mapping"],
            {"expires_at": datetime.datetime(2000, 1, 1)},
            {"expires_at": datetime.date(2000, 1, 1)},
        ]
        for metadata in expired_values:
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                snapshots = site_root / "example.test" / "fixtures" / "snapshots"
                write_request(snapshots, "GET-a")
                (snapshots / "GET-a.meta.yaml").write_text("present\n", encoding="utf-8")

                parser = mock.Mock()
                parser.safe_load.return_value = metadata
                with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                    exit_code, result, _, stderr, _ = self.run_replay(
                        site_root,
                        replies=[response(200)],
                    )

                self.assertEqual(exit_code, 0)
                if isinstance(metadata, list):
                    self.assertEqual(result["expired"], 0)
                    self.assertIn("root must be a mapping", stderr)
                else:
                    self.assertEqual(result["expired"], 1)
                    self.assertIn("expired at", stderr)

    def test_invalid_expiry_value_is_diagnosed_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "example.test" / "fixtures" / "snapshots"
            write_request(snapshots, "GET-a")
            (snapshots / "GET-a.meta.yaml").write_text("present\n", encoding="utf-8")

            parser = mock.Mock()
            parser.safe_load.return_value = {"expires_at": ["invalid"]}
            with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                exit_code, result, _, stderr, _ = self.run_replay(
                    site_root,
                    replies=[response(200)],
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["expired"], 0)
            self.assertIn("invalid expires_at", stderr)

    def test_malformed_and_falsy_metadata_are_diagnosed(self) -> None:
        metadata_cases = [False, 0, "", []]
        for metadata in metadata_cases:
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                snapshots = site_root / "example.test" / "fixtures" / "snapshots"
                write_request(snapshots, "GET-a")
                (snapshots / "GET-a.meta.yaml").write_text("invalid\n", encoding="utf-8")
                parser = mock.Mock()
                parser.safe_load.return_value = metadata

                with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                    exit_code, result, _, stderr, _ = self.run_replay(
                        site_root,
                        replies=[response(200)],
                    )

                self.assertEqual(exit_code, 0)
                self.assertEqual(result["expired"], 0)
                self.assertIn("root must be a mapping", stderr)

        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "example.test" / "fixtures" / "snapshots"
            write_request(snapshots, "GET-a")
            (snapshots / "GET-a.meta.yaml").write_text(": malformed", encoding="utf-8")
            parser = mock.Mock()
            parser.safe_load.side_effect = ValueError("malformed YAML")

            with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                exit_code, result, _, stderr, _ = self.run_replay(
                    site_root,
                    replies=[response(200)],
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["expired"], 0)
            self.assertIn("malformed YAML", stderr)

    def test_falsy_expiry_values_are_invalid_not_missing(self) -> None:
        for expiry in (False, 0, "", []):
            with self.subTest(expiry=expiry), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                snapshots = site_root / "example.test" / "fixtures" / "snapshots"
                write_request(snapshots, "GET-a")
                (snapshots / "GET-a.meta.yaml").write_text("present\n", encoding="utf-8")
                parser = mock.Mock()
                parser.safe_load.return_value = {"expires_at": expiry}

                with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                    exit_code, result, _, stderr, _ = self.run_replay(
                        site_root,
                        replies=[response(200)],
                    )

                self.assertEqual(exit_code, 0)
                self.assertEqual(result["expired"], 0)
                self.assertIn("invalid expires_at", stderr)

    def test_expired_metadata_counts_when_request_shape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "example.test" / "fixtures" / "snapshots"
            write_request(snapshots, "GET-bad", "[]")
            (snapshots / "GET-bad.meta.yaml").write_text("present\n", encoding="utf-8")
            parser = mock.Mock()
            parser.safe_load.return_value = {
                "expires_at": datetime.datetime(2000, 1, 1),
            }

            with mock.patch.object(snapshot_replay, "yaml_parser", parser):
                exit_code, result, _, stderr, send = self.run_replay(site_root)

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(result["expired"], 1)
            self.assertIn("expired at", stderr)
            send.assert_not_called()

    def test_atomic_write_failure_removes_partial_and_stale_actual(self) -> None:
        class PartialTempFile:
            def __init__(self, path: Path):
                self.name = str(path)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def write(self, value: str) -> int:
                Path(self.name).write_text(value[:5], encoding="utf-8")
                raise OSError("disk full")

        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-a")
            actual_dir = fixtures / "actual"
            actual_dir.mkdir()
            actual_file = actual_dir / "GET-a.actual.json"
            actual_file.write_text("stale", encoding="utf-8")
            temp_file = actual_dir / ".GET-a.actual.json.partial.tmp"

            with mock.patch.object(
                snapshot_replay.tempfile,
                "NamedTemporaryFile",
                return_value=PartialTempFile(temp_file),
            ):
                exit_code, result, _, stderr, _ = self.run_replay(
                    site_root,
                    replies=[response(200)],
                )

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(result["actual_artifacts"], [])
            self.assertIn("disk full", stderr)
            self.assertFalse(actual_file.exists())
            self.assertFalse(temp_file.exists())

    def test_mkdir_failure_removes_stale_actual_and_temp_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-a")
            actual_dir = fixtures / "actual"
            actual_dir.mkdir()
            actual_file = actual_dir / "GET-a.actual.json"
            actual_file.write_text("stale", encoding="utf-8")
            temp_file = actual_dir / ".GET-a.actual.json.orphan.tmp"
            temp_file.write_text("partial", encoding="utf-8")

            with mock.patch.object(Path, "mkdir", side_effect=OSError("mkdir denied")):
                exit_code, result, _, stderr, _ = self.run_replay(
                    site_root,
                    replies=[response(200)],
                )

            self.assertEqual(exit_code, 3)
            self.assertEqual(result["status"], "FAILURE")
            self.assertEqual(result["actual_artifacts"], [])
            self.assertIn("mkdir denied", stderr)
            self.assertFalse(actual_file.exists())
            self.assertFalse(temp_file.exists())

    def test_missing_snapshots_is_no_data_without_actual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            (fixtures / "active").mkdir(parents=True)

            exit_code, result, _, stderr, send = self.run_replay(site_root)

            self.assertEqual(exit_code, 4)
            self.assertEqual(result["status"], "NO_DATA")
            self.assertIn("not found", stderr)
            send.assert_not_called()
            self.assertFalse((fixtures / "active" / "actual").exists())

    def test_zero_requests_is_no_data_without_actual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            (fixtures / "active" / "snapshots").mkdir(parents=True)

            exit_code, result, _, _, send = self.run_replay(site_root)

            self.assertEqual(exit_code, 4)
            self.assertEqual(result["total"], 0)
            send.assert_not_called()
            self.assertFalse((fixtures / "active" / "actual").exists())

    def test_filter_selects_zero_is_no_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_request(fixtures / "snapshots", "GET-present")

            exit_code, result, _, _, send = self.run_replay(
                site_root,
                "--filter",
                "missing",
            )

            self.assertEqual(exit_code, 4)
            self.assertEqual(result["total"], 1)
            self.assertEqual(result["filtered"], 1)
            send.assert_not_called()
            self.assertFalse((fixtures / "actual").exists())

    def test_original_target_is_refused_without_actual_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            actual = site_root / "example.test" / "fixtures" / "actual"
            actual.mkdir(parents=True)
            marker = actual / "existing.txt"
            marker.write_text("keep", encoding="utf-8")

            exit_code, result, _, stderr, send = self.run_replay(
                site_root,
                replies=[],
                *["--target", "original"],
            )

            self.assertEqual(exit_code, 2)
            self.assertEqual(result["status"], "REFUSED")
            self.assertIn("危险", stderr)
            send.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_malformed_adapter_target_is_refused_without_original_fallback(self) -> None:
        for target in (
            "https://",
            "ftp://adapter.test",
            "https://adapter.test:notaport",
            "https://adapter.test:70000",
            "https://adapter.test:",
            "https://adapter .test",
            "https://adapter..test",
            "https://-adapter.test",
            "https://user:secret@adapter.test",
        ):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                actual = site_root / "example.test" / "fixtures" / "actual"
                actual.mkdir(parents=True)
                marker = actual / "existing.txt"
                marker.write_text("keep", encoding="utf-8")

                exit_code, result, _, stderr, send = self.run_replay(
                    site_root,
                    "--target",
                    target,
                    "--allow-original",
                )

                self.assertEqual(exit_code, 2)
                self.assertEqual(result["status"], "REFUSED")
                self.assertIn("invalid --target", stderr)
                send.assert_not_called()
                self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_argparse_failures_emit_one_replay_result(self) -> None:
        cases = [
            (["snapshot_replay.py", "--help"], "usage:"),
            (["snapshot_replay.py", "--target", "https://adapter.test"], "error:"),
            ([
                "snapshot_replay.py",
                "--domain",
                "example.test",
                "--target",
                "https://adapter.test",
                "--timeout",
                "invalid",
            ], "error:"),
            ([
                "snapshot_replay.py",
                "--domain",
                "example.test",
                "--target",
                "https://adapter.test",
                "--unknown-option",
            ], "error:"),
            ([
                "snapshot_replay.py",
                "--domain",
                "example.test",
                "--target",
                "https://adapter.test",
                "--timeo",
                "1",
            ], "error:"),
            ([
                "snapshot_replay.py",
                "--dom",
                "example.test",
                "--target",
                "https://adapter.test",
            ], "error:"),
        ]
        for argv, diagnostic in cases:
            with self.subTest(argv=argv), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"

                exit_code, result, raw, stderr, send = self.run_cli_args(
                    site_root, argv
                )

                self.assertEqual(exit_code, 2)
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(raw.count("\n"), 1)
                self.assertIn(diagnostic, stderr.lower())
                send.assert_not_called()
                self.assertFalse(site_root.exists())

                process = subprocess.run(
                    [sys.executable, str(Path(snapshot_replay.__file__)), *argv[1:]],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                process_result = json.loads(process.stdout)
                self.assertEqual(process.returncode, process_result["exit_code"])
                self.assertEqual(process.returncode, 2)
                self.assertEqual(process.stdout.count("\n"), 1)
                self.assertIn(diagnostic, process.stderr.lower())

    def test_unsafe_domains_are_refused_without_external_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / "sites"
            outside = root / "outside.test"
            write_request(outside / "fixtures" / "snapshots", "GET-outside")
            marker = outside / "fixtures" / "actual" / "existing.txt"
            marker.parent.mkdir()
            marker.write_text("keep", encoding="utf-8")
            unsafe_domains = [
                str(outside),
                "../outside.test",
                "safe/../outside.test",
                "safe\\outside.test",
                ".",
                "..",
            ]

            for domain in unsafe_domains:
                with self.subTest(domain=domain):
                    exit_code, result, _, stderr, send = self.run_replay(
                        site_root,
                        "--domain",
                        domain,
                    )

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(result["status"], "REFUSED")
                    self.assertIn("invalid --domain", stderr)
                    send.assert_not_called()
                    self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
                    self.assertFalse(
                        (outside / "fixtures" / "actual" / "GET-outside.actual.json").exists()
                    )

    def test_domain_symlink_escape_is_refused_by_resolved_containment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / "sites"
            outside = root / "outside.test"
            write_request(outside / "fixtures" / "snapshots", "GET-outside")
            site_root.mkdir()
            (site_root / "escape.test").symlink_to(outside, target_is_directory=True)

            exit_code, result, _, stderr, send = self.run_replay(
                site_root,
                "--domain",
                "escape.test",
            )

            self.assertEqual(exit_code, 2)
            self.assertEqual(result["status"], "REFUSED")
            self.assertIn("outside SITE_ROOT", stderr)
            send.assert_not_called()
            self.assertFalse((outside / "fixtures" / "actual").exists())

    def test_control_domains_are_rejected_before_any_path_access(self) -> None:
        direct_domains = [
            "bad\x01",
            "bad\x7f",
            "bad\u200b",
            "bad\ue000",
            "bad\u0378",
            "bad\ud800",
            "bad name",
            "bad/name",
            "bad\\name",
            ".",
            "..",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            for domain in direct_domains:
                with (
                    self.subTest(domain=repr(domain)),
                    mock.patch.object(
                        Path,
                        "resolve",
                        side_effect=AssertionError("path access before rejection"),
                    ),
                    mock.patch.object(snapshot_replay, "select_fixture_layout") as selector,
                ):
                    exit_code, result, _, stderr, send = self.run_replay(
                        site_root,
                        "--domain",
                        domain,
                    )

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(result["status"], "REFUSED")
                    self.assertIn("invalid --domain", stderr)
                    selector.assert_not_called()
                    send.assert_not_called()

            cli_domains = [
                "bad\x01",
                "bad\x7f",
                "bad\u200b",
                "bad\ue000",
                "bad\u0378",
                "bad name",
                "bad/name",
                ".",
                "..",
                str(Path(tmp) / "absolute.test"),
            ]
            for domain in cli_domains:
                with self.subTest(cli_domain=repr(domain)):
                    process = subprocess.run(
                        [
                            sys.executable,
                            str(Path(snapshot_replay.__file__)),
                            "--domain",
                            domain,
                            "--target",
                            "https://adapter.test",
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    result = json.loads(process.stdout)
                    self.assertEqual(process.returncode, 2)
                    self.assertEqual(result["status"], "REFUSED")
                    self.assertEqual(result["exit_code"], process.returncode)
                    self.assertEqual(process.stdout.count("\n"), 1)
                    self.assertIn("invalid --domain", process.stderr)

    def test_valid_idn_domain_remains_a_safe_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            snapshots = site_root / "例子.test" / "fixtures" / "snapshots"
            snapshots.mkdir(parents=True)

            exit_code, result, _, _, send = self.run_replay(
                site_root,
                "--domain",
                "例子.test",
            )

            self.assertEqual(exit_code, 4)
            self.assertEqual(result["status"], "NO_DATA")
            send.assert_not_called()


class WorkflowReplayResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = (REPO_ROOT / ".github/workflows/consistency-replay.yml").read_text(
            encoding="utf-8"
        )

    def validator_source(self) -> str:
        start_marker = "# REPLAY_RESULT_VALIDATOR_START"
        end_marker = "# REPLAY_RESULT_VALIDATOR_END"
        start = self.workflow.index(start_marker) + len(start_marker)
        end = self.workflow.index(end_marker, start)
        return textwrap.dedent(self.workflow[start:end]).strip() + "\n"

    def domain_driver_source(self) -> str:
        start_marker = "# REPLAY_DOMAIN_DRIVER_START"
        end_marker = "# REPLAY_DOMAIN_DRIVER_END"
        start = self.workflow.index(start_marker) + len(start_marker)
        end = self.workflow.index(end_marker, start)
        return textwrap.dedent(self.workflow[start:end]).strip() + "\n"

    def domain_discovery_source(self) -> str:
        start_marker = "# REPLAY_DOMAIN_DISCOVERY_START"
        end_marker = "# REPLAY_DOMAIN_DISCOVERY_END"
        start = self.workflow.index(start_marker) + len(start_marker)
        end = self.workflow.index(end_marker, start)
        return textwrap.dedent(self.workflow[start:end]).strip() + "\n"

    def domain_handoff_source(self) -> str:
        start_marker = "# REPLAY_DOMAIN_HANDOFF_START"
        end_marker = "# REPLAY_DOMAIN_HANDOFF_END"
        start = self.workflow.index(start_marker) + len(start_marker)
        end = self.workflow.index(end_marker, start)
        return textwrap.dedent(self.workflow[start:end]).strip() + "\n"

    def domain_mapping_validator_source(self) -> str:
        start_marker = "# REPLAY_DOMAIN_MAPPING_VALIDATOR_START"
        end_marker = "# REPLAY_DOMAIN_MAPPING_VALIDATOR_END"
        start = self.workflow.index(start_marker) + len(start_marker)
        end = self.workflow.index(end_marker, start)
        return textwrap.dedent(self.workflow[start:end]).strip() + "\n"

    def validate(self, document: str, process_exit: int) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            result_file = Path(tmp) / "result.json"
            result_file.write_text(document, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-", str(result_file), str(process_exit)],
                input=self.validator_source(),
                text=True,
                capture_output=True,
                check=False,
            )

    def pass_result(self) -> dict:
        return {
            "status": "PASS",
            "exit_code": 0,
            "total": 1,
            "selected": 1,
            "replayed": 1,
            "failed": 0,
            "expired": 0,
            "no_data": False,
            "actual_artifacts": ["actual/GET-a.actual.json"],
            "filtered": 0,
        }

    def test_validator_rejects_malformed_mismatch_and_replay_failure(self) -> None:
        valid = json.dumps(self.pass_result())
        self.assertEqual(self.validate(valid, 0).returncode, 0)
        self.assertNotEqual(self.validate("not-json", 0).returncode, 0)
        self.assertNotEqual(self.validate(valid, 3).returncode, 0)
        for constant in ("NaN", "Infinity", "-Infinity"):
            non_finite = valid.replace('"expired": 0', f'"expired": {constant}')
            self.assertNotEqual(self.validate(non_finite, 0).returncode, 0)
        duplicate_required = valid[:-1] + ', "status": "PASS"}'
        nested_duplicate = valid[:-1] + ', "extra": {"x": 1, "x": 2}}'
        self.assertNotEqual(self.validate(duplicate_required, 0).returncode, 0)
        self.assertNotEqual(self.validate(nested_duplicate, 0).returncode, 0)

        failure = self.pass_result()
        failure.update({
            "status": "FAILURE",
            "exit_code": 3,
            "replayed": 0,
            "failed": 1,
            "actual_artifacts": [],
        })
        self.assertNotEqual(self.validate(json.dumps(failure), 3).returncode, 0)

    def test_actual_workflow_driver_gates_continues_and_aggregates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            replay_inputs = root / "replay-inputs"
            fake_bin.mkdir()
            replay_inputs.mkdir()
            consistency_log = root / "consistency.log"
            fake_python = fake_bin / "python3"
            fake_python.write_text(
                f"""#!{sys.executable}
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if args and args[0].endswith('snapshot_replay.py'):
    domain = args[args.index('--domain') + 1]
    root = Path(os.environ['FAKE_REPLAY_DIR'])
    sys.stdout.write((root / f'{{domain}}.stdout').read_text(encoding='utf-8'))
    raise SystemExit(int((root / f'{{domain}}.exit').read_text(encoding='utf-8')))
if args and args[0].endswith('consistency_report.py'):
    domain = args[args.index('--domain') + 1]
    with open(os.environ['FAKE_CONSISTENCY_LOG'], 'a', encoding='utf-8') as handle:
        handle.write(domain + '\\n')
    raise SystemExit(0)
if args and args[0] == '-':
    os.execv({sys.executable!r}, [{sys.executable!r}, *args])
raise SystemExit(99)
""",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)

            failure = {
                **self.pass_result(),
                "status": "FAILURE",
                "exit_code": 3,
                "replayed": 0,
                "failed": 1,
                "actual_artifacts": [],
            }
            valid = json.dumps(self.pass_result())
            nan_result = valid.replace('"expired": 0', '"expired": NaN')
            infinity_result = valid.replace('"expired": 0', '"expired": Infinity')
            duplicate_required = valid[:-1] + ', "status": "PASS"}'
            nested_duplicate = valid[:-1] + ', "extra": {"x": 1, "x": 2}}'
            documents = {
                "malformed.test": ("not-json\n", 0),
                "mismatch.test": (json.dumps(self.pass_result()) + "\n", 3),
                "failure.test": (json.dumps(failure) + "\n", 3),
                "nan.test": (nan_result + "\n", 0),
                "infinity.test": (infinity_result + "\n", 0),
                "duplicate-required.test": (duplicate_required + "\n", 0),
                "duplicate-nested.test": (nested_duplicate + "\n", 0),
                "pass.test": (valid + "\n", 0),
            }
            for domain, (document, exit_code) in documents.items():
                (replay_inputs / f"{domain}.stdout").write_text(
                    document, encoding="utf-8"
                )
                (replay_inputs / f"{domain}.exit").write_text(
                    str(exit_code), encoding="utf-8"
                )

            env = os.environ.copy()
            env.update({
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "DOMAINS_JSON": json.dumps(sorted(documents), separators=(",", ":")),
                "ADAPTER_URL": "https://adapter.test",
                "THRESHOLD": "0.90",
                "FAKE_REPLAY_DIR": str(replay_inputs),
                "FAKE_CONSISTENCY_LOG": str(consistency_log),
            })
            completed = subprocess.run(
                ["bash", "-c", self.domain_driver_source()],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 3, completed.stderr)
            self.assertEqual(
                consistency_log.read_text(encoding="utf-8").splitlines(),
                ["pass.test"],
            )
            mapping = json.loads(
                (root / ".ci-out" / "replay" / "domain-map.json").read_text(
                    encoding="utf-8"
                )
            )
            key_by_domain = {
                entry["domain"]: entry["key"] for entry in mapping["entries"]
            }
            for domain, (document, _) in documents.items():
                captured = (
                    root
                    / ".ci-out"
                    / "replay"
                    / f"{key_by_domain[domain]}.json"
                )
                self.assertEqual(captured.read_text(encoding="utf-8"), document)

    def test_discovery_json_handoff_processes_comma_domain_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / "sites"
            expected_domains = ["a", "a,b", "b"]
            for domain in expected_domains:
                write_request(
                    site_root / domain / "fixtures" / "snapshots",
                    "GET-a",
                )

            discovery = subprocess.run(
                [sys.executable, "-", str(REPO_ROOT), str(site_root)],
                input=self.domain_discovery_source(),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(discovery.returncode, 0, discovery.stderr)
            self.assertEqual(json.loads(discovery.stdout), expected_domains)
            self.assertEqual(
                discovery.stdout,
                json.dumps(expected_domains, ensure_ascii=True, separators=(",", ":"))
                + "\n",
            )

            fake_bin = root / "bin"
            replay_inputs = root / "replay-inputs"
            fake_bin.mkdir()
            replay_inputs.mkdir()
            replay_log = root / "replay.log"
            consistency_log = root / "consistency.log"
            fake_python = fake_bin / "python3"
            fake_python.write_text(
                f"""#!{sys.executable}
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if args and args[0].endswith('snapshot_replay.py'):
    domain = args[args.index('--domain') + 1]
    with open(os.environ['FAKE_REPLAY_LOG'], 'a', encoding='utf-8') as handle:
        handle.write(domain + '\\n')
    root = Path(os.environ['FAKE_REPLAY_DIR'])
    sys.stdout.write((root / f'{{domain}}.stdout').read_text(encoding='utf-8'))
    raise SystemExit(int((root / f'{{domain}}.exit').read_text(encoding='utf-8')))
if args and args[0].endswith('consistency_report.py'):
    domain = args[args.index('--domain') + 1]
    with open(os.environ['FAKE_CONSISTENCY_LOG'], 'a', encoding='utf-8') as handle:
        handle.write(domain + '\\n')
    raise SystemExit(0)
if args and args[0] == '-':
    os.execv({sys.executable!r}, [{sys.executable!r}, *args])
raise SystemExit(99)
""",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            document = json.dumps(self.pass_result()) + "\n"
            for domain in expected_domains:
                (replay_inputs / f"{domain}.stdout").write_text(
                    document, encoding="utf-8"
                )
                (replay_inputs / f"{domain}.exit").write_text("0", encoding="utf-8")

            env = os.environ.copy()
            env.update({
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "DOMAINS_JSON": discovery.stdout.strip(),
                "ADAPTER_URL": "https://adapter.test",
                "THRESHOLD": "0.90",
                "FAKE_REPLAY_DIR": str(replay_inputs),
                "FAKE_REPLAY_LOG": str(replay_log),
                "FAKE_CONSISTENCY_LOG": str(consistency_log),
            })
            completed = subprocess.run(
                ["bash", "-c", self.domain_driver_source()],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                replay_log.read_text(encoding="utf-8").splitlines(),
                expected_domains,
            )
            self.assertEqual(
                consistency_log.read_text(encoding="utf-8").splitlines(),
                expected_domains,
            )
            mapping_path = root / ".ci-out" / "replay" / "domain-map.json"
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [entry["domain"] for entry in mapping["entries"]],
                expected_domains,
            )
            key_by_domain = {
                entry["domain"]: entry["key"] for entry in mapping["entries"]
            }
            for domain in expected_domains:
                captured = (
                    root
                    / ".ci-out"
                    / "replay"
                    / f"{key_by_domain[domain]}.json"
                )
                self.assertEqual(captured.read_text(encoding="utf-8"), document)

            replay_count = replay_log.read_text(encoding="utf-8")
            malformed_handoffs = [
                "not-json",
                json.dumps(["a", "a"]),
                json.dumps(["b", "a"]),
                json.dumps(["a\nb"]),
            ]
            for index, handoff in enumerate(malformed_handoffs):
                malformed_root = root / f"malformed-{index}"
                malformed_root.mkdir()
                malformed_env = {**env, "DOMAINS_JSON": handoff}
                malformed = subprocess.run(
                    ["bash", "-c", self.domain_driver_source()],
                    cwd=malformed_root,
                    env=malformed_env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(malformed.returncode, 3)
                self.assertIn("Malformed domain handoff", malformed.stdout)
                self.assertEqual(
                    replay_log.read_text(encoding="utf-8"), replay_count
                )
                self.assertEqual(
                    list((malformed_root / ".ci-out" / "replay").glob("*.json")),
                    [],
                )

    def test_name_max_domains_use_bounded_traceable_collision_safe_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / "sites"
            long_a = "a" * 251
            long_b = "a" * 250 + "b"
            non_ascii_a = "例" * 80 + "a"
            non_ascii_b = "例" * 80 + "b"
            injection = "$(touch${IFS}pwned)"
            expected_domains = sorted([
                long_a,
                long_b,
                non_ascii_a,
                non_ascii_b,
                injection,
            ])
            for domain in expected_domains:
                write_request(
                    site_root / domain / "fixtures" / "snapshots",
                    "GET-a",
                )

            discovery = subprocess.run(
                [sys.executable, "-", str(REPO_ROOT), str(site_root)],
                input=self.domain_discovery_source(),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(discovery.returncode, 0, discovery.stderr)
            self.assertEqual(json.loads(discovery.stdout), expected_domains)

            fake_bin = root / "bin"
            fake_bin.mkdir()
            replay_log = root / "replay.log"
            consistency_log = root / "consistency.log"
            fake_python = fake_bin / "python3"
            fake_python.write_text(
                f"""#!{sys.executable}
import os
import sys

args = sys.argv[1:]
if args and args[0].endswith('snapshot_replay.py'):
    domain = args[args.index('--domain') + 1]
    with open(os.environ['FAKE_REPLAY_LOG'], 'a', encoding='utf-8') as handle:
        handle.write(domain + '\\n')
    sys.stdout.write(os.environ['FAKE_REPLAY_DOCUMENT'])
    raise SystemExit(0)
if args and args[0].endswith('consistency_report.py'):
    domain = args[args.index('--domain') + 1]
    with open(os.environ['FAKE_CONSISTENCY_LOG'], 'a', encoding='utf-8') as handle:
        handle.write(domain + '\\n')
    raise SystemExit(0)
if args and args[0] == '-':
    os.execv({sys.executable!r}, [{sys.executable!r}, *args])
raise SystemExit(99)
""",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            document = json.dumps(self.pass_result()) + "\n"
            env = os.environ.copy()
            env.update({
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "DOMAINS_JSON": discovery.stdout.strip(),
                "ADAPTER_URL": "https://adapter.test",
                "THRESHOLD": "0.90",
                "FAKE_REPLAY_LOG": str(replay_log),
                "FAKE_CONSISTENCY_LOG": str(consistency_log),
                "FAKE_REPLAY_DOCUMENT": document,
            })
            completed = subprocess.run(
                ["bash", "-c", self.domain_driver_source()],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                replay_log.read_text(encoding="utf-8").splitlines(),
                expected_domains,
            )
            self.assertEqual(
                consistency_log.read_text(encoding="utf-8").splitlines(),
                expected_domains,
            )
            replay_root = root / ".ci-out" / "replay"
            mapping_path = replay_root / "domain-map.json"
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            self.assertEqual(mapping["schema_version"], 1)
            self.assertEqual(
                [entry["domain"] for entry in mapping["entries"]],
                expected_domains,
            )
            keys = [entry["key"] for entry in mapping["entries"]]
            self.assertEqual(len(keys), len(set(keys)))
            key_by_domain = {
                entry["domain"]: entry["key"] for entry in mapping["entries"]
            }
            for domain, key in key_by_domain.items():
                self.assertRegex(key, r"^[a-z0-9][a-z0-9._-]*--[0-9a-f]{64}$")
                self.assertLessEqual(len((key + ".json").encode("utf-8")), 128)
                self.assertEqual(
                    (replay_root / f"{key}.json").read_text(encoding="utf-8"),
                    document,
                )
                self.assertNotIn(domain, key)
            self.assertNotEqual(key_by_domain[long_a], key_by_domain[long_b])
            self.assertNotEqual(
                key_by_domain[non_ascii_a], key_by_domain[non_ascii_b]
            )
            self.assertFalse((root / "pwned").exists())

    def test_domain_mapping_validator_rejects_malformed_coverage_and_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mapping_path = root / "domain-map.json"
            domains = ["a", "a,b", "b"]
            domains_json = json.dumps(domains, separators=(",", ":"))
            built = subprocess.run(
                [sys.executable, "-", domains_json, str(mapping_path)],
                input=self.domain_handoff_source(),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            valid_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            validated = subprocess.run(
                [sys.executable, "-", domains_json, str(mapping_path)],
                input=self.domain_mapping_validator_source(),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(
                [line.split("\t", 1)[1] for line in validated.stdout.splitlines()],
                domains,
            )

            missing = json.loads(json.dumps(valid_mapping))
            missing["entries"].pop()
            duplicate_key = json.loads(json.dumps(valid_mapping))
            duplicate_key["entries"][1]["key"] = duplicate_key["entries"][0]["key"]
            unsafe_key = json.loads(json.dumps(valid_mapping))
            unsafe_key["entries"][0]["key"] = "../escape"
            oversized_key = json.loads(json.dumps(valid_mapping))
            oversized_key["entries"][0]["key"] = "a" * 129
            malformed_documents = [
                "not-json",
                json.dumps(missing),
                json.dumps(duplicate_key),
                json.dumps(unsafe_key),
                json.dumps(oversized_key),
            ]
            for document_value in malformed_documents:
                mapping_path.write_text(document_value, encoding="utf-8")
                rejected = subprocess.run(
                    [sys.executable, "-", domains_json, str(mapping_path)],
                    input=self.domain_mapping_validator_source(),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(rejected.stdout, "")

    def test_workflow_captures_and_retains_each_replay_result(self) -> None:
        self.assertNotIn("snapshot_replay.py \\\n+              --domain \"$d\" \\\n+              --target \"${{ steps.adapter.outputs.url }}\" || true", self.workflow)
        self.assertIn('> "$result_file"', self.workflow)
        self.assertIn("replay_exit=$?", self.workflow)
        self.assertIn("domains_json=%s", self.workflow)
        self.assertIn("DOMAINS_JSON: ${{ needs.validate-schema.outputs.domains }}", self.workflow)
        self.assertNotIn("IFS=','", self.workflow)
        self.assertIn("domain-map.json", self.workflow)
        self.assertIn('if [ "$validation_exit" -eq 0 ]; then', self.workflow)
        self.assertIn("name: Upload ReplayResult artifacts", self.workflow)
        self.assertIn("if: always() && steps.adapter.outputs.skip != 'true'", self.workflow)
        self.assertIn("path: .ci-out/replay/", self.workflow)


if __name__ == "__main__":
    unittest.main()
