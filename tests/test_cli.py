"""Tests for DeepTrace ELA CLI (compatible with unittest and pytest)."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "deeptrace_ela.cli", *args],
        capture_output=True,
        text=True,
    )


class TestELACLI(unittest.TestCase):
    def test_cli_version(self):
        """CLI should print current version."""
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        output = proc.stdout + proc.stderr
        self.assertIn("deeptrace-ela 0.1.1", output)

    def test_cli_basic_run(self):
        """CLI should analyze image and save default heatmap."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Image.new("RGB", (100, 100), color=(100, 150, 200))
            test_img = Path(tmp_dir) / "test.jpg"
            img.save(test_img)

            proc = run_cli(str(test_img))
            self.assertEqual(proc.returncode, 0)
            self.assertIn("DeepTrace ELA - Image Forensics Engine", proc.stdout)
            self.assertIn("Verdict:", proc.stdout)
            self.assertIn("[CLEAN]", proc.stdout)

            default_heatmap = Path(tmp_dir) / "test_ela.png"
            self.assertTrue(default_heatmap.exists())

    def test_cli_custom_output(self):
        """CLI should respect -o / --output flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Image.new("RGB", (100, 100), color=(100, 150, 200))
            test_img = Path(tmp_dir) / "test.jpg"
            img.save(test_img)
            out_img = Path(tmp_dir) / "custom_out.png"

            proc = run_cli(str(test_img), "-o", str(out_img), "-q", "90", "-s", "10.0")
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(out_img.exists())
            self.assertIn("Scale Factor:   10.00x", proc.stdout)

    def test_cli_json_flag(self):
        """CLI --json should output structured valid JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Image.new("RGB", (100, 100), color=(120, 130, 140))
            test_img = Path(tmp_dir) / "test.png"
            img.save(test_img)

            proc = run_cli(str(test_img), "--json")
            self.assertEqual(proc.returncode, 0)

            data = json.loads(proc.stdout)
            self.assertEqual(data["verdict"], "CLEAN")
            self.assertFalse(data["is_suspicious"])
            self.assertEqual(data["quality"], 95)
            self.assertEqual(data["author"], "Shaheer Ul Hassan")
            self.assertIn("https://shaheerulhassan.com/", data["homepage"])

    def test_cli_missing_file(self):
        """CLI should fail gracefully with non-zero exit code if file not found."""
        proc = run_cli("non_existent_file_12345.jpg")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("does not exist", proc.stderr)


if __name__ == "__main__":
    unittest.main()
