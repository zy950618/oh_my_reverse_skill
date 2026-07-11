from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "validate_links.py"
SPEC = importlib.util.spec_from_file_location("validate_links", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validate_links = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_links)


class ValidateLinksTest(unittest.TestCase):
    def run_validator(self, root: Path) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with mock.patch.object(validate_links, "ROOT", root), contextlib.redirect_stdout(stdout):
            exit_code = validate_links.main()
        return exit_code, json.loads(stdout.getvalue())

    def test_local_url_paths_are_decoded_without_query_or_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "target file.md").write_text("target", encoding="utf-8")
            (root / "中文文件.md").write_text("target", encoding="utf-8")
            (root / "ordinary.md").write_text("target", encoding="utf-8")
            (root / "source.md").write_text(
                "\n".join(
                    [
                        "[space](target%20file.md)",
                        "[utf8](%E4%B8%AD%E6%96%87%E6%96%87%E4%BB%B6.md)",
                        "[ordinary](ordinary.md)",
                        "[query](ordinary.md?download=target%20file.md)",
                        "[fragment](ordinary.md#section%20name)",
                        "[web](https://example.com/missing%20file.md)",
                        "[mail](mailto:user@example.com)",
                    ]
                ),
                encoding="utf-8",
            )

            exit_code, payload = self.run_validator(root)

            self.assertEqual(0, exit_code)
            self.assertEqual("PASS", payload["status"])

    def test_decoded_outside_and_missing_targets_still_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            (root / "source.md").write_text(
                "[outside](%2E%2E/outside.md)\n[missing](missing%20file.md)",
                encoding="utf-8",
            )

            exit_code, payload = self.run_validator(root)

            self.assertEqual(1, exit_code)
            self.assertEqual("FAIL", payload["status"])
            self.assertEqual(2, payload["failure_count"])
            failures = payload["failures"]
            self.assertTrue(any("links outside repo" in failure for failure in failures))
            self.assertTrue(any("broken link" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
