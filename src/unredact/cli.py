"""
Command-line interface for the unredact tool.
"""

import os
import argparse
import sys

from unredact.rendering import make_side_by_side, make_overlay_white


def main() -> int:
    """
    Main entry point for the unredact CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    ap = argparse.ArgumentParser(
        prog="unredact",
        description="Extract and display visually redacted text from PDFs.",
        epilog="This tool extracts text that remains selectable in PDFs despite visual redaction."
    )
    ap.add_argument(
        "input_pdf", 
        help="Path to input PDF"
    )
    ap.add_argument(
        "-o", "--output", 
        default=None, 
        help="Output PDF path (default: input_side_by_side.pdf or input_overlay_white.pdf)"
    )
    ap.add_argument(
        "--mode", 
        choices=["side_by_side", "overlay_white"], 
        default="side_by_side",
        help="Output mode: 'side_by_side' shows original and recovered text, 'overlay_white' overlays white text on original"
    )
    ap.add_argument(
        "--line-tol", 
        type=float, 
        default=2.0, 
        help="Line grouping tolerance in points (default: 2.0, try 1.5–4.0)"
    )
    ap.add_argument(
        "--space-unit", 
        type=float, 
        default=3.0, 
        help="Points per inserted space - larger values = fewer spaces (default: 3.0)"
    )
    ap.add_argument(
        "--min-spaces", 
        type=int, 
        default=1, 
        help="Minimum spaces between words when gap exists (default: 1)"
    )
    ap.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    args = ap.parse_args()

    if not os.path.exists(args.input_pdf):
        print(f"Error: File not found: {args.input_pdf}", file=sys.stderr)
        return 1

    if args.output is None:
        base, _ = os.path.splitext(args.input_pdf)
        suffix = "_side_by_side.pdf" if args.mode == "side_by_side" else "_overlay_white.pdf"
        args.output = base + suffix

    try:
        if args.mode == "side_by_side":
            make_side_by_side(
                args.input_pdf, 
                args.output,
                line_tol=args.line_tol, 
                space_unit_pts=args.space_unit, 
                min_spaces=args.min_spaces
            )
        else:
            make_overlay_white(
                args.input_pdf, 
                args.output,
                line_tol=args.line_tol, 
                space_unit_pts=args.space_unit, 
                min_spaces=args.min_spaces
            )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
