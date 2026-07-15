from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAYER_DIR = REPO_ROOT / "tools" / "replayer"
sys.path.insert(0, str(REPLAYER_DIR))

import consistency_report
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
                "expires_at: 2099-01-01T00:00:00Z",
                "category: public-read",
                "sensitive: false",
                "requires_auth: false",
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
                    validate_fixtures,
                    "select_fixture_layout",
                    wraps=fixture_layout.select_fixture_layout,
                ) as selector,
                mock.patch.object(sys, "argv", ["validate_fixtures.py", str(site_root)]),
                contextlib.redirect_stdout(output),
            ):
                result = validate_fixtures.main()

            self.assertEqual(result, 0)
            selector.assert_called_once_with(fixtures)
            self.assertIn("domains: 1  snapshots: 1  valid: 1", output.getvalue())

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
                    self.assertEqual(validate_fixtures.main(), 0)
                self.assertIn("domains: 0  snapshots: 0  valid: 0", output.getvalue())
                self.assertFalse((fixtures / "actual" / "GET-active.actual.json").exists())


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
