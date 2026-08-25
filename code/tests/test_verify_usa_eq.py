import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers.verify_usa_eq import check_file_for_duplicates, main


class TestCheckFileForDuplicates(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def _write(self, name, content):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_valid_file_with_unique_entries_passes(self):
        path = self._write(
            "eq.json",
            json.dumps(
                {
                    "US0000000001": {"symbol": "AAA", "name": "Alpha Inc."},
                    "US0000000002": {"symbol": "BBB", "name": "Beta Inc."},
                }
            ),
        )
        is_valid, message = check_file_for_duplicates(path)
        self.assertTrue(is_valid, message)
        self.assertIn("No duplicate entries", message)

    def test_duplicate_isin_key_fails(self):
        # Two identical top-level keys - json.load would normally silently
        # keep only the last one, so this has to be written as raw text.
        path = self._write(
            "eq.json",
            """
            {
                "US0000000001": {"symbol": "AAA", "name": "Alpha Inc."},
                "US0000000001": {"symbol": "AAA-DUP", "name": "Alpha Inc. Dup"}
            }
            """,
        )
        is_valid, message = check_file_for_duplicates(path)
        self.assertFalse(is_valid)
        self.assertIn("Duplicate entry", message)
        self.assertIn("US0000000001", message)

    def test_duplicate_symbol_under_different_isin_fails(self):
        # Regression case: same company/symbol listed under two ISINs,
        # e.g. EchoStar Corporation (SATS) previously appeared twice in
        # nasdaq_eq.json under different ISIN keys.
        path = self._write(
            "eq.json",
            json.dumps(
                {
                    "US0000000001": {"symbol": "SATS", "name": "EchoStar Corporation"},
                    "US0000000002": {"symbol": "SATS", "name": "EchoStar Corporation"},
                }
            ),
        )
        is_valid, message = check_file_for_duplicates(path)
        self.assertFalse(is_valid)
        self.assertIn("Duplicate symbol entries", message)
        self.assertIn("SATS", message)

    def test_invalid_json_fails(self):
        path = self._write("eq.json", "{ not valid json")
        is_valid, message = check_file_for_duplicates(path)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON", message)

    def test_nonexistent_file_fails(self):
        path = os.path.join(self.temp_dir, "nonexistent.json")
        is_valid, message = check_file_for_duplicates(path)
        self.assertFalse(is_valid)
        self.assertIn("File not found", message)


class TestMainAgainstRealFiles(unittest.TestCase):
    """These run against the actual nasdaq_eq.json/nyse_eq.json in the repo,
    so this test fails the build if a real duplicate entry sneaks in."""

    def test_real_usa_eq_files_have_no_duplicates(self):
        self.assertTrue(main())


class TestCliExitCode(unittest.TestCase):
    """The GitHub Actions workflow relies on this script's exit code to fail
    CI, so verify that directly rather than just the Python-level return
    value of main()."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "helpers",
            "verify_usa_eq.py",
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def run_script(self, *args):
        import subprocess
        return subprocess.run(
            [sys.executable, self.script_path, *args],
            capture_output=True,
            text=True,
        )

    def test_exits_zero_on_real_files(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
