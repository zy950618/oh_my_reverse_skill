from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import shutil
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

import consistency_report
import fixture_gate
import fixture_layout
import snapshot_replay
import validate_fixtures


def write_snapshot(snapshots: Path, prefix: str = "GET-example") -> None:
    snapshots.mkdir(parents=True, exist_ok=True)
    (snapshots / f"{prefix}.req.json").write_text(
        json.dumps({"method": "GET", "url": "https://example.test/data"}),
        encoding="utf-8",
    )
    response = {"status": 200, "headers": {}, "body": {"value": 1}}
    (snapshots / f"{prefix}.resp.json").write_text(
        json.dumps(response), encoding="utf-8"
    )
    (snapshots / f"{prefix}.meta.yaml").write_text(
        "\n".join(
            [
                "endpoint: example",
                "recorded_at: 2026-07-14T00:00:00Z",
                "captured_at: 2026-07-14T00:00:00Z",
                "expires_at: 2099-01-01T00:00:00Z",
                "category: public-read",
                "sensitive: false",
                "requires_auth: false",
                "source: unit-test",
                "schema_version: fixture-meta-v2",
                "review_status: reviewed",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_actual(actual_dir: Path, prefix: str = "GET-example") -> None:
    actual_dir.mkdir(parents=True, exist_ok=True)
    (actual_dir / f"{prefix}.actual.json").write_text(
        json.dumps({"status": 200, "headers": {}, "body": {"value": 1}}),
        encoding="utf-8",
    )


def write_report(selected_root: Path, *, status: str = "PASS", total: int = 1, replayed: int = 1) -> Path:
    reports = selected_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report = reports / "2026-07-16-replay.md"
    report.write_text(
        "\n".join(
            [
                "# Replay",
                f"status: {status}",
                f"total: {total}",
                f"replayed: {replayed}",
                "source: unit-test",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report


class FixtureLayoutTests(unittest.TestCase):
    def test_active_over_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            (fixtures / "active").mkdir(parents=True)
            (fixtures / "snapshots").mkdir()

            selected, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(selected, fixtures / "active")
            self.assertEqual(snapshots, fixtures / "active" / "snapshots")

    def test_empty_active_does_not_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            (fixtures / "active" / "snapshots").mkdir(parents=True)
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")

            selected, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(selected, fixtures / "active")
            self.assertEqual(list(snapshots.glob("*.req.json")), [])

    def test_missing_active_snapshots_does_not_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            (fixtures / "active").mkdir(parents=True)
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")

            _, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(snapshots, fixtures / "active" / "snapshots")
            self.assertFalse(snapshots.exists())

    def test_non_directory_active_snapshots_does_not_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            (fixtures / "active").mkdir(parents=True)
            (fixtures / "active" / "snapshots").write_text("damaged", encoding="utf-8")
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")

            _, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(snapshots, fixtures / "active" / "snapshots")
            self.assertFalse(snapshots.is_dir())

    def test_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            write_snapshot(fixtures / "snapshots")

            selected, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(selected, fixtures)
            self.assertEqual(snapshots, fixtures / "snapshots")

    def test_historical_is_never_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = Path(tmp) / "fixtures"
            write_snapshot(fixtures / "historical" / "snapshots")

            selected, snapshots = fixture_layout.select_fixture_layout(fixtures)

            self.assertEqual(selected, fixtures)
            self.assertEqual(snapshots, fixtures / "snapshots")
            self.assertFalse(snapshots.exists())


class ReplayerConsumerTests(unittest.TestCase):
    def test_snapshot_replay_uses_active_snapshots_and_actual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_snapshot(fixtures / "active" / "snapshots", "GET-active")
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
            legacy_actual = fixtures / "actual"
            legacy_actual.mkdir()
            poison = legacy_actual / "POISON.txt"
            poison.write_text("do not touch", encoding="utf-8")
            reply = {"status": 200, "headers": {}, "body": {}, "_meta": {}}

            with (
                mock.patch.object(snapshot_replay, "SITE_ROOT", site_root),
                mock.patch.object(
                    snapshot_replay,
                    "select_fixture_layout",
                    wraps=fixture_layout.select_fixture_layout,
                ) as selector,
                mock.patch.object(snapshot_replay, "send_request", return_value=reply) as send,
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "snapshot_replay.py",
                        "--domain",
                        "example.test",
                        "--target",
                        "adapter.test",
                    ],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = snapshot_replay.main()

            self.assertEqual(result, 0)
            selector.assert_called_once_with(fixtures)
            send.assert_called_once()
            self.assertTrue((fixtures / "active" / "actual" / "GET-active.actual.json").is_file())
            self.assertFalse((legacy_actual / "GET-active.actual.json").exists())
            self.assertEqual(poison.read_text(encoding="utf-8"), "do not touch")

    def test_consistency_report_uses_only_active_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_snapshot(fixtures / "active" / "snapshots", "GET-active")
            write_actual(fixtures / "active" / "actual", "GET-active")
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
            write_actual(fixtures / "actual", "GET-legacy-poison")
            actual_poison = fixtures / "actual" / "POISON.txt"
            actual_poison.write_text("do not touch", encoding="utf-8")
            legacy_reports = fixtures / "reports"
            legacy_reports.mkdir()
            poison = legacy_reports / "POISON.txt"
            poison.write_text("do not touch", encoding="utf-8")
            diff_result = {
                "status_match": True,
                "snapshot_status": 200,
                "actual_status": 200,
                "total_fields": 1,
                "matched": 1,
                "mismatched": [],
                "missing": [],
                "extra": [],
                "structure_ok": True,
                "consistency_rate": 1.0,
                "empty_snapshot": False,
            }

            with (
                mock.patch.object(consistency_report, "SITE_ROOT", site_root),
                mock.patch.object(
                    consistency_report,
                    "select_fixture_layout",
                    wraps=fixture_layout.select_fixture_layout,
                ) as selector,
                mock.patch.object(consistency_report, "diff_snapshot", return_value=diff_result),
                mock.patch.object(
                    sys,
                    "argv",
                    ["consistency_report.py", "--domain", "example.test"],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = consistency_report.main()

            self.assertEqual(result, 0)
            selector.assert_called_once_with(fixtures)
            active_reports = fixtures / "active" / "reports"
            self.assertTrue(list(active_reports.glob("*-replay.md")))
            self.assertTrue((active_reports / "trend.json").is_file())
            self.assertEqual(actual_poison.read_text(encoding="utf-8"), "do not touch")
            self.assertEqual(poison.read_text(encoding="utf-8"), "do not touch")
            self.assertEqual(list(legacy_reports.glob("*-replay.md")), [])

    def test_validate_fixtures_uses_active_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "sites"
            fixtures = site_root / "example.test" / "fixtures"
            write_snapshot(fixtures / "active" / "snapshots", "GET-active")
            legacy = fixtures / "snapshots"
            legacy.mkdir(parents=True)
            (legacy / "GET-legacy-poison.req.json").write_text("{}", encoding="utf-8")
            output = io.StringIO()

            with (
                mock.patch.object(
                    fixture_gate,
                    "select_fixture_layout",
                    wraps=fixture_layout.select_fixture_layout,
                ) as selector,
                mock.patch.object(sys, "argv", ["validate_fixtures.py", str(site_root)]),
                contextlib.redirect_stdout(output),
            ):
                result = validate_fixtures.main()

            self.assertEqual(result, 0)
            selector.assert_called_once_with(fixtures)
            gate_result = json.loads(output.getvalue())
            self.assertEqual(gate_result["status"], "STALE")
            self.assertEqual(gate_result["totals"]["domains_selected"], 1)
            self.assertEqual(gate_result["totals"]["complete_triplets"], 1)
            self.assertEqual(gate_result["totals"]["valid_triplets"], 1)

    def test_damaged_active_snapshots_return_structured_no_data(self) -> None:
        for damage in ("missing", "non-directory"):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp) / "sites"
                fixtures = site_root / "example.test" / "fixtures"
                (fixtures / "active").mkdir(parents=True)
                if damage == "non-directory":
                    (fixtures / "active" / "snapshots").write_text(
                        "damaged", encoding="utf-8"
                    )
                write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
                write_actual(fixtures / "actual", "GET-legacy-poison")
                replay_output = io.StringIO()

                with (
                    mock.patch.object(snapshot_replay, "SITE_ROOT", site_root),
                    mock.patch.object(snapshot_replay, "send_request") as send,
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            "snapshot_replay.py",
                            "--domain",
                            "example.test",
                            "--target",
                            "adapter.test",
                        ],
                    ),
                    contextlib.redirect_stdout(replay_output),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(snapshot_replay.main(), 4)
                send.assert_not_called()
                replay_result = json.loads(replay_output.getvalue())
                self.assertEqual(replay_result["status"], "NO_DATA")
                self.assertEqual(replay_result["exit_code"], 4)
                self.assertTrue(replay_result["no_data"])
                self.assertEqual(replay_result["selected"], 0)
                self.assertEqual(replay_result["replayed"], 0)
                self.assertEqual(replay_result["failed"], 0)
                self.assertEqual(replay_result["actual_artifacts"], [])
                self.assertFalse((fixtures / "active" / "actual").exists())
                self.assertTrue(
                    (fixtures / "actual" / "GET-legacy-poison.actual.json").is_file()
                )

                with (
                    mock.patch.object(consistency_report, "SITE_ROOT", site_root),
                    mock.patch.object(sys, "argv", ["consistency_report.py", "--domain", "example.test"]),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    self.assertEqual(consistency_report.main(), 1)

                output = io.StringIO()
                with (
                    mock.patch.object(sys, "argv", ["validate_fixtures.py", str(site_root)]),
                    contextlib.redirect_stdout(output),
                ):
                    self.assertEqual(validate_fixtures.main(), 1)
                gate_result = json.loads(output.getvalue())
                self.assertEqual(gate_result["status"], "STRUCTURE_INVALID")
                self.assertTrue(gate_result["no_data"])
                self.assertEqual(gate_result["totals"]["complete_triplets"], 0)
                self.assertFalse((fixtures / "actual" / "GET-active.actual.json").exists())


class FixtureGateTests(unittest.TestCase):
    def make_site(self, root: Path, domain: str = "example.test") -> Path:
        active = root / domain / "fixtures" / "active"
        write_snapshot(active / "snapshots")
        write_report(active)
        return active

    def test_mode_truth_table_and_require_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            root.mkdir()
            expected = {
                fixture_gate.Mode.OFFLINE: ("NO_DATA", 0, "STRUCTURE_ONLY"),
                fixture_gate.Mode.DIAGNOSTIC: ("NO_DATA", 0, "DIAGNOSTIC_ONLY"),
                fixture_gate.Mode.STRICT: ("NO_DATA", 4, "NO_CAPABILITY"),
                fixture_gate.Mode.REFRESH: ("RECERTIFICATION_REQUIRED", 3, "REFRESH_PLAN"),
            }
            for mode, terminal in expected.items():
                with self.subTest(mode=mode):
                    result = fixture_gate.run_gate(
                        site_root=root,
                        tool="validate_fixtures",
                        mode=mode,
                        now=fixture_gate.dt.datetime(2026, 7, 16, tzinfo=fixture_gate.dt.timezone.utc),
                    ).to_dict()
                    self.assertEqual((result["status"], result["exit_code"], result["capability"]), terminal)
                    self.assertEqual(fixture_gate.validate_result_document(result), [])
            required = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.DIAGNOSTIC,
                require_data=True,
            ).to_dict()
            self.assertEqual((required["status"], required["exit_code"]), ("NO_DATA", 4))

    def test_strict_fresh_report_and_mtime_poison(self) -> None:
        now = fixture_gate.dt.datetime(2026, 7, 16, tzinfo=fixture_gate.dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            report = next((active / "reports").glob("*-replay.md"))
            timestamp = now.timestamp()
            os.utime(report, (timestamp, timestamp))
            result = fixture_gate.run_gate(
                site_root=root,
                tool="fixture_freshness_report",
                mode=fixture_gate.Mode.STRICT,
                require_data=True,
                now=now,
            ).to_dict()
            self.assertEqual((result["status"], result["capability"]), ("PASS", "FRESH_FIXTURE_GATE"))
            self.assertEqual(result["replay_lineage"], "UNKNOWN")
            self.assertEqual(fixture_gate.validate_result_document(result), [])

            report.write_text(
                "status: FAIL\ntotal: 1\nreplayed: 1\nsource: poison\n",
                encoding="utf-8",
            )
            os.utime(report, (timestamp, timestamp))
            poisoned = fixture_gate.run_gate(
                site_root=root,
                tool="fixture_freshness_report",
                mode=fixture_gate.Mode.STRICT,
                now=now,
            ).to_dict()
            self.assertEqual((poisoned["status"], poisoned["exit_code"]), ("STALE", 3))
            self.assertIn("REPORT_NOT_PASS", {item["reason"] for item in poisoned["issues"]})

    def test_domain_filter_is_sorted_unique_and_does_not_select_poison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            selected = "例子-selected.test"
            self.make_site(root, selected)
            poison = root / "sibling.test"
            poison.mkdir(parents=True)
            with mock.patch.object(Path, "iterdir", side_effect=AssertionError("root enumeration")):
                result = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.OFFLINE,
                    domains=[selected, selected],
                ).to_dict()
            self.assertEqual([item["domain"] for item in result["domains"]], [selected])
            self.assertEqual(result["status"], "STRUCTURE_ONLY")

    def test_structure_and_freshness_failure_matrix(self) -> None:
        cases = {
            "ORPHAN_REQ": lambda active: (active / "snapshots" / "GET-example.resp.json").unlink(),
            "JSON_MALFORMED": lambda active: (active / "snapshots" / "GET-example.req.json").write_text("{", encoding="utf-8"),
            "JSON_ROOT_NOT_OBJECT": lambda active: (active / "snapshots" / "GET-example.resp.json").write_text("[]", encoding="utf-8"),
            "META_REQUIRED_MISSING": lambda active: self.rewrite_meta(active, "endpoint: example\n", ""),
            "META_BOOL_INVALID": lambda active: self.rewrite_meta(active, "sensitive: false", "sensitive: maybe"),
            "CATEGORY_FORBIDDEN": lambda active: self.rewrite_meta(active, "category: public-read", "category: payment"),
            "EXPIRY_MISSING": lambda active: self.rewrite_meta(
                active, "expires_at: 2099-01-01T00:00:00Z", "expires_at: "
            ),
            "EXPIRY_INVALID": lambda active: self.rewrite_meta(active, "2099-01-01T00:00:00Z", "not-a-date"),
            "EXPIRED": lambda active: self.rewrite_meta(active, "2099-01-01T00:00:00Z", "2020-01-01T00:00:00Z"),
            "REVIEW_PENDING": lambda active: self.rewrite_meta(active, "endpoint: example", "endpoint: TODO review and edit"),
            "REPORT_MISSING": lambda active: next((active / "reports").glob("*-replay.md")).unlink(),
            "REPORT_MALFORMED": lambda active: next((active / "reports").glob("*-replay.md")).write_text("not a report\n", encoding="utf-8"),
            "REPORT_NOT_PASS": lambda active: write_report(active, status="FAIL"),
            "REPORT_COVERAGE_MISMATCH": lambda active: write_report(active, total=2, replayed=1),
        }
        structural = fixture_gate.STRUCTURE_REASONS
        for reason, poison in cases.items():
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "sites"
                active = self.make_site(root)
                poison(active)
                result = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.STRICT,
                    now=fixture_gate.dt.datetime(2026, 7, 16, tzinfo=fixture_gate.dt.timezone.utc),
                ).to_dict()
                self.assertIn(reason, {item["reason"] for item in result["issues"]})
                expected = ("STRUCTURE_INVALID", 1) if reason in structural else ("STALE", 3)
                self.assertEqual((result["status"], result["exit_code"]), expected)
                self.assertEqual(fixture_gate.validate_result_document(result), [])

    def test_acc_001_empty_metadata_fails_all_applicable_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            (active / "snapshots" / "GET-example.meta.yaml").write_text("", encoding="utf-8")
            result = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.STRICT,
            ).to_dict()
            reasons = {item["reason"] for item in result["issues"]}
            self.assertEqual((result["status"], result["exit_code"]), ("STRUCTURE_INVALID", 1))
            self.assertTrue({"META_REQUIRED_MISSING", "META_BOOL_INVALID", "EXPIRY_MISSING"} <= reasons)
            self.assertEqual(result["totals"]["valid_triplets"], 0)
            self.assertEqual(fixture_gate.validate_result_document(result), [])

    def test_acc_002_active_and_artifact_symlinks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            fixtures = root / "example.test" / "fixtures"
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
            (fixtures / "active").write_text("not a directory", encoding="utf-8")
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            self.assertEqual(result["domains"][0]["selected_layout"], "legacy")
            self.assertEqual(result["domains"][0]["request_files"], 1)
            self.assertEqual(result["status"], "STRUCTURE_ONLY")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            fixtures = root / "example.test" / "fixtures"
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
            (fixtures / "active").symlink_to(fixtures, target_is_directory=True)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            self.assertEqual(result["domains"][0]["selected_layout"], "active")
            self.assertEqual(result["domains"][0]["snapshots_state"], "NOT_DIRECTORY")
            self.assertEqual(result["domains"][0]["request_files"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            fixtures = root / "example.test" / "fixtures"
            active = fixtures / "active"
            write_snapshot(fixtures / "snapshots", "GET-legacy-poison")
            active.mkdir(parents=True)
            (active / "snapshots").symlink_to(fixtures / "snapshots", target_is_directory=True)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            self.assertEqual(result["domains"][0]["snapshots_state"], "NOT_DIRECTORY")
            self.assertEqual(result["domains"][0]["request_files"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = root / "example.test" / "fixtures" / "active"
            write_snapshot(active / "snapshots")
            outside = Path(tmp) / "outside-reports"
            write_report(outside)
            (active / "reports").symlink_to(outside, target_is_directory=True)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertIn("REPORT_MALFORMED", {item["reason"] for item in result["issues"]})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            request = active / "snapshots" / "GET-example.req.json"
            outside = Path(tmp) / "outside.req.json"
            outside.write_text('{}', encoding="utf-8")
            request.unlink()
            request.symlink_to(outside)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertIn("JSON_UNREADABLE", {item["reason"] for item in result["issues"]})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            owner = Path(tmp) / "owner.json"
            owner.write_text("owner", encoding="utf-8")
            out = Path(tmp) / "refresh.json"
            out.symlink_to(owner)
            with mock.patch.object(fixture_gate, "REPO_ROOT", Path(tmp)):
                result = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=out,
                ).to_dict()
            self.assertEqual((result["status"], result["exit_code"]), ("INTERNAL_ERROR", 5))
            self.assertTrue(out.is_symlink())
            self.assertEqual(owner.read_text(encoding="utf-8"), "owner")

    def test_acc_003_validator_is_total_for_malformed_json_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            valid = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            malformed_values = [None, [], [1], "value", 1, True]
            for key, element in (("domains", None), ("issues", []), ("refresh_tasks", "bad")):
                poisoned = json.loads(json.dumps(valid))
                poisoned[key] = [element]
                malformed_values.append(poisoned)
            malformed_top = {key: [] for key in fixture_gate.TOP_LEVEL_KEYS}
            malformed_values.append(malformed_top)
            for value in malformed_values:
                first = fixture_gate.validate_result_document(value)
                second = fixture_gate.validate_result_document(value)
                self.assertTrue(first)
                self.assertEqual(first, second)

    def test_acc_004_validator_recomputes_strict_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            self.rewrite_meta(active, "2099-01-01T00:00:00Z", "2020-01-01T00:00:00Z")
            stale = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            stale["status"] = "PASS"
            stale["exit_code"] = 0
            stale["capability"] = "FRESH_FIXTURE_GATE"
            self.assertIn("derived terminal", fixture_gate.validate_result_document(stale))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            valid = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            for mutate in (
                lambda value: (
                    value["totals"].__setitem__("valid_triplets", 0),
                    value["domains"][0].__setitem__("valid_triplets", 0),
                ),
                lambda value: value["domains"][0].__setitem__("source_freshness", "stale"),
                lambda value: value["domains"][0].__setitem__("selected_report", None),
            ):
                poisoned = json.loads(json.dumps(valid))
                mutate(poisoned)
                self.assertTrue(fixture_gate.validate_result_document(poisoned))

    def test_acc_006_normalized_review_status_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            meta = active / "snapshots" / "GET-example.meta.yaml"
            meta.write_text(
                meta.read_text(encoding="utf-8").replace(
                    "review_status: reviewed", "review_status: pending"
                ),
                encoding="utf-8",
            )
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertEqual((result["status"], result["exit_code"]), ("STALE", 3))
            self.assertIn("REVIEW_PENDING", {item["reason"] for item in result["issues"]})

    def test_acc_007_duplicate_report_fields_are_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            report = next((active / "reports").glob("*-replay.md"))
            report.write_text(
                report.read_text(encoding="utf-8") + "status: PASS\nsource: conflicting\n",
                encoding="utf-8",
            )
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertEqual((result["status"], result["exit_code"]), ("STALE", 3))
            self.assertIn("REPORT_MALFORMED", {item["reason"] for item in result["issues"]})

    def test_acc_008_output_boundary_sanitizes_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            raw_domain = "user:pass@example.test?token=SECRET#fragment"
            self.make_site(root, raw_domain)
            result = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.OFFLINE,
            )
            serialized = result.serialize()
            for secret in ("SECRET", "user:pass", "token=", "cookie=", "https://"):
                self.assertNotIn(secret, serialized)
            self.assertEqual(result.to_dict()["domains"], [])
            unsafe = [item for item in result.to_dict()["issues"] if item["reason"] == "UNSAFE_DOMAIN"]
            self.assertEqual(unsafe[0]["domain"], fixture_gate._unsafe_domain_identifier(raw_domain))
            self.assertEqual(fixture_gate.validate_result_document(result.to_dict()), [])

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    sys,
                    "argv",
                    ["validate_fixtures.py", str(root), "--domain", raw_domain],
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(validate_fixtures.main(), 2)
            self.assertNotIn("SECRET", stderr.getvalue())
            self.assertNotIn("user:pass", stderr.getvalue())

    def test_acc_009_exact_integer_and_repository_path_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            valid = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()

            integer_poisons = []
            for schema_version in (True, 1.0):
                poisoned = json.loads(json.dumps(valid))
                poisoned["schema_version"] = schema_version
                integer_poisons.append(poisoned)
            for exit_code in (True, 0.0):
                poisoned = json.loads(json.dumps(valid))
                poisoned["exit_code"] = exit_code
                integer_poisons.append(poisoned)
            for key in fixture_gate.TOTAL_KEYS:
                for value in (True, float(valid["totals"][key])):
                    poisoned = json.loads(json.dumps(valid))
                    poisoned["totals"][key] = value
                    integer_poisons.append(poisoned)
            domain_integer_keys = (
                "request_files",
                "response_files",
                "metadata_files",
                "complete_triplets",
                "valid_triplets",
                "structure_issue_count",
                "freshness_issue_count",
            )
            for key in domain_integer_keys:
                for value in (True, float(valid["domains"][0][key])):
                    poisoned = json.loads(json.dumps(valid))
                    poisoned["domains"][0][key] = value
                    integer_poisons.append(poisoned)
            for key in ("total", "replayed"):
                for value in (True, 1.0):
                    poisoned = json.loads(json.dumps(valid))
                    poisoned["domains"][0]["selected_report"][key] = value
                    integer_poisons.append(poisoned)
            for poison in integer_poisons:
                self.assertTrue(fixture_gate.validate_result_document(poison))

            unsafe_paths = (
                "",
                ".",
                "..",
                "../outside",
                "a/../outside",
                "/absolute",
                "C:/absolute",
                "a\\outside",
                "a//outside",
                "./outside",
            )
            for path in unsafe_paths:
                domain_poison = json.loads(json.dumps(valid))
                domain_poison["domains"][0]["selected_root"] = path
                self.assertTrue(fixture_gate.validate_result_document(domain_poison))
                report_poison = json.loads(json.dumps(valid))
                report_poison["domains"][0]["selected_report"]["path"] = path
                self.assertTrue(fixture_gate.validate_result_document(report_poison))

            active = root / "example.test" / "fixtures" / "active"
            self.rewrite_meta(active, "2099-01-01T00:00:00Z", "2020-01-01T00:00:00Z")
            refresh = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.REFRESH
            ).to_dict()
            for path in unsafe_paths:
                issue_poison = json.loads(json.dumps(refresh))
                issue_poison["issues"][0]["selected_root"] = path
                self.assertTrue(fixture_gate.validate_result_document(issue_poison))
                task_poison = json.loads(json.dumps(refresh))
                task_poison["refresh_tasks"][0]["selected_root"] = path
                self.assertTrue(fixture_gate.validate_result_document(task_poison))

            out = Path(tmp) / "refresh.json"
            with mock.patch.object(fixture_gate, "REPO_ROOT", Path(tmp)):
                published = fixture_gate.run_gate(
                    site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.REFRESH, out=out
                ).to_dict()
            for path in unsafe_paths:
                artifact_poison = json.loads(json.dumps(published))
                artifact_poison["artifact"]["path"] = path
                self.assertTrue(fixture_gate.validate_result_document(artifact_poison))

    def test_r5_rework_f001_through_f009(self) -> None:
        # F001: a synthetic post-commit os.close failure must not leak the owned fd.
        with tempfile.TemporaryDirectory() as tmp:
            trusted = Path(tmp)
            root = trusted / "sites"
            self.make_site(root)
            out_parent = trusted / "artifacts"
            out_parent.mkdir()
            out = out_parent / "refresh.json"
            before_fds = len(os.listdir("/dev/fd"))
            real_close = fixture_gate.os.close
            real_commit = fixture_gate._rename_commit
            committed = False
            injected = False

            def commit(parent_fd: int, source: str, target: str) -> None:
                nonlocal committed
                real_commit(parent_fd, source, target)
                committed = True

            def close(fd: int) -> None:
                nonlocal injected
                if committed and not injected:
                    injected = True
                    real_close(fd)
                    raise OSError("synthetic post-commit close after descriptor close")
                real_close(fd)

            with (
                mock.patch.object(fixture_gate, "REPO_ROOT", trusted),
                mock.patch.object(fixture_gate, "_rename_commit", side_effect=commit),
                mock.patch.object(fixture_gate.os, "close", side_effect=close),
            ):
                published = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=out,
                ).to_dict()
            self.assertTrue(injected)
            self.assertIsNotNone(published["artifact"])
            self.assertEqual(len(os.listdir("/dev/fd")), before_fds)

        # F002: a healthy domain cannot mask a selected empty domain in strict mode.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root, "healthy.test")
            (root / "empty.test" / "fixtures" / "active" / "snapshots").mkdir(parents=True)
            mixed = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertEqual((mixed["status"], mixed["exit_code"]), ("NO_DATA", 4))
            self.assertIn("NO_COMPLETE_TRIPLETS", {item["reason"] for item in mixed["issues"]})
            self.assertEqual(
                fixture_gate.validate_result_document(mixed, expected_site_root=root), []
            )

        # F003: canonical and even partial bare claims are mutually exclusive.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            canonical = {
                "status": "PASS", "exit_code": 0, "total": 1, "selected": 1,
                "replayed": 1, "compared": 1, "fatal_error_count": 0,
                "status_mismatch_count": 0, "no_data": False, "consistency_rate": 1.0,
                "threshold": 0.95, "failure_kind": None,
                "report_artifact": "reports/2026-07-16-replay.md",
                "trend_artifact": "reports/trend.json", "comparable_fields": 1,
                "matched_fields": 1, "structure_ok": 1, "empty_snapshot_count": 0,
            }
            report = next((active / "reports").glob("*-replay.md"))
            report.write_text(
                "## Canonical Result\n\n```json\n"
                + json.dumps(canonical, separators=(",", ":"))
                + "\n```\nstatus: PASS\n",
                encoding="utf-8",
            )
            dual = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertIn("REPORT_MALFORMED", {item["reason"] for item in dual["issues"]})

        # F004/F005: exact root binding and offline evidence are validator invariants.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            strict = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            forged = json.loads(json.dumps(strict))
            forged["domains"][0]["selected_root"] = "forged/" + forged["domains"][0]["selected_root"]
            forged["domains"][0]["selected_report"]["path"] = (
                "forged/" + forged["domains"][0]["selected_report"]["path"]
            )
            self.assertIn(
                "domain selected_root binding",
                fixture_gate.validate_result_document(forged, expected_site_root=root),
            )
            offline = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            poisoned_offline = json.loads(json.dumps(offline))
            poisoned_offline["totals"]["freshness_issue_count"] = 1
            poisoned_offline["domains"][0]["freshness_issue_count"] = 1
            self.assertIn(
                "offline freshness evidence",
                fixture_gate.validate_result_document(poisoned_offline, expected_site_root=root),
            )

        # F006: booleans are unquoted literals and expires_at is always scalar.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            self.rewrite_meta(active, "sensitive: false", 'sensitive: "false"')
            quoted = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertIn("META_BOOL_INVALID", {item["reason"] for item in quoted["issues"]})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            self.rewrite_meta(
                active, "expires_at: 2099-01-01T00:00:00Z", "expires_at:\n  - 2099-01-01T00:00:00Z"
            )
            container = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            self.assertIn("META_UNREADABLE", {item["reason"] for item in container["issues"]})

        # F007/F008: raw invalid mode anywhere is diagnostic; empty out is explicit invalid.
        for argv, expected_mode in (
            (["--mode", "strict", "--mode", "invalid"], "diagnostic"),
            (["--mode", "refresh", "--out="], "refresh"),
        ):
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = fixture_gate.cli_main("validate_fixtures", argv)
            value = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 2)
            self.assertEqual((value["status"], value["mode"]), ("INVALID_ARGUMENT", expected_mode))

        # F009: the governance record reflects the corrected passing command set.
        impact = (REPO_ROOT / "站点经验库/local-governance.fixture/impact-regression.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "required_regression: focused F014 forged unpublished refresh plus contextual positive/negative tests, full replayer tests, workflow shell tests, and low-loop package-validator tests",
            impact,
        )
        self.assertIn(
            "| 2026-07-17 | LL-0004-R7 | focused F014 forged unpublished refresh plus contextual positive/negative tests, full replayer regressions, workflow shell tests, and low-loop package-validator tests | pass | external Fresh acceptance remains separate; historical invocation identity remains unverified |",
            impact,
        )
        self.assertNotIn("external-temp score gate mislocates repository root", impact)

    def test_r3_f001_report_coverage_and_selected_root_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            write_report(active, total=2, replayed=2)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertEqual((result["status"], result["exit_code"]), ("STALE", 3))
            self.assertIn("REPORT_COVERAGE_MISMATCH", {item["reason"] for item in result["issues"]})

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            valid = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            coverage = json.loads(json.dumps(valid))
            coverage["domains"][0]["selected_report"]["total"] = 2
            coverage["domains"][0]["selected_report"]["replayed"] = 2
            self.assertTrue(fixture_gate.validate_result_document(coverage))
            selected_root = valid["domains"][0]["selected_root"]
            invalid_paths = (
                f"{selected_root}/outside-replay.md",
                f"{selected_root}/reports/nested/run-replay.md",
                f"other.test/fixtures/active/reports/run-replay.md",
                f"{selected_root}/reports/run.md",
            )
            for path in invalid_paths:
                poisoned = json.loads(json.dumps(valid))
                poisoned["domains"][0]["selected_report"]["path"] = path
                self.assertTrue(fixture_gate.validate_result_document(poisoned))

    def test_r5_publication_platform_probe_and_linearization(self) -> None:
        for existing in (False, True):
            with self.subTest(normal_publish_existing=existing), tempfile.TemporaryDirectory() as tmp:
                trusted = Path(tmp)
                root = trusted / "sites"
                self.make_site(root)
                parent = trusted / "artifacts"
                parent.mkdir()
                out = parent / "refresh.json"
                old = b"owner bytes\n"
                if existing:
                    out.write_bytes(old)
                with mock.patch.object(fixture_gate, "REPO_ROOT", trusted):
                    result = fixture_gate.run_gate(
                        site_root=root,
                        tool="validate_fixtures",
                        mode=fixture_gate.Mode.REFRESH,
                        out=out,
                    ).to_dict()
                self.assertIsNotNone(result["artifact"])
                self.assertTrue(out.is_file())
                self.assertNotEqual(out.read_bytes(), old)

        class FaultyHandle:
            def __init__(self, handle: object, operation: str) -> None:
                self.handle = handle
                self.operation = operation

            def write(self, value: bytes) -> int:
                if self.operation == "write":
                    raise OSError("write")
                return self.handle.write(value)

            def flush(self) -> None:
                if self.operation == "flush":
                    raise OSError("flush")
                self.handle.flush()

            def read(self) -> bytes:
                value = self.handle.read()
                return b"wrong" if self.operation == "verify" else value

            def fileno(self) -> int:
                return self.handle.fileno()

            def close(self) -> None:
                self.handle.close()

        fault_names = (
            "serialize",
            "stage",
            "write_fdopen",
            "write",
            "flush",
            "file_fsync",
            "verify_fdopen",
            "verify_bytes",
            "final_validation",
            "cleanup_retry",
            "before_rename",
        )
        for existing in (False, True):
            for fault in fault_names:
                with self.subTest(existing=existing, fault=fault), tempfile.TemporaryDirectory() as tmp:
                    trusted = Path(tmp)
                    root = trusted / "sites"
                    self.make_site(root)
                    parent = trusted / "artifacts"
                    parent.mkdir()
                    out = parent / "refresh.json"
                    old = b"owner bytes\n"
                    if existing:
                        out.write_bytes(old)
                    before_fds = len(os.listdir("/dev/fd")) if Path("/dev/fd").is_dir() else None
                    original_owned = fixture_gate._fdopen_owned
                    owned_calls = 0
                    fsync_calls = 0
                    validate_calls = 0
                    temp_unlink_calls = 0
                    original_fsync = fixture_gate.os.fsync
                    original_validate = fixture_gate._validate_output_chain
                    original_unlink = fixture_gate.os.unlink

                    def owned(fd: int, mode: str) -> object:
                        nonlocal owned_calls
                        owned_calls += 1
                        if fault == "write_fdopen" and owned_calls == 1:
                            raise OSError("fdopen")
                        if fault == "verify_fdopen" and owned_calls == 2:
                            raise OSError("fdopen")
                        handle = original_owned(fd, mode)
                        if owned_calls == 1 and fault in {"write", "flush"}:
                            return FaultyHandle(handle, fault)
                        if owned_calls == 2 and fault == "verify_bytes":
                            return FaultyHandle(handle, "verify")
                        return handle

                    def staged_fsync(fd: int) -> None:
                        nonlocal fsync_calls
                        fsync_calls += 1
                        if fault == "file_fsync" and fsync_calls == 2:
                            raise OSError("fsync")
                        original_fsync(fd)

                    def validate(*args: object) -> None:
                        nonlocal validate_calls
                        validate_calls += 1
                        if fault in {"final_validation", "cleanup_retry"} and validate_calls == 4:
                            raise OSError("final validation")
                        original_validate(*args)

                    def unlink(name: object, *args: object, **kwargs: object) -> None:
                        nonlocal temp_unlink_calls
                        if fault == "cleanup_retry" and str(name).endswith(".tmp"):
                            temp_unlink_calls += 1
                            if temp_unlink_calls == 1:
                                raise OSError("retry cleanup")
                        original_unlink(name, *args, **kwargs)

                    with contextlib.ExitStack() as stack:
                        stack.enter_context(mock.patch.object(fixture_gate, "REPO_ROOT", trusted))
                        if fault == "serialize":
                            stack.enter_context(mock.patch.object(fixture_gate, "_artifact_bytes", side_effect=ValueError("serialize")))
                        elif fault == "stage":
                            stack.enter_context(mock.patch.object(fixture_gate, "_create_temp_at", side_effect=OSError("stage")))
                        elif fault in {"write_fdopen", "write", "flush", "verify_fdopen", "verify_bytes"}:
                            stack.enter_context(mock.patch.object(fixture_gate, "_fdopen_owned", side_effect=owned))
                        elif fault == "file_fsync":
                            stack.enter_context(mock.patch.object(fixture_gate.os, "fsync", side_effect=staged_fsync))
                        elif fault in {"final_validation", "cleanup_retry"}:
                            stack.enter_context(mock.patch.object(fixture_gate, "_validate_output_chain", side_effect=validate))
                            if fault == "cleanup_retry":
                                stack.enter_context(mock.patch.object(fixture_gate.os, "unlink", side_effect=unlink))
                        else:
                            stack.enter_context(mock.patch.object(fixture_gate, "_rename_commit", side_effect=OSError("rename")))
                        failed = fixture_gate.run_gate(
                            site_root=root,
                            tool="validate_fixtures",
                            mode=fixture_gate.Mode.REFRESH,
                            out=out,
                        ).to_dict()

                    self.assertEqual((failed["status"], failed["exit_code"]), ("INTERNAL_ERROR", 5))
                    self.assertIsNone(failed["artifact"])
                    if existing:
                        self.assertEqual(out.read_bytes(), old)
                    else:
                        self.assertFalse(out.exists())
                    self.assertEqual(list(parent.glob(".refresh.json.*.tmp")), [])
                    if before_fds is not None:
                        self.assertEqual(len(os.listdir("/dev/fd")), before_fds)

        with tempfile.TemporaryDirectory() as tmp:
            trusted = Path(tmp)
            root = trusted / "sites"
            self.make_site(root)
            parent = trusted / "artifacts"
            parent.mkdir()
            out = parent / "refresh.json"
            original_close = fixture_gate._close_raw_fd

            def close_after_commit(fd: int, *, committed: bool) -> None:
                original_close(fd, committed=committed)
                if committed:
                    raise OSError("post-commit close")

            with (
                mock.patch.object(fixture_gate, "REPO_ROOT", trusted),
                mock.patch.object(fixture_gate, "_close_raw_fd", side_effect=close_after_commit),
            ):
                committed_result = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=out,
                ).to_dict()
            self.assertIsNotNone(committed_result["artifact"])
            self.assertTrue(out.is_file())

        for fault in (errno.EINTR, errno.EIO):
            with self.subTest(rename_errno=fault), tempfile.TemporaryDirectory() as tmp:
                trusted = Path(tmp)
                root = trusted / "sites"
                self.make_site(root)
                parent = trusted / "artifacts"
                parent.mkdir()
                out = parent / "refresh.json"
                old = b"owner bytes\n"
                out.write_bytes(old)
                with (
                    mock.patch.object(fixture_gate, "REPO_ROOT", trusted),
                    mock.patch.object(
                        fixture_gate,
                        "_rename_commit",
                        side_effect=fixture_gate.PublicationStop(f"rename errno {fault}"),
                    ),
                    self.assertRaises(fixture_gate.PublicationStop),
                ):
                    fixture_gate.run_gate(
                        site_root=root,
                        tool="validate_fixtures",
                        mode=fixture_gate.Mode.REFRESH,
                        out=out,
                    )
                self.assertEqual(out.read_bytes(), old)
                self.assertEqual(list(parent.glob(".refresh.json.*.tmp")), [])

        for depth in ("parent", "grandparent"):
            for phase in ("before_temp", "after_temp", "before_commit", "after_commit"):
                with self.subTest(depth=depth, phase=phase), tempfile.TemporaryDirectory() as tmp:
                    trusted = Path(tmp)
                    root = trusted / "sites"
                    self.make_site(root)
                    grand = trusted / "grand"
                    parent = grand / "parent"
                    parent.mkdir(parents=True)
                    out = parent / "refresh.json"
                    old = b"owner bytes\n"
                    out.write_bytes(old)
                    outside = trusted / "outside"
                    outside.mkdir()
                    replaced = False

                    def replace_ancestor() -> None:
                        nonlocal replaced
                        if replaced:
                            return
                        replaced = True
                        if depth == "parent":
                            parent.rename(grand / "parent-original")
                            parent.symlink_to(outside, target_is_directory=True)
                        else:
                            grand.rename(trusted / "grand-original")
                            grand.symlink_to(outside, target_is_directory=True)

                    original_create = fixture_gate._create_temp_at
                    original_commit = fixture_gate._rename_commit

                    def create_before(parent_fd: int, target_name: str) -> tuple[int, str]:
                        replace_ancestor()
                        return original_create(parent_fd, target_name)

                    def create_after(parent_fd: int, target_name: str) -> tuple[int, str]:
                        made = original_create(parent_fd, target_name)
                        replace_ancestor()
                        return made

                    def commit_race(parent_fd: int, source: str, target: str) -> None:
                        if phase == "before_commit":
                            replace_ancestor()
                        original_commit(parent_fd, source, target)
                        if phase == "after_commit":
                            replace_ancestor()

                    with contextlib.ExitStack() as stack:
                        stack.enter_context(mock.patch.object(fixture_gate, "REPO_ROOT", trusted))
                        if phase == "before_temp":
                            stack.enter_context(mock.patch.object(fixture_gate, "_create_temp_at", side_effect=create_before))
                        elif phase == "after_temp":
                            stack.enter_context(mock.patch.object(fixture_gate, "_create_temp_at", side_effect=create_after))
                        elif phase == "before_commit":
                            stack.enter_context(mock.patch.object(fixture_gate, "_rename_commit", side_effect=commit_race))
                        else:
                            stack.enter_context(mock.patch.object(fixture_gate, "_rename_commit", side_effect=commit_race))
                        result = fixture_gate.run_gate(
                            site_root=root,
                            tool="validate_fixtures",
                            mode=fixture_gate.Mode.REFRESH,
                            out=out,
                        ).to_dict()

                    owner = (
                        grand / "parent-original" / "refresh.json"
                        if depth == "parent"
                        else trusted / "grand-original" / "parent" / "refresh.json"
                    )
                    self.assertTrue(replaced)
                    self.assertFalse(any(outside.rglob("*")))
                    if phase in {"before_temp", "after_temp"}:
                        self.assertEqual((result["status"], result["exit_code"]), ("INTERNAL_ERROR", 5))
                        self.assertIsNone(result["artifact"])
                        self.assertEqual(owner.read_bytes(), old)
                    else:
                        self.assertIsNotNone(result["artifact"])
                        self.assertNotEqual(owner.read_bytes(), old)
                    self.assertEqual(list(owner.parent.glob(".refresh.json.*.tmp")), [])

    def rewrite_meta(self, active: Path, old: str, new: str) -> None:
        path = active / "snapshots" / "GET-example.meta.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_r5_metadata_and_report_profiles(self) -> None:
        now = fixture_gate.dt.datetime(2026, 7, 16, tzinfo=fixture_gate.dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            report = next((active / "reports").glob("*-replay.md"))
            canonical = {
                "status": "PASS",
                "exit_code": 0,
                "total": 1,
                "selected": 1,
                "replayed": 1,
                "compared": 1,
                "fatal_error_count": 0,
                "status_mismatch_count": 0,
                "no_data": False,
                "consistency_rate": 1.0,
                "threshold": 0.95,
                "failure_kind": None,
                "report_artifact": "reports/2026-07-16-replay.md",
                "trend_artifact": "reports/trend.json",
                "comparable_fields": 2,
                "matched_fields": 2,
                "structure_ok": 1,
                "empty_snapshot_count": 0,
            }
            report.write_text(
                "# Replay evidence\n\n## Canonical Result\n\n```json\n"
                + json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
                + "\n```\n\nProducer: consistency_report.\n",
                encoding="utf-8",
            )
            strict = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT, now=now
            ).to_dict()
            self.assertEqual((strict["status"], strict["exit_code"]), ("PASS", 0))
            self.assertEqual(strict["domains"][0]["selected_report"]["source"], "consistency_report")

            older = report.with_name("2026-07-15-replay.md")
            older.write_text("status: PASS\ntotal: 1\nreplayed: 1\nsource: older\n", encoding="utf-8")
            report.write_text("status: FAIL\ntotal: 1\nreplayed: 1\nsource: newest\n", encoding="utf-8")
            failed = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT, now=now
            ).to_dict()
            self.assertIn("REPORT_NOT_PASS", {item["reason"] for item in failed["issues"]})
            self.assertIsNone(failed["domains"][0]["selected_report"])

            report.write_text("status: PASS\ntotal: 1\nreplayed: 1\nsource: newest\n", encoding="utf-8")
            future = report.with_name("2026-07-17-replay.md")
            future.write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
            future_result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT, now=now
            ).to_dict()
            self.assertIn("REPORT_STALE", {item["reason"] for item in future_result["issues"]})

    def test_r5_exact_artifact_payload_metadata_block_and_surrogate_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trusted = Path(tmp)
            root = trusted / "sites"
            active = self.make_site(root)
            meta = active / "snapshots" / "GET-example.meta.yaml"
            meta.write_text(meta.read_text(encoding="utf-8") + "notes: |\n  reviewed by owner\n", encoding="utf-8")
            out_parent = trusted / "artifacts"
            out_parent.mkdir()
            out = out_parent / "refresh.json"
            with mock.patch.object(fixture_gate, "REPO_ROOT", trusted):
                returned = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=out,
                ).to_dict()
            committed = json.loads(json.dumps(returned))
            committed["artifact"] = None
            expected = (fixture_gate.serialize_result(committed) + "\n").encode("utf-8")
            self.assertEqual(out.read_bytes(), expected)
            self.assertEqual(returned["artifact"]["sha256"], fixture_gate.hashlib.sha256(expected).hexdigest())
            self.assertEqual(returned["artifact"]["path"], "artifacts/refresh.json")

            self.rewrite_meta(active, "reviewed by owner", "TODO review")
            strict = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertIn("REVIEW_PENDING", {item["reason"] for item in strict["issues"]})
            offline = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
            ).to_dict()
            self.assertNotIn("REVIEW_PENDING", {item["reason"] for item in offline["issues"]})
            self.assertEqual(offline["domains"][0]["valid_triplets"], 1)

        if os.name == "posix":
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "sites"
                raw = b"\xff.fixture".decode("utf-8", "surrogateescape")
                physical = "bad:domain.fixture"
                self.make_site(root, physical)
                result = fixture_gate.run_gate(
                    site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.OFFLINE
                ).to_dict()
                self.assertEqual(result["domains"], [])
                unsafe = [item for item in result["issues"] if item["reason"] == "UNSAFE_DOMAIN"]
                self.assertEqual(unsafe[0]["domain"], fixture_gate._unsafe_domain_identifier(physical))
                self.assertEqual(
                    fixture_gate._unsafe_domain_identifier(raw),
                    "domain-sha256-" + fixture_gate.hashlib.sha256(os.fsencode(raw)).hexdigest()[:16],
                )
                self.assertEqual(fixture_gate.validate_result_document(result), [])

    def test_report_stale_and_offline_freshness_boundary(self) -> None:
        now = fixture_gate.dt.datetime(2026, 7, 16, tzinfo=fixture_gate.dt.timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            active = self.make_site(root)
            self.rewrite_meta(active, "2099-01-01T00:00:00Z", "2020-01-01T00:00:00Z")
            report = next((active / "reports").glob("*-replay.md"))
            old = (now - fixture_gate.dt.timedelta(days=31)).timestamp()
            os.utime(report, (old, old))
            strict = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.STRICT,
                now=now,
            ).to_dict()
            self.assertNotIn("REPORT_STALE", {item["reason"] for item in strict["issues"]})
            self.assertIn("EXPIRED", {item["reason"] for item in strict["issues"]})
            report.rename(report.with_name("2026-06-01-replay.md"))
            strict = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT, now=now
            ).to_dict()
            self.assertIn("REPORT_STALE", {item["reason"] for item in strict["issues"]})
            offline = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.OFFLINE,
                now=now,
            ).to_dict()
            self.assertEqual((offline["status"], offline["capability"]), ("STRUCTURE_ONLY", "STRUCTURE_ONLY"))
            self.assertFalse(offline["freshness_checked"])
            self.assertEqual(offline["replay_lineage"], "NOT_CHECKED")
            self.assertEqual(offline["totals"]["freshness_issue_count"], 0)

    def test_exact_schema_validator_rejects_poison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            valid = fixture_gate.run_gate(
                site_root=root,
                tool="validate_fixtures",
                mode=fixture_gate.Mode.STRICT,
            ).to_dict()
            self.assertEqual(fixture_gate.validate_result_document(valid), [])
            poisons = []
            added = json.loads(json.dumps(valid))
            added["extra"] = True
            poisons.append(added)
            negative = json.loads(json.dumps(valid))
            negative["totals"]["complete_triplets"] = -1
            poisons.append(negative)
            mismatch = json.loads(json.dumps(valid))
            mismatch["domains"][0]["valid_triplets"] = 2
            poisons.append(mismatch)
            wrong_terminal = json.loads(json.dumps(valid))
            wrong_terminal["capability"] = "DIAGNOSTIC_ONLY"
            poisons.append(wrong_terminal)
            for poison in poisons:
                self.assertTrue(fixture_gate.validate_result_document(poison))

    def test_both_legacy_strict_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            commands = (
                [sys.executable, str(REPLAYER_DIR / "validate_fixtures.py"), str(root), "--strict-review"],
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/web_h5/fixture_freshness_report.py"),
                    str(root),
                    "--strict-fresh",
                ],
            )
            for command in commands:
                completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result = json.loads(completed.stdout)
                self.assertEqual((result["mode"], result["capability"]), ("strict", "FRESH_FIXTURE_GATE"))
                self.assertEqual(fixture_gate.validate_result_document(result), [])

    def test_cli_alias_conflict_and_help_are_one_json_document(self) -> None:
        for argv in (
            ["validate_fixtures.py", "--strict-review", "--mode", "offline"],
            ["validate_fixtures.py", "--help"],
        ):
            with self.subTest(argv=argv), mock.patch.object(sys, "argv", argv):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    self.assertEqual(validate_fixtures.main(), 2)
                result = json.loads(stdout.getvalue())
                self.assertEqual(result["status"], "INVALID_ARGUMENT")
                self.assertEqual(fixture_gate.validate_result_document(result), [])
                self.assertTrue(stderr.getvalue())

    def test_refresh_artifact_failures_are_atomic_and_rerunnable(self) -> None:
        class FlushFailure:
            def __init__(self, handle: object) -> None:
                self.handle = handle

            def __enter__(self) -> "FlushFailure":
                return self

            def __exit__(self, *args: object) -> None:
                self.handle.close()

            def write(self, value: bytes) -> int:
                return self.handle.write(value)

            def flush(self) -> None:
                raise OSError("flush")

            def fileno(self) -> int:
                return self.handle.fileno()

            def close(self) -> None:
                self.handle.close()

        failures = ("stage", "open", "serialize", "flush", "fsync", "replace")
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "sites"
                self.make_site(root)
                out = Path(tmp) / "refresh.json"
                old = b"owner bytes\n"
                out.write_bytes(old)
                original_fdopen = fixture_gate.os.fdopen
                if failure == "stage":
                    patcher = mock.patch.object(fixture_gate, "_create_temp_at", side_effect=OSError("stage"))
                elif failure == "open":
                    patcher = mock.patch.object(fixture_gate.os, "fdopen", side_effect=OSError("open"))
                elif failure == "serialize":
                    patcher = mock.patch.object(fixture_gate, "_artifact_bytes", side_effect=ValueError("serialize"))
                elif failure == "flush":
                    patcher = mock.patch.object(
                        fixture_gate.os,
                        "fdopen",
                        side_effect=lambda fd, mode: FlushFailure(original_fdopen(fd, mode)),
                    )
                elif failure == "fsync":
                    patcher = mock.patch.object(fixture_gate.os, "fsync", side_effect=OSError("fsync"))
                else:
                    patcher = mock.patch.object(fixture_gate, "_rename_commit", side_effect=OSError("replace"))
                with mock.patch.object(fixture_gate, "REPO_ROOT", Path(tmp)), patcher:
                    failed = fixture_gate.run_gate(
                        site_root=root,
                        tool="validate_fixtures",
                        mode=fixture_gate.Mode.REFRESH,
                        out=out,
                    ).to_dict()
                self.assertEqual((failed["status"], failed["exit_code"]), ("INTERNAL_ERROR", 5))
                self.assertIsNone(failed["artifact"])
                self.assertEqual(out.read_bytes(), old)
                self.assertEqual(list(out.parent.glob(f".{out.name}.*.tmp")), [])
                with mock.patch.object(fixture_gate, "REPO_ROOT", Path(tmp)):
                    rerun = fixture_gate.run_gate(
                        site_root=root,
                        tool="validate_fixtures",
                        mode=fixture_gate.Mode.REFRESH,
                        out=out,
                    ).to_dict()
                    validation = fixture_gate.validate_result_document(rerun, expected_out=out)
                self.assertEqual(rerun["status"], "PASS")
                self.assertEqual(rerun["artifact"]["sha256"], fixture_gate.hashlib.sha256(out.read_bytes()).hexdigest())
                self.assertEqual(validation, [])

    def test_f010_ambiguous_raw_close_never_probes_or_recloses_fd(self) -> None:
        calls: list[object] = []

        def ambiguous_close(fd: int) -> None:
            calls.append(fd)
            raise OSError(errno.EINTR, "interrupted")

        with (
            mock.patch.object(fixture_gate.os, "close", side_effect=ambiguous_close),
            mock.patch.object(fixture_gate.os, "fstat", side_effect=AssertionError("numeric fd probed")),
            mock.patch.object(
                fixture_gate.os, "closerange", side_effect=AssertionError("numeric fd reclosed")
            ),
            self.assertRaises(fixture_gate.PublicationStop),
        ):
            fixture_gate._close_raw_fd(41, committed=False)
        self.assertEqual(calls, [41])

    def test_f011_file_object_close_failure_retains_raw_ownership(self) -> None:
        class CloseFailure:
            def close(self) -> None:
                raise OSError("synthetic file-object close")

        closed: list[int] = []
        with mock.patch.object(fixture_gate.os, "close", side_effect=closed.append):
            with self.assertRaises(OSError):
                fixture_gate._close_file_owned(CloseFailure(), 42)
        self.assertEqual(closed, [42])

        read_fd, write_fd = os.pipe()
        try:
            handle = fixture_gate._fdopen_owned(write_fd, "wb")
            self.assertEqual(handle.fileno(), write_fd)
            handle.close()
            os.fstat(write_fd)
        finally:
            os.close(read_fd)
            os.close(write_fd)

        class PublicationCloseFailure:
            def __init__(self, handle: object) -> None:
                self.handle = handle

            def write(self, value: bytes) -> int:
                return self.handle.write(value)

            def flush(self) -> None:
                self.handle.flush()

            def close(self) -> None:
                raise OSError("synthetic file-object close")

        if Path("/dev/fd").is_dir():
            with tempfile.TemporaryDirectory() as tmp:
                trusted = Path(tmp)
                root = trusted / "sites"
                self.make_site(root)
                (trusted / "artifacts").mkdir()
                before_fds = len(os.listdir("/dev/fd"))
                original_owned = fixture_gate._fdopen_owned
                for _ in range(3):
                    calls = 0

                    def owned(fd: int, mode: str) -> object:
                        nonlocal calls
                        calls += 1
                        handle = original_owned(fd, mode)
                        return PublicationCloseFailure(handle) if calls == 1 else handle

                    with (
                        mock.patch.object(fixture_gate, "REPO_ROOT", trusted),
                        mock.patch.object(fixture_gate, "_fdopen_owned", side_effect=owned),
                    ):
                        result = fixture_gate.run_gate(
                            site_root=root,
                            tool="validate_fixtures",
                            mode=fixture_gate.Mode.REFRESH,
                            out=trusted / "artifacts" / "refresh.json",
                        ).to_dict()
                    self.assertEqual(result["status"], "INTERNAL_ERROR")
                    self.assertIsNone(result["artifact"])
                    self.assertEqual(len(os.listdir("/dev/fd")), before_fds)

    def test_f012_engine_binds_alternate_site_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as tmp:
            root = Path(tmp) / "alternate-sites"
            self.make_site(root)
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.STRICT
            ).to_dict()
            self.assertEqual((result["status"], result["exit_code"]), ("PASS", 0))
            self.assertEqual(
                fixture_gate.validate_result_document(result, expected_site_root=root), []
            )

    def test_f013_any_empty_out_occurrence_is_invalid(self) -> None:
        for argv in (
            ["--mode", "refresh", "--out=", "--out", "valid.json"],
            ["--mode", "refresh", "--out", "", "--out", "valid.json"],
            ["--mode", "refresh", "--out", "valid.json", "--out="],
        ):
            with self.subTest(argv=argv):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                    exit_code = fixture_gate.cli_main("validate_fixtures", argv)
                result = json.loads(stdout.getvalue())
                self.assertEqual(exit_code, 2)
                self.assertEqual(result["status"], "INVALID_ARGUMENT")
                self.assertIsNone(result["artifact"])

    def test_f014_artifact_requires_committed_refresh_result(self) -> None:
        cases = [
            fixture_gate.invalid_argument_result(
                "validate_fixtures", fixture_gate.Mode.REFRESH
            ).to_dict(),
            fixture_gate._internal_result(
                "validate_fixtures", fixture_gate.Mode.REFRESH
            ).to_dict(),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root)
            cases.append(
                fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.DIAGNOSTIC,
                ).to_dict()
            )
            unpublished = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.REFRESH
            ).to_dict()
            self.assertIsNone(unpublished["artifact"])
            cases.append(unpublished)
            for value in cases:
                value["artifact"] = {"path": "forged.json", "sha256": "0" * 64}
                self.assertIn(
                    "artifact publication state",
                    fixture_gate.validate_result_document(value, expected_site_root=root),
                )

    def test_f014_contextual_artifact_verifier_binds_expected_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trusted = Path(tmp)
            root = trusted / "sites"
            self.make_site(root)
            out = trusted / "artifacts" / "refresh.json"
            out.parent.mkdir()
            with mock.patch.object(fixture_gate, "REPO_ROOT", trusted):
                published = fixture_gate.run_gate(
                    site_root=root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=out,
                ).to_dict()
                self.assertIn(
                    "artifact publication state",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                    ),
                )
                self.assertEqual(
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                    [],
                )
                forged_path = json.loads(json.dumps(published))
                forged_path["artifact"]["path"] = "artifacts/elsewhere.json"
                self.assertIn(
                    "artifact publication path",
                    fixture_gate.validate_result_document(
                        forged_path,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                forged_digest = json.loads(json.dumps(published))
                forged_digest["artifact"]["sha256"] = "f" * 64
                self.assertIn(
                    "artifact publication digest",
                    fixture_gate.validate_result_document(
                        forged_digest,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                out.write_bytes(b"forged\n")
                self.assertIn(
                    "artifact publication bytes",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                out.unlink()
                self.assertIn(
                    "artifact publication state",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                out.symlink_to(root / "example.test" / "fixtures" / "active" / "reports", target_is_directory=True)
                self.assertIn(
                    "artifact publication state",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                out.unlink()
                out.mkdir()
                self.assertIn(
                    "artifact publication state",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                out.rmdir()
                wrong_payload = json.loads(json.dumps(published))
                wrong_payload["status"] = "RECERTIFICATION_REQUIRED"
                wrong_payload["exit_code"] = 3
                wrong_payload["capability"] = "REFRESH_PLAN"
                wrong_payload["issues"] = [
                    {
                        "scope": "FIXTURE",
                        "domain": "example.test",
                        "prefix": "GET-example",
                        "selected_root": published["domains"][0]["selected_root"],
                        "reason": "EXPIRED",
                    }
                ]
                wrong_payload["refresh_tasks"] = fixture_gate._tasks_for(wrong_payload["issues"])
                wrong_payload["totals"]["expired_count"] = 1
                wrong_payload["totals"]["freshness_issue_count"] = 1
                wrong_payload["totals"]["refresh_task_count"] = 1
                wrong_payload["domains"][0]["freshness_issue_count"] = 1
                wrong_payload["domains"][0]["source_freshness"] = "stale"
                wrong_payload["domains"][0]["selected_report"] = None
                out.write_bytes(fixture_gate._artifact_claim_bytes(wrong_payload))
                self.assertIn(
                    "artifact publication bytes",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )
                other_root = trusted / "other-sites"
                self.make_site(other_root, "other.test")
                other_out = trusted / "artifacts" / "other-refresh.json"
                other_published = fixture_gate.run_gate(
                    site_root=other_root,
                    tool="validate_fixtures",
                    mode=fixture_gate.Mode.REFRESH,
                    out=other_out,
                ).to_dict()
                out.write_bytes(fixture_gate._artifact_claim_bytes(other_published))
                self.assertIn(
                    "artifact publication bytes",
                    fixture_gate.validate_result_document(
                        published,
                        expected_site_root=root,
                        expected_out=out,
                    ),
                )

    def test_f015_issue_and_task_roots_bind_to_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sites"
            self.make_site(root, "a.test")
            self.make_site(root, "b.test")
            result = fixture_gate.run_gate(
                site_root=root, tool="validate_fixtures", mode=fixture_gate.Mode.REFRESH
            ).to_dict()
            forged_issue = json.loads(json.dumps(result))
            forged_issue["issues"] = [
                {
                    "scope": "REPORT",
                    "domain": "a.test",
                    "prefix": None,
                    "selected_root": forged_issue["domains"][1]["selected_root"],
                    "reason": "REPORT_STALE",
                }
            ]
            forged_issue["domains"][0]["freshness_issue_count"] = 1
            forged_issue["domains"][0]["source_freshness"] = "stale"
            forged_issue["domains"][0]["selected_report"] = None
            forged_issue["totals"]["freshness_issue_count"] = 1
            forged_issue["status"] = "RECERTIFICATION_REQUIRED"
            forged_issue["exit_code"] = 3
            forged_issue["capability"] = "REFRESH_PLAN"
            forged_issue["refresh_tasks"] = fixture_gate._tasks_for(forged_issue["issues"])
            forged_issue["totals"]["refresh_task_count"] = 1
            errors = fixture_gate.validate_result_document(
                forged_issue, expected_site_root=root
            )
            self.assertIn("issue selected_root binding", errors)
            self.assertIn("task selected_root binding", errors)


class WorkflowActualShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = (REPO_ROOT / ".github/workflows/consistency-replay.yml").read_text(encoding="utf-8")

    def extract(self, name: str) -> str:
        start = f"# {name}_START"
        end = f"# {name}_END"
        lines = self.workflow.splitlines()
        first = next(index for index, line in enumerate(lines) if line.strip() == start)
        last = next(index for index, line in enumerate(lines[first + 1 :], first + 1) if line.strip() == end)
        return textwrap.dedent("\n".join(lines[first + 1 : last])) + "\n"

    def checkout(self, root: Path, *, report_status: str) -> None:
        replayer = root / "tools" / "replayer"
        replayer.mkdir(parents=True)
        for name in ("fixture_layout.py", "fixture_gate.py", "validate_fixtures.py"):
            shutil.copy2(REPLAYER_DIR / name, replayer / name)
        active = root / "站点经验库" / "example.test" / "fixtures" / "active"
        write_snapshot(active / "snapshots")
        write_report(active, status=report_status)

    def run_shell(self, root: Path, block: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GITHUB_OUTPUT"] = str(root / "github-output.txt")
        return subprocess.run(
            ["bash", "-c", block],
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_actual_gate_validator_and_discovery_blocks(self) -> None:
        blocks = [
            self.extract("FIXTURE_GATE_SHELL"),
            self.extract("FIXTURE_GATE_RESULT_VALIDATOR_SHELL"),
            self.extract("REPLAY_DOMAIN_DISCOVERY_SHELL"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.checkout(root, report_status="PASS")
            for block in blocks:
                result = self.run_shell(root, block)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('domains_json=["example.test"]', (root / "github-output.txt").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.checkout(root, report_status="FAIL")
            gate = self.run_shell(root, blocks[0])
            self.assertEqual(gate.returncode, 0, gate.stderr)
            self.assertNotEqual(self.run_shell(root, blocks[1]).returncode, 0)
            self.assertNotEqual(self.run_shell(root, blocks[2]).returncode, 0)

    def test_acc_005_actual_workflow_rejects_duplicate_keys_and_non_finite_json(self) -> None:
        gate_block = self.extract("FIXTURE_GATE_SHELL")
        validator_block = self.extract("FIXTURE_GATE_RESULT_VALIDATOR_SHELL")
        discovery_block = self.extract("REPLAY_DOMAIN_DISCOVERY_SHELL")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.checkout(root, report_status="PASS")
            self.assertEqual(self.run_shell(root, gate_block).returncode, 0)
            gate_path = root / ".ci-out" / "fixture-gate.json"
            valid = gate_path.read_text(encoding="utf-8")
            poisons = (
                valid.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1),
                valid.replace(
                    '"domains_selected":1',
                    '"domains_selected":1,"domains_selected":1',
                    1,
                ),
                valid.replace('"exit_code":0', '"exit_code":NaN', 1),
                valid.replace('"exit_code":0', '"exit_code":Infinity', 1),
            )
            for poison in poisons:
                gate_path.write_text(poison, encoding="utf-8")
                self.assertNotEqual(self.run_shell(root, validator_block).returncode, 0)
                self.assertNotEqual(self.run_shell(root, discovery_block).returncode, 0)

    def test_acc_009_actual_workflow_rejects_types_and_paths(self) -> None:
        gate_block = self.extract("FIXTURE_GATE_SHELL")
        validator_block = self.extract("FIXTURE_GATE_RESULT_VALIDATOR_SHELL")
        discovery_block = self.extract("REPLAY_DOMAIN_DISCOVERY_SHELL")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.checkout(root, report_status="PASS")
            self.assertEqual(self.run_shell(root, gate_block).returncode, 0)
            gate_path = root / ".ci-out" / "fixture-gate.json"
            valid = json.loads(gate_path.read_text(encoding="utf-8"))
            poisons = []
            for key, value in (("schema_version", 1.0), ("schema_version", True)):
                poisoned = json.loads(json.dumps(valid))
                poisoned[key] = value
                poisons.append(poisoned)
            replayed_bool = json.loads(json.dumps(valid))
            replayed_bool["domains"][0]["selected_report"]["replayed"] = True
            poisons.append(replayed_bool)
            for location in ("selected_root",):
                for path in ("../outside", "a/../outside", "C:/outside", "a\\outside", "."):
                    poisoned = json.loads(json.dumps(valid))
                    poisoned["domains"][0][location] = path
                    poisons.append(poisoned)
            report_path = json.loads(json.dumps(valid))
            report_path["domains"][0]["selected_report"]["path"] = "../outside"
            poisons.append(report_path)
            for poison in poisons:
                gate_path.write_text(
                    json.dumps(poison, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                self.assertNotEqual(self.run_shell(root, validator_block).returncode, 0)
                self.assertNotEqual(self.run_shell(root, discovery_block).returncode, 0)

    def test_r3_f001_actual_workflow_rejects_report_linkage_poison(self) -> None:
        gate_block = self.extract("FIXTURE_GATE_SHELL")
        validator_block = self.extract("FIXTURE_GATE_RESULT_VALIDATOR_SHELL")
        discovery_block = self.extract("REPLAY_DOMAIN_DISCOVERY_SHELL")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.checkout(root, report_status="PASS")
            self.assertEqual(self.run_shell(root, gate_block).returncode, 0)
            gate_path = root / ".ci-out" / "fixture-gate.json"
            valid = json.loads(gate_path.read_text(encoding="utf-8"))
            coverage = json.loads(json.dumps(valid))
            coverage["domains"][0]["selected_report"]["total"] = 2
            coverage["domains"][0]["selected_report"]["replayed"] = 2
            wrong_path = json.loads(json.dumps(valid))
            wrong_path["domains"][0]["selected_report"]["path"] = (
                "站点经验库/other.test/fixtures/active/reports/run-replay.md"
            )
            nested_path = json.loads(json.dumps(valid))
            selected_root = nested_path["domains"][0]["selected_root"]
            nested_path["domains"][0]["selected_report"]["path"] = (
                f"{selected_root}/reports/nested/run-replay.md"
            )
            for poison in (coverage, wrong_path, nested_path):
                gate_path.write_text(
                    json.dumps(poison, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                self.assertNotEqual(self.run_shell(root, validator_block).returncode, 0)
                self.assertNotEqual(self.run_shell(root, discovery_block).returncode, 0)


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_orders_tests_and_uses_selected_report_staging(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/consistency-replay.yml").read_text(
            encoding="utf-8"
        )
        test_command = (
            "python3 -m unittest discover -s tools/replayer/tests "
            "-p 'test_*.py' -v"
        )
        self.assertLess(workflow.index(test_command), workflow.index("Validate fixtures schema"))
        self.assertIn("needs: validate-schema", workflow)
        self.assertGreaterEqual(
            workflow.count("from fixture_layout import select_fixture_layout"), 2
        )
        self.assertIn("path: .ci-out/consistency-reports/", workflow)
        self.assertIn("const root = '.ci-out/consistency-reports';", workflow)
        self.assertNotIn("path: 站点经验库/*/fixtures/reports/", workflow)

    def test_workflow_selection_excludes_poison_legacy_and_historical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp) / "站点经验库"
            active = site_root / "active.test" / "fixtures"
            write_snapshot(active / "active" / "snapshots")
            write_snapshot(active / "snapshots", "GET-legacy-poison")
            (active / "active" / "reports").mkdir()
            (active / "active" / "reports" / "trend.json").write_text(
                '{"entries": [{"status": "ACTIVE"}]}', encoding="utf-8"
            )
            (active / "reports").mkdir()
            poison = active / "reports" / "POISON.txt"
            poison.write_text("legacy marker", encoding="utf-8")
            (active / "reports" / "trend.json").write_text(
                '{"entries": [{"status": "POISON"}]}', encoding="utf-8"
            )

            damaged = site_root / "damaged.test" / "fixtures"
            (damaged / "active").mkdir(parents=True)
            write_snapshot(damaged / "snapshots", "GET-legacy-poison")
            (damaged / "reports").mkdir()
            (damaged / "reports" / "POISON.txt").write_text(
                "legacy marker", encoding="utf-8"
            )

            legacy = site_root / "legacy.test" / "fixtures"
            write_snapshot(legacy / "snapshots")
            (legacy / "reports").mkdir()
            (legacy / "reports" / "trend.json").write_text(
                '{"entries": [{"status": "LEGACY"}]}', encoding="utf-8"
            )

            historical = site_root / "historical.test" / "fixtures"
            write_snapshot(historical / "historical" / "snapshots")
            (historical / "historical" / "reports").mkdir()
            (historical / "historical" / "reports" / "POISON.txt").write_text(
                "historical marker", encoding="utf-8"
            )

            domains = []
            artifact_candidates = []
            comment_candidates = []
            for domain in sorted(site_root.iterdir()):
                selected_root, snapshots = fixture_layout.select_fixture_layout(
                    domain / "fixtures"
                )
                if snapshots.is_dir():
                    domains.append(domain.name)
                reports = selected_root / "reports"
                if reports.is_dir():
                    artifact_candidates.extend(reports.iterdir())
                    trend = reports / "trend.json"
                    if trend.is_file():
                        comment_candidates.append(trend)

            self.assertEqual(domains, ["active.test", "legacy.test"])
            self.assertNotIn(poison, artifact_candidates)
            self.assertFalse(any("historical" in str(path) for path in artifact_candidates))
            statuses = [
                json.loads(path.read_text(encoding="utf-8"))["entries"][-1]["status"]
                for path in comment_candidates
            ]
            self.assertEqual(statuses, ["ACTIVE", "LEGACY"])
            self.assertNotIn("POISON", statuses)


if __name__ == "__main__":
    unittest.main()
