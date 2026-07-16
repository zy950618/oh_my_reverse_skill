from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from snapshot_diff import diff_snapshot


class SnapshotDiffContractTests(unittest.TestCase):
    def test_status_mismatch_fails_structure_even_when_body_matches(self) -> None:
        expected = {"status": 200, "headers": {}, "body": {"value": 1}}
        actual = {"status": 503, "headers": {}, "body": {"value": 1}}

        result = diff_snapshot(expected, actual, {})

        self.assertFalse(result["status_match"])
        self.assertFalse(result["structure_ok"])
        self.assertEqual(result["consistency_rate"], 1.0)
        self.assertEqual(result["total_fields"], 1)

    def test_empty_expected_snapshot_has_no_comparable_fields(self) -> None:
        expected = {"status": 200, "headers": {}, "body": {}}
        actual = {"status": 200, "headers": {}, "body": {"extra": 1}}

        result = diff_snapshot(expected, actual, {})

        self.assertTrue(result["status_match"])
        self.assertTrue(result["empty_snapshot"])
        self.assertFalse(result["structure_ok"])
        self.assertEqual(result["total_fields"], 0)
        self.assertEqual(result["consistency_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
