"""
DeepTrace ELA — CLI Interface
Command-line tool for running JPEG Error Level Analysis forensics.
Author: Shaheer Ul Hassan (https://shaheerulhassan.com/)
"""

import argparse
import json
from pathlib import Path
import sys

from deeptrace_ela.core import analyze_ela


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deeptrace-ela",
        description="NIST-grade Error Level Analysis (ELA) Image Forensics Engine.\n"
                    "Developed by Shaheer Ul Hassan (https://shaheerulhassan.com/)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("image", type=str, help="Path to the image to analyze")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path to save the amplified ELA heatmap image")
    parser.add_argument("-q", "--quality", type=int, default=95, help="JPEG re-compression quality level (default: 95)")
    parser.add_argument("-s", "--scale", type=float, default=None, help="Amplification factor scale (default: auto)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("-v", "--version", action="version", version="deeptrace-ela 0.1.0")

    args = parser.parse_args()

    input_path = Path(args.image)
    if not input_path.exists():
        print(f"Error: Input file '{args.image}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        result = analyze_ela(str(input_path), quality=args.quality, scale=args.scale)
    except Exception as exc:
        print(f"Error analyzing image: {exc}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if not output_path:
        output_path = str(input_path.with_name(f"{input_path.stem}_ela.png"))

    try:
        result.heatmap.save(output_path)
    except Exception as exc:
        print(f"Warning: Could not save heatmap to '{output_path}': {exc}", file=sys.stderr)

    if args.json:
        data = result.to_dict()
        data["input_file"] = str(input_path.resolve())
        data["output_heatmap"] = str(Path(output_path).resolve())
        data["author"] = "Shaheer Ul Hassan"
        data["homepage"] = "https://shaheerulhassan.com/"
        print(json.dumps(data, indent=2))
    else:
        status_text = "[SUSPICIOUS] Potential Tampering / Splicing Detected" if result.is_suspicious else "[CLEAN] Uniform Ambient Compression Noise"
        print("=" * 64)
        print(" DeepTrace ELA - Image Forensics Engine")
        print(" Author: Shaheer Ul Hassan (https://shaheerulhassan.com/)")
        print("=" * 64)
        print(f"Input Image:    {input_path.name}")
        print(f"Resave Quality: {result.quality}")
        print(f"Scale Factor:   {result.scale_factor:.2f}x")
        print(f"Max Delta:      {result.max_difference}")
        print(f"Mean Error:     {result.mean_error:.2f}")
        print(f"Std Error:      {result.std_error:.2f}")
        print(f"Threshold:      {result.threshold:.2f} (ambient mean + 3.5 sigma)")
        print(f"Verdict:        {status_text}")
        print("-" * 64)

        if result.anomalies:
            print(f"Detected Anomalies ({len(result.anomalies)}):")
            for idx, a in enumerate(result.anomalies, start=1):
                print(f"  [#{idx}] Bounding Box: [x={a.x}, y={a.y}, w={a.w}, h={a.h}] | Peak Delta: {a.peak_delta:.1f}")
        else:
            print("No anomalous localized compression hotspots detected.")

        print(f"\nHeatmap saved to: {output_path}")
        print("=" * 64)


if __name__ == "__main__":
    main()
