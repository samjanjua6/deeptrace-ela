# DeepTrace ELA (Error Level Analysis) Forensics Engine

An open-source, NIST-grade Error Level Analysis (ELA) and JPEG compression artifact forensics toolkit developed by [Shaheer Ul Hassan](https://shaheerulhassan.com/).

[![PyPI version](https://img.shields.io/pypi/v/deeptrace-ela.svg?color=blue)](https://pypi.org/project/deeptrace-ela/)
[![Downloads](https://img.shields.io/pypi/dm/deeptrace-ela.svg?color=emerald)](https://pypistats.org/packages/deeptrace-ela)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Shaheer%20Ul%20Hassan-8F63DD)](https://shaheerulhassan.com/)
[![GitHub stars](https://img.shields.io/github/stars/samjanjua6/deeptrace-ela?style=social)](https://github.com/samjanjua6/deeptrace-ela)

> [!TIP]
> **Support Open-Source**: If you find `deeptrace-ela` useful in your computer vision or image tampering research, please consider giving it a ⭐ on GitHub — it helps the project grow!

---

## 🔍 Overview

When an image is modified or spliced (such as pasting a fake signature, changing numbers on a document, or splicing digital elements), the newly pasted regions typically have a distinct JPEG compression history from the ambient background.

`deeptrace-ela` re-compresses the input image at a known quality level ($Q = 95$ by default), evaluates the absolute residual error between the input and re-compressed pixels, amplifies compression discrepancies, and detects anomalous noise clusters indicative of cut-and-paste manipulation.

Extracted from the [DeepTrace](https://github.com/samjanjua6/DeepTrace) document forensics pipeline.

---

## 🚀 Installation

```bash
# Standard installation (lightweight, zero OpenCV bloat)
pip install deeptrace-ela

# With OpenCV for sub-pixel morphological contour clustering
pip install deeptrace-ela[cv]

# With development and test dependencies
pip install deeptrace-ela[dev]
```

---

## 💻 CLI Usage

Analyze any image directly from your terminal:

```bash
# Basic ELA analysis (displays summary & saves heatmap to input_ela.png)
deeptrace-ela sample_check.jpg

# Save output heatmap to a custom file
deeptrace-ela contract.jpg --output heatmap.png

# Custom JPEG quality & amplification scale
deeptrace-ela invoice.png --quality 95 --scale 20.0

# Output structured JSON for automated pipelines
deeptrace-ela document.jpg --json
```

### CLI Output Example

```text
============================================================
 DeepTrace ELA — Image Forensics Engine
 Author: Shaheer Ul Hassan (https://shaheerulhassan.com/)
============================================================
Image:        invoice.jpg (1920x1080)
Resave Q:     95
Max Delta:    84
Mean Error:   3.42
Std Error:    2.15
Threshold:    10.95 (ambient mean + 3.5σ)
Status:       ⚠️ SUSPICIOUS (2 anomalous compression cluster(s) detected)

Detected Anomalies:
  [#1] Bounding Box: [x=420, y=310, w=180, h=45] | Peak Delta: 68.2
  [#2] Bounding Box: [x=915, y=740, w=120, h=35] | Peak Delta: 72.1

Heatmap saved to: invoice_ela.png
```

---

## 🐍 Python API

You can easily integrate `deeptrace-ela` into your Python scripts or web services:

```python
from deeptrace_ela import analyze_ela

# Run ELA forensics analysis
result = analyze_ela("document.jpg", quality=95, scale=15.0)

print(f"Forensic Verdict: {result.verdict}")        # 'SUSPICIOUS' or 'CLEAN'
print(f"Is Suspicious:    {result.is_suspicious}")   # True / False
print(f"Mean error:       {result.mean_error:.2f}")

# Iterate over detected anomaly regions
for box in result.anomalies:
    print(f"Anomaly at (x={box.x}, y={box.y}, w={box.w}, h={box.h}) | peak delta: {box.peak_delta}")

# Export structured dictionary for JSON APIs
data = result.to_dict()

# Save amplified heatmap directly
result.save_heatmap("analyzed_ela.png")
```

---

## 🔬 Algorithm Specification

1. **Re-compression**: The input image is converted to RGB and saved to an in-memory JPEG stream at quality $Q$ (standard $Q = 95$).
2. **Differential Residual**: Pixel-by-pixel absolute difference is computed between the original and the re-saved JPEG:
   $$\Delta(x, y) = |I_{orig}(x, y) - I_{resaved}(x, y)|$$
3. **Contrast Amplification**: Differences are amplified dynamically by scaling factor $S = \min(15.0, 255 / \max(\Delta))$ to highlight microscopic compression rate mismatches.
4. **Adaptive Baseline Masking**: An adaptive statistical threshold ($\mu + 3.5\sigma$) computes the localized anomaly score across non-edge ambient surface pixels.

---

## 👤 Author & Maintainer

- **Author**: [Shaheer Ul Hassan](https://shaheerulhassan.com/)
- **Website**: [shaheerulhassan.com](https://shaheerulhassan.com/)
- **GitHub**: [@samjanjua6](https://github.com/samjanjua6)
- **DeepTrace Project**: [samjanjua6/DeepTrace](https://github.com/samjanjua6/DeepTrace)
- **LinkedIn**: [Shaheer Ul Hassan](https://www.linkedin.com/in/muhammad-shaheer-ul-hassan-b3b7213b3/)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
