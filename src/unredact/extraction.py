"""
Text extraction module for PDF redaction recovery.

This module handles extracting text and positional information from PDFs
using pdfplumber, grouping words into lines, and reconstructing text layout.
"""

from typing import List, Tuple, Any, Optional
import pdfplumber


def group_words_into_lines(
    words: List[dict], 
    line_tol: float = 2.0
) -> List[List[dict]]:
    """
    Cluster words into lines using their 'top' coordinate.
    
    Args:
        words: List of word dictionaries from pdfplumber with 'top', 'x0' keys.
        line_tol: Vertical tolerance (in points) for grouping words into lines.
        
    Returns:
        List of lines, where each line is a list of word dictionaries.
    """
    if not words:
        return []

    words = sorted(
        words, 
        key=lambda w: (float(w.get("top", 0.0)), float(w.get("x0", 0.0)))
    )

    lines: List[List[dict]] = []
    current: List[dict] = []
    current_top: Optional[float] = None

    for w in words:
        top = float(w.get("top", 0.0))
        if current_top is None:
            current_top = top
            current = [w]
            continue

        if abs(top - current_top) <= line_tol:
            current.append(w)
            # running average stabilizes grouping
            current_top = (current_top * (len(current) - 1) + top) / len(current)
        else:
            lines.append(current)
            current = [w]
            current_top = top

    if current:
        lines.append(current)

    return lines


def build_line_text(
    line_words: List[dict], 
    space_unit_pts: float = 3.0, 
    min_spaces: int = 1
) -> Tuple[str, float, float, float, float]:
    """
    Rebuild a line by inserting spaces based on x-gaps.
    
    Args:
        line_words: List of word dictionaries for a single line.
        space_unit_pts: Points per inserted space (larger = fewer spaces).
        min_spaces: Minimum spaces between words when a gap exists.
        
    Returns:
        Tuple of (text, x0, x1, top, font_size_est).
    """
    line_words = sorted(line_words, key=lambda w: float(w.get("x0", 0.0)))

    # representative font size: median of sizes if present, else bbox height
    sizes: List[float] = []
    for w in line_words:
        s = w.get("size", None)
        if s is not None:
            try:
                sizes.append(float(s))
            except Exception:
                pass

    if sizes:
        sizes_sorted = sorted(sizes)
        font_size = float(sizes_sorted[len(sizes_sorted) // 2])
    else:
        # fallback: median bbox height
        hs: List[float] = []
        for w in line_words:
            top = float(w.get("top", 0.0))
            bottom = float(w.get("bottom", top + 10.0))
            hs.append(max(6.0, bottom - top))
        hs.sort()
        font_size = float(hs[len(hs) // 2]) if hs else 10.0

    top_med = sorted([float(w.get("top", 0.0)) for w in line_words])[len(line_words) // 2]

    first_x0 = float(line_words[0].get("x0", 0.0))
    last_x1 = float(line_words[0].get("x1", line_words[0].get("x0", 0.0)))
    prev_x1 = float(line_words[0].get("x1", line_words[0].get("x0", 0.0)))

    parts = [line_words[0].get("text", "")]

    for w in line_words[1:]:
        text = w.get("text", "")
        x0 = float(w.get("x0", 0.0))
        x1 = float(w.get("x1", x0))

        gap = x0 - prev_x1

        if gap > 0:
            n_spaces = int(round(gap / max(0.5, space_unit_pts)))
            n_spaces = max(min_spaces, n_spaces)
            parts.append(" " * n_spaces)
        else:
            # slight negative gaps happen; keep minimal separation only when it looks like a break
            parts.append(" " if gap > -space_unit_pts * 0.3 else "")

        parts.append(text)
        prev_x1 = max(prev_x1, x1)
        last_x1 = max(last_x1, x1)

    return "".join(parts), first_x0, last_x1, top_med, font_size


def extract_lines_with_positions(
    pdf_path: str, 
    line_tol: float = 2.0, 
    space_unit_pts: float = 3.0, 
    min_spaces: int = 1
) -> List[List[Tuple[str, float, float, float]]]:
    """
    Extract text lines with positional information from a PDF.
    
    Args:
        pdf_path: Path to the input PDF file.
        line_tol: Vertical tolerance for grouping words into lines.
        space_unit_pts: Points per inserted space.
        min_spaces: Minimum spaces between words.
        
    Returns:
        List per page of tuples: [(line_text, x0, top, font_size), ...]
        Coordinates are in PDF points with origin at top-left.
    """
    pages_lines: List[List[Tuple[str, float, float, float]]] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False,
                extra_attrs=["size", "fontname"]
            )

            lines = group_words_into_lines(words, line_tol=line_tol)

            out: List[Tuple[str, float, float, float]] = []
            for lw in lines:
                line_text, x0, x1, top, font_size = build_line_text(
                    lw, space_unit_pts=space_unit_pts, min_spaces=min_spaces
                )
                if line_text.strip():
                    out.append((line_text, x0, top, font_size))
            pages_lines.append(out)

    return pages_lines
