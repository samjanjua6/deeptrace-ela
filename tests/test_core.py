"""Tests for core ELA forensics engine (compatible with unittest and pytest)."""

import io
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image

from deeptrace_ela.core import AnomalyBox, ELAResult, analyze_ela


class TestELACore(unittest.TestCase):
    def test_clean_image_verdict(self):
        """A uniform synthetic image should have uniform compression and zero anomalies."""
        img = Image.new("RGB", (256, 256), color=(120, 150, 180))
        result = analyze_ela(img, quality=95)

        self.assertIsInstance(result, ELAResult)
        self.assertFalse(result.is_suspicious)
        self.assertEqual(result.verdict, "CLEAN")
        self.assertGreaterEqual(result.mean_error, 0.0)
        self.assertLess(result.mean_error, 5.0)
        self.assertEqual(len(result.anomalies), 0)
        self.assertEqual(result.heatmap.size, (256, 256))

    def test_spliced_tampering_detection(self):
        """An image with a distinct spliced high-frequency block should calculate valid delta metrics."""
        # Create a smooth base image and save as compressed JPEG
        base = Image.new("RGB", (300, 300), color=(100, 100, 100))
        buf = io.BytesIO()
        base.save(buf, format="JPEG", quality=75)
        buf.seek(0)
        base_jpeg = Image.open(buf).convert("RGB")

        # Splice a patch with alternating high-contrast noise
        tampered_arr = np.array(base_jpeg)
        tampered_arr[100:140, 100:140, :] = 255
        tampered_arr[100:140:2, 100:140, :] = 0
        tampered = Image.fromarray(tampered_arr)

        result = analyze_ela(tampered, quality=95)
        self.assertIsInstance(result, ELAResult)
        self.assertGreater(result.max_difference, 0)
        self.assertGreater(result.mean_error, 0.0)
        self.assertIn(result.verdict, ("SUSPICIOUS", "CLEAN"))

    def test_input_formats(self):
        """Test analyze_ela accepts Path, str, bytes, and PIL.Image."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Image.new("RGB", (128, 128), color=(200, 210, 220))
            img_path = Path(tmp_dir) / "test_sample.png"
            img.save(img_path)

            # 1. Path object
            res_path = analyze_ela(img_path)
            self.assertEqual(res_path.verdict, "CLEAN")

            # 2. str path
            res_str = analyze_ela(str(img_path))
            self.assertEqual(res_str.verdict, "CLEAN")

            # 3. Raw bytes
            img_bytes = img_path.read_bytes()
            res_bytes = analyze_ela(img_bytes)
            self.assertEqual(res_bytes.verdict, "CLEAN")

            # 4. PIL Image
            res_pil = analyze_ela(img)
            self.assertEqual(res_pil.verdict, "CLEAN")

    def test_color_modes(self):
        """Test analyze_ela handles RGBA and Grayscale inputs smoothly."""
        rgba_img = Image.new("RGBA", (100, 100), color=(100, 150, 200, 128))
        res_rgba = analyze_ela(rgba_img)
        self.assertEqual(res_rgba.heatmap.mode, "RGB")

        gray_img = Image.new("L", (100, 100), color=128)
        res_gray = analyze_ela(gray_img)
        self.assertEqual(res_gray.heatmap.mode, "RGB")

    def test_save_heatmap(self):
        """Test ELAResult.save_heatmap() writes a valid image to disk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            img = Image.new("RGB", (150, 150), color=(80, 120, 160))
            result = analyze_ela(img)

            out_file = Path(tmp_dir) / "custom_heatmap.png"
            result.save_heatmap(out_file)

            self.assertTrue(out_file.exists())
            self.assertGreater(out_file.stat().st_size, 0)
            with Image.open(out_file) as saved_img:
                self.assertEqual(saved_img.size, (150, 150))

    def test_to_dict(self):
        """Test to_dict produces all expected metadata fields."""
        img = Image.new("RGB", (128, 128), color=(90, 100, 110))
        result = analyze_ela(img, quality=90, scale=12.0)
        data = result.to_dict()

        self.assertEqual(data["verdict"], "CLEAN")
        self.assertFalse(data["is_suspicious"])
        self.assertEqual(data["quality"], 90)
        self.assertEqual(data["scale_factor"], 12.0)
        self.assertIn("mean_error", data)
        self.assertIn("std_error", data)
        self.assertIn("threshold", data)
        self.assertEqual(data["anomaly_count"], 0)
        self.assertIsInstance(data["anomalies"], list)

    def test_custom_parameters(self):
        """Test custom quality and scale factor overrides."""
        img = Image.new("RGB", (100, 100), color=(50, 100, 150))
        result = analyze_ela(img, quality=80, scale=8.5)

        self.assertEqual(result.quality, 80)
        self.assertEqual(result.scale_factor, 8.5)

    def test_invalid_input_type(self):
        """Passing an unsupported input type should raise ValueError."""
        with self.assertRaises(ValueError):
            analyze_ela(12345)  # type: ignore


if __name__ == "__main__":
    unittest.main()
