"""
PDF Redaction Text Recovery & Display Tool

A Python utility for extracting selectable (but visually redacted) text 
from PDF files and presenting it in a clear, human-readable format.
"""

from unredact.extraction import (
    extract_lines_with_positions,
    group_words_into_lines,
    build_line_text,
)
from unredact.rendering import (
    make_side_by_side,
    make_overlay_white,
)

__version__ = "1.0.0"
__author__ = "leedrake5"

__all__ = [
    "extract_lines_with_positions",
    "group_words_into_lines", 
    "build_line_text",
    "make_side_by_side",
    "make_overlay_white",
    "__version__",
]
