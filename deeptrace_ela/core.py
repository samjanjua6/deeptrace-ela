"""
DeepTrace ELA — Core Forensics Engine
Error Level Analysis (ELA) for digital image forgery and splice detection.
Author: Shaheer Ul Hassan (https://shaheerulhassan.com/)
"""

from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import List, Tuple, Union, Optional

import numpy as np
from PIL import Image, ImageChops, ImageEnhance

try:
    import cv2  # Optional enhancement for precise contour bounding boxes
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


@dataclass
class AnomalyBox:
    """Represents a localized suspicious compression anomaly bounding box."""
    x: int
    y: int
    w: int
    h: int
    peak_delta: float
    pixel_count: int

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "peak_delta": round(self.peak_delta, 2),
            "pixel_count": self.pixel_count,
        }


@dataclass
class ELAResult:
    """Contains comprehensive metrics and artifacts from an ELA forensics pass."""
    heatmap: Image.Image
    mean_error: float
    std_error: float
    max_difference: int
    threshold: float
    scale_factor: float
    quality: int
    anomalies: List[AnomalyBox] = field(default_factory=list)

    @property
    def is_suspicious(self) -> bool:
        """Heuristic check: returns True if significant localized compression spikes are present."""
        return len(self.anomalies) > 0

    def to_dict(self) -> dict:
        return {
            "is_suspicious": self.is_suspicious,
            "quality": self.quality,
            "scale_factor": round(self.scale_factor, 2),
            "max_difference": self.max_difference,
            "mean_error": round(self.mean_error, 2),
            "std_error": round(self.std_error, 2),
            "threshold": round(self.threshold, 2),
            "anomaly_count": len(self.anomalies),
            "anomalies": [a.to_dict() for a in self.anomalies],
        }


def analyze_ela(
    image_input: Union[str, Path, bytes, Image.Image],
    quality: int = 95,
    scale: Optional[float] = None,
) -> ELAResult:
    """
    Perform Error Level Analysis (ELA) on an image to detect localized compression discrepancies.

    Parameters:
        image_input: File path, bytes, or PIL Image instance.
        quality: JPEG re-compression quality level (default 95).
        scale: Custom amplification multiplier. If None, auto-calculated up to 15.0x.

    Returns:
        ELAResult object with heatmap and detected anomaly regions.
    """
    # 1. Normalize input to RGB PIL Image
    if isinstance(image_input, (str, Path)):
        orig_img = Image.open(str(image_input)).convert("RGB")
    elif isinstance(image_input, bytes):
        orig_img = Image.open(io.BytesIO(image_input)).convert("RGB")
    elif isinstance(image_input, Image.Image):
        orig_img = image_input.convert("RGB")
    else:
        raise ValueError("Unsupported image input type. Provide a path, bytes, or PIL Image.")

    width, height = orig_img.size

    # 2. Resave at specified quality in an in-memory JPEG stream
    buf = io.BytesIO()
    orig_img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    resaved_img = Image.open(buf)

    # 3. Compute absolute differential image
    diff = ImageChops.difference(orig_img, resaved_img)

    # 4. Calculate amplification scaling factor
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) if extrema else 0

    if scale is None:
        if max_diff > 0:
            scale = min(15.0, 255.0 / float(max_diff))
        else:
            scale = 1.0

    # 5. Amplify contrast to bring out faint compression residuals
    diff_amplified = ImageEnhance.Brightness(diff).enhance(scale)

    # 6. Statistical ambient noise evaluation
    diff_gray = np.array(diff.convert("L"), dtype=np.float32)
    mean_err = float(np.mean(diff_gray))
    std_err = float(np.std(diff_gray))

    # Adaptive threshold: ambient mean + 3.5 sigma (minimum threshold 4.0)
    adaptive_threshold = max(4.0, mean_err + (3.5 * std_err))

    # 7. Localized anomaly cluster detection
    anomalies: List[AnomalyBox] = []

    if HAS_CV2:
        # High precision contour clustering via OpenCV
        hotspots = (diff_gray > adaptive_threshold).astype(np.uint8) * 255

        # Morphological opening/closing to filter individual sensor noise dots
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(hotspots, cv2.MORPH_OPEN, kernel_open)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = 50

        for c in contours:
            carea = cv2.contourArea(c)
            cx, cy, cw, ch = cv2.boundingRect(c)
            if cw <= 0 or ch <= 0:
                continue

            density = carea / float(cw * ch)
            aspect_ratio = float(cw) / float(ch) if ch > 0 else 0

            # Filter dense, localized clusters that aren't global full-frame changes
            if (
                carea >= min_area
                and density >= 0.12
                and 0.08 <= aspect_ratio <= 12.0
                and cw < (0.50 * width)
                and ch < (0.45 * height)
            ):
                patch = diff_gray[cy : cy + ch, cx : cx + cw]
                peak = float(np.max(patch)) if patch.size > 0 else float(adaptive_threshold)
                anomalies.append(AnomalyBox(x=cx, y=cy, w=cw, h=ch, peak_delta=peak, pixel_count=int(carea)))
    else:
        # Fallback grid patch variance detector (pure NumPy)
        block_size = 32
        for y in range(0, height - block_size, block_size):
            for x in range(0, width - block_size, block_size):
                patch = diff_gray[y : y + block_size, x : x + block_size]
                hot_pixels = int(np.sum(patch > adaptive_threshold))
                if hot_pixels > (block_size * block_size * 0.25):
                    peak = float(np.max(patch))
                    anomalies.append(
                        AnomalyBox(x=x, y=y, w=block_size, h=block_size, peak_delta=peak, pixel_count=hot_pixels)
                    )

    # Sort anomalies by peak severity descending
    anomalies.sort(key=lambda a: a.peak_delta, reverse=True)

    return ELAResult(
        heatmap=diff_amplified,
        mean_error=mean_err,
        std_error=std_err,
        max_difference=max_diff,
        threshold=adaptive_threshold,
        scale_factor=scale,
        quality=quality,
        anomalies=anomalies[:10],
    )
