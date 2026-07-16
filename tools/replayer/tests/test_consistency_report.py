from __future__ import annotations

import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAYER_DIR = REPO_ROOT / "tools" / "replayer"
sys.path.insert(0, str(REPLAYER_DIR))

import consistency_report


DOMAIN = "example.test"


def write_endpoint(
    site_root: Path,
    prefix: str = "GET-example",
    *,
    expected_status: int = 200,
    actual_status: int = 200,
    expected_body: object = None,
    actual_body: object = None,
    active: bool = False,
) -> tuple[Path, Path, Path]:
    selected = site_root / DOMAIN / "fixtures"
    if active:
        selected /= "active"
    snapshots = selected / "snapshots"
    actual = selected / "actual"
    snapshots.mkdir(parents=True, exist_ok=True)
    actual.mkdir(parents=True, exist_ok=True)
    if expected_body is None:
        expected_body = {"value": 1}
    if actual_body is None:
        actual_body = expected_body
    request = snapshots / f"{prefix}.req.json"
    response = snapshots / f"{prefix}.resp.json"
    actual_file = actual / f"{prefix}.actual.json"
    request.write_text(json.dumps({"method": "GET", "url": "https://example.test"}), encoding="utf-8")
    response.write_text(
        json.dumps({"status": expected_status, "headers": {}, "body": expected_body}),
        encoding="utf-8",
    )
    actual_file.write_text(
        json.dumps({"status": actual_status, "headers": {}, "body": actual_body}),
        encoding="utf-8",
    )
    return request, response, actual_file


def strict_json(document: str) -> dict:
    def reject(value: str) -> None:
        raise AssertionError(f"non-standard JSON constant: {value}")

    parsed = json.loads(document, parse_constant=reject)
    if not isinstance(parsed, dict):
        raise AssertionError("stdout is not one JSON object")
    return parsed


class ConsistencyReportTests(unittest.TestCase):
    def run_main(
        self,
        site_root: Path,
        *extra_args: str,
        patches: tuple[mock._patch, ...] = (),
    ) -> tuple[int, dict, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        stack = contextlib.ExitStack()
        with stack:
            stack.enter_context(mock.patch.object(consistency_report, "SITE_ROOT", site_root))
            stack.enter_context(
                mock.patch.object(
                    sys,
                    "argv",
                    ["consistency_report.py", "--domain", DOMAIN, *extra_args],
                )
            )
            for patcher in patches:
                stack.enter_context(patcher)
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            exit_code = consistency_report.main()
        result = strict_json(stdout.getvalue())
        self.assertEqual(exit_code, result["exit_code"])
        self.assertEqual(stdout.getvalue().count("\n"), 1)
        return exit_code, result, stdout.getvalue(), stderr.getvalue()

    def assert_artifacts(self, site_root: Path, result: dict, *, active: bool = False) -> Path:
        selected = site_root / DOMAIN / "fixtures"
        if active:
            selected /= "active"
        self.assertIsNotNone(result["report_artifact"])
        self.assertIsNotNone(result["trend_artifact"])
        self.assertTrue((selected / result["report_artifact"]).is_file())
        self.assertTrue((selected / result["trend_artifact"]).is_file())
        return selected

    def test_missing_actual_and_coverage_gap_are_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            _, _, actual = write_endpoint(site_root)
            actual.unlink()
            code, result, _, stderr = self.run_main(site_root, "--threshold", "0")
            self.assertEqual(code, 3)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
            self.assertEqual((result["selected"], result["replayed"], result["compared"]), (1, 0, 0))
            self.assertEqual(result["fatal_error_count"], 1)
            self.assertIn("actual", stderr)
            self.assert_artifacts(site_root, result)

    def test_required_endpoint_malformed_non_object_matrix_is_fatal(self) -> None:
        cases = (
            ("request", 0, "{"),
            ("response", 1, "[]"),
            ("actual", 2, "{"),
        )
        for label, path_index, document in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                paths = write_endpoint(site_root)
                paths[path_index].write_text(document, encoding="utf-8")
                code, result, _, _ = self.run_main(site_root)
                self.assertEqual(code, 3)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
                self.assertEqual(result["fatal_error_count"], 1)
                self.assertEqual(result["compared"], 0)
                self.assertEqual(result["replayed"], 0 if label == "actual" else 1)
                selected = site_root / DOMAIN / "fixtures"
                report = (selected / result["report_artifact"]).read_text(encoding="utf-8")
                self.assertEqual(report.count("| ERROR:"), 1)

    def test_parser_failures_emit_one_canonical_result_in_subprocess(self) -> None:
        cases = (
            ("invalid threshold syntax", ["--domain", DOMAIN, "--threshold", "abc"]),
            ("missing threshold value", ["--domain", DOMAIN, "--threshold"]),
            ("missing required domain", []),
        )
        script = REPLAYER_DIR / "consistency_report.py"
        for label, arguments in cases:
            with self.subTest(label=label):
                completed = subprocess.run(
                    [sys.executable, "-B", str(script), *arguments],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                result = strict_json(completed.stdout)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.returncode, result["exit_code"])
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["failure_kind"], "INVALID_ARGUMENT")
                self.assertFalse(result["no_data"])
                self.assertIsNone(result["threshold"])
                self.assertIsNone(result["report_artifact"])
                self.assertIsNone(result["trend_artifact"])
                self.assertEqual(completed.stdout.count("\n"), 1)
                self.assertTrue(completed.stderr.strip())

    def test_non_finite_endpoint_constants_are_malformed_json(self) -> None:
        cases = (
            ("request", "NaN"),
            ("response", "Infinity"),
            ("actual", "-Infinity"),
        )
        labels = ("request", "response", "actual")
        for label, constant in cases:
            with self.subTest(label=label, constant=constant), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                paths = write_endpoint(site_root)
                target = paths[labels.index(label)]
                target.write_text(f'{{"value": {constant}}}', encoding="utf-8")
                code, result, _, stderr = self.run_main(site_root)
                self.assertEqual(code, 3)
                self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
                self.assertEqual(result["fatal_error_count"], 1)
                self.assertEqual(result["compared"], 0)
                self.assertIn("non-finite JSON constant", stderr)

    def test_metadata_parse_non_mapping_and_parser_unavailable_are_fatal(self) -> None:
        for loaded, expected_text in (([], "mapping"), (None, "unavailable")):
            with self.subTest(loaded=loaded), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                request, _, _ = write_endpoint(site_root)
                request.with_name("GET-example.meta.yaml").write_text("endpoint: x\n", encoding="utf-8")
                patcher = (
                    mock.patch.object(consistency_report, "load_meta", return_value=loaded)
                    if loaded is not None
                    else mock.patch.object(consistency_report, "load_meta", None)
                )
                _, result, _, stderr = self.run_main(site_root, patches=(patcher,))
                self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
                self.assertEqual(result["fatal_error_count"], 1)
                self.assertIn(expected_text, stderr)

    def test_metadata_parser_exception_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            request, _, _ = write_endpoint(site_root)
            request.with_name("GET-example.meta.yaml").write_text("malformed: [", encoding="utf-8")
            _, result, _, stderr = self.run_main(
                site_root,
                patches=(
                    mock.patch.object(
                        consistency_report,
                        "load_meta",
                        side_effect=ValueError("malformed metadata"),
                    ),
                ),
            )
            self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
            self.assertEqual(result["fatal_error_count"], 1)
            self.assertIn("malformed metadata", stderr)

    def test_endpoint_read_io_failure_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            request, _, _ = write_endpoint(site_root)
            real_read_text = Path.read_text

            def injected_read_text(path: Path, *args: object, **kwargs: object) -> str:
                if path == request:
                    raise OSError("request read failed")
                return real_read_text(path, *args, **kwargs)

            _, result, _, stderr = self.run_main(
                site_root,
                patches=(mock.patch.object(Path, "read_text", autospec=True, side_effect=injected_read_text),),
            )
            self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
            self.assertEqual(result["fatal_error_count"], 1)
            self.assertIn("request read failed", stderr)

    def test_diff_exception_is_a_fatal_endpoint_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            _, result, _, stderr = self.run_main(
                site_root,
                patches=(mock.patch.object(consistency_report, "diff_snapshot", side_effect=RuntimeError("boom")),),
            )
            self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")
            self.assertEqual((result["replayed"], result["compared"]), (1, 0))
            self.assertIn("diff", stderr)

    def test_perfect_body_with_status_mismatch_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root, expected_status=200, actual_status=503)
            _, result, _, _ = self.run_main(site_root, "--threshold", "0")
            self.assertEqual(result["consistency_rate"], 1.0)
            self.assertEqual(result["status_mismatch_count"], 1)
            self.assertEqual(result["fatal_error_count"], 1)
            self.assertEqual(result["failure_kind"], "FATAL_ENDPOINT")

    def test_zero_requests_writes_no_data_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            (site_root / DOMAIN / "fixtures" / "snapshots").mkdir(parents=True)
            code, result, _, _ = self.run_main(site_root, "--threshold", "0")
            self.assertEqual(code, 4)
            self.assertEqual(result["status"], "NO_DATA")
            self.assertTrue(result["no_data"])
            self.assert_artifacts(site_root, result)

    def test_empty_snapshots_do_not_enter_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root, expected_body={}, actual_body={"extra": 1})
            code, result, _, _ = self.run_main(site_root, "--threshold", "0")
            self.assertEqual(code, 4)
            self.assertEqual(result["failure_kind"], "NO_DATA")
            self.assertEqual(result["compared"], 1)
            self.assertEqual(result["comparable_fields"], 0)

    def test_missing_selected_root_is_no_data_without_phantom_hierarchy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            code, result, _, _ = self.run_main(site_root)
            self.assertEqual(code, 4)
            self.assertEqual(result["failure_kind"], "NO_DATA")
            self.assertIsNone(result["report_artifact"])
            self.assertIsNone(result["trend_artifact"])
            self.assertFalse((site_root / DOMAIN).exists())

    def test_threshold_pass_warn_and_fail(self) -> None:
        cases = (
            ({"a": 1}, {"a": 1}, "PASS", 0),
            ({str(i): i for i in range(5)}, {**{str(i): i for i in range(4)}, "4": -1}, "WARN", 3),
            ({"a": 1, "b": 2}, {"a": 1, "b": -1}, "FAIL", 3),
        )
        for expected, actual, status, code in cases:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                write_endpoint(site_root, expected_body=expected, actual_body=actual)
                actual_code, result, _, _ = self.run_main(site_root, "--threshold", "0.9")
                self.assertEqual((result["status"], actual_code), (status, code))
                self.assertEqual(result["failure_kind"], None if status == "PASS" else "THRESHOLD")

    def test_invalid_thresholds_are_strict_json_and_write_nothing(self) -> None:
        for raw, expected in (("nan", None), ("inf", None), ("-inf", None), ("-0.1", -0.1), ("1.1", 1.1)):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                code, result, stdout, stderr = self.run_main(site_root, "--threshold", raw)
                self.assertEqual(code, 2)
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["failure_kind"], "INVALID_ARGUMENT")
                self.assertEqual(result["threshold"], expected)
                strict_json(stdout)
                self.assertIn(raw.lower().replace("+", ""), stderr.lower())
                self.assertFalse((site_root / DOMAIN).exists())

    def test_invalid_trend_is_preserved_and_blocks_all_publication(self) -> None:
        invalid_documents = ("{", "[]", "{}", '{"entries": {}}')
        for document in invalid_documents:
            with self.subTest(document=document), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                write_endpoint(site_root)
                reports = site_root / DOMAIN / "fixtures" / "reports"
                reports.mkdir()
                trend = reports / "trend.json"
                original = document.encode()
                trend.write_bytes(original)
                code, result, _, _ = self.run_main(site_root)
                self.assertEqual(code, 5)
                self.assertEqual(result["failure_kind"], "TREND_INVALID")
                self.assertIsNone(result["report_artifact"])
                self.assertIsNone(result["trend_artifact"])
                self.assertEqual(trend.read_bytes(), original)
                self.assertEqual(list(reports.glob("*-replay.md")), [])

    def test_non_finite_trend_constants_are_invalid_and_preserved(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                write_endpoint(site_root)
                reports = site_root / DOMAIN / "fixtures" / "reports"
                reports.mkdir()
                trend = reports / "trend.json"
                original = f'{{"entries": [{constant}]}}'.encode()
                trend.write_bytes(original)
                code, result, _, stderr = self.run_main(site_root)
                self.assertEqual(code, 5)
                self.assertEqual(result["failure_kind"], "TREND_INVALID")
                self.assertIsNone(result["report_artifact"])
                self.assertIsNone(result["trend_artifact"])
                self.assertEqual(trend.read_bytes(), original)
                self.assertIn("non-finite JSON constant", stderr)

    def test_unreadable_trend_io_is_invalid_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            reports = site_root / DOMAIN / "fixtures" / "reports"
            reports.mkdir()
            trend = reports / "trend.json"
            original = b'{"entries": []}'
            trend.write_bytes(original)
            real_read_text = Path.read_text

            def injected_read_text(path: Path, *args: object, **kwargs: object) -> str:
                if path == trend:
                    raise OSError("trend read failed")
                return real_read_text(path, *args, **kwargs)

            code, result, _, stderr = self.run_main(
                site_root,
                patches=(mock.patch.object(Path, "read_text", autospec=True, side_effect=injected_read_text),),
            )
            self.assertEqual(code, 5)
            self.assertEqual(result["failure_kind"], "TREND_INVALID")
            self.assertIsNone(result["report_artifact"])
            self.assertIsNone(result["trend_artifact"])
            self.assertEqual(trend.read_bytes(), original)
            self.assertIn("trend read failed", stderr)

    def test_successful_stdout_report_and_trend_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            code, result, _, _ = self.run_main(site_root)
            self.assertEqual(code, 0)
            selected = self.assert_artifacts(site_root, result)
            report = (selected / result["report_artifact"]).read_text(encoding="utf-8")
            canonical = strict_json(report.split("```json\n", 1)[1].split("\n```", 1)[0])
            trend = json.loads((selected / result["trend_artifact"]).read_text(encoding="utf-8"))
            trend_entry = dict(trend["entries"][-1])
            trend_entry.pop("date")
            self.assertEqual(canonical, result)
            self.assertEqual(trend_entry, result)

    def test_valid_mapping_history_is_preserved_and_capped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            reports = site_root / DOMAIN / "fixtures" / "reports"
            reports.mkdir()
            entries = [{"sequence": i} for i in range(205)]
            (reports / "trend.json").write_text(
                json.dumps({"schema": "kept", "entries": entries}), encoding="utf-8"
            )
            _, result, _, _ = self.run_main(site_root)
            trend = json.loads((reports / "trend.json").read_text(encoding="utf-8"))
            self.assertEqual(trend["schema"], "kept")
            self.assertEqual(len(trend["entries"]), 200)
            self.assertEqual(trend["entries"][0]["sequence"], 6)
            self.assertEqual(trend["entries"][-1]["status"], result["status"])

    def test_active_layout_excludes_legacy_and_historical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root, "GET-active", active=True)
            write_endpoint(site_root, "GET-legacy")
            historical = site_root / DOMAIN / "fixtures" / "historical" / "snapshots"
            historical.mkdir(parents=True)
            (historical / "GET-history.req.json").write_text("{}", encoding="utf-8")
            _, result, _, _ = self.run_main(site_root)
            self.assertEqual((result["total"], result["selected"], result["replayed"]), (1, 1, 1))
            self.assert_artifacts(site_root, result, active=True)
            self.assertFalse((site_root / DOMAIN / "fixtures" / "reports").exists())

    def test_artifact_staging_failure_declares_no_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            real_stage = consistency_report._stage_text
            calls = 0

            def fail_second(target: Path, content: str) -> Path:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("stage two")
                return real_stage(target, content)

            code, result, _, _ = self.run_main(
                site_root,
                patches=(mock.patch.object(consistency_report, "_stage_text", side_effect=fail_second),),
            )
            self.assertEqual(code, 5)
            self.assertEqual(result["failure_kind"], "ARTIFACT_WRITE")
            self.assertIsNone(result["report_artifact"])
            self.assertIsNone(result["trend_artifact"])
            reports = site_root / DOMAIN / "fixtures" / "reports"
            self.assertEqual(list(reports.glob("*.tmp")), [])
            self.assertEqual(list(reports.glob("*-replay.md")), [])
            self.assertFalse((reports / "trend.json").exists())

    def test_serialization_failure_is_canonical_artifact_write_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            write_endpoint(site_root)
            code, result, _, stderr = self.run_main(
                site_root,
                patches=(
                    mock.patch.object(
                        consistency_report,
                        "render_report",
                        side_effect=ValueError("serialize failed"),
                    ),
                ),
            )
            self.assertEqual(code, 5)
            self.assertEqual(result["failure_kind"], "ARTIFACT_WRITE")
            self.assertIsNone(result["report_artifact"])
            self.assertIsNone(result["trend_artifact"])
            self.assertIn("serialize failed", stderr)

    def test_first_and_second_replace_failures_leave_no_current_partial(self) -> None:
        for fail_call in (1, 2):
            with self.subTest(fail_call=fail_call), tempfile.TemporaryDirectory() as tmp:
                site_root = Path(tmp)
                write_endpoint(site_root)
                real_replace = os.replace
                calls = 0

                def injected_replace(source: object, target: object) -> None:
                    nonlocal calls
                    calls += 1
                    if calls == fail_call:
                        raise OSError(f"replace {fail_call}")
                    real_replace(source, target)

                code, result, _, _ = self.run_main(
                    site_root,
                    patches=(mock.patch.object(consistency_report.os, "replace", side_effect=injected_replace),),
                )
                self.assertEqual(code, 5)
                self.assertEqual(result["failure_kind"], "ARTIFACT_WRITE")
                self.assertIsNone(result["report_artifact"])
                self.assertIsNone(result["trend_artifact"])
                reports = site_root / DOMAIN / "fixtures" / "reports"
                self.assertEqual(list(reports.glob("*.tmp")), [])
                self.assertEqual(list(reports.glob("*-replay.md")), [])
                self.assertFalse((reports / "trend.json").exists())


if __name__ == "__main__":
    unittest.main()
