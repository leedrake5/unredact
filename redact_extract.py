import os
import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path


def map_font_to_pymudf(font):
    """Maps arbitrary font names to built-in PyMuPDF fonts"""
    font = font.lower()

    f = "helvetica"
    if "helvetica" in font:
        if "bold" in font:
            f = "helvetica-bold"
            if "oblique" in font:
                f = "helvetica-boldoblique"
        elif "oblique" in font:
            f = "helvetica-oblique"
    elif "times" in font:
        f = "times-roman"
        if "bold" in font:
            f = "times-bold"
            if "italic" in font:
                f = "times-bolditalic"
        elif "italic" in font:
            f = "times-italic"
    elif "courier" in font:
        f = "courier"
        if "bold" in font:
            f = "courier-bold"
            if "oblique" in font:
                f = "courier-boldoblique"
        elif "oblique" in font:
            f = "courier-oblique"
    elif "symbol" in font:
        f = "symbol"
    elif "zapf" in font or "dingbat" in font:
        f = "zapfdingbats"
    
    return f

@dataclass
class RedactionStats:
    """Statistics about text DISCOVERED under redactions."""
    redaction_boxes_found: int
    words_under_redactions: int
    chars_under_redactions: int
    total_words_extracted: int
    total_chars_extracted: int
    recovery_rate: float  # percent of total that was hidden
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert stats to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def display(self) -> str:
        """Return a formatted string for CLI display."""
        if self.redaction_boxes_found == 0:
            return """
📊 Unredaction Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  No redaction boxes detected
    (Document may not have standard black-bar redactions)

Total text extracted:  {:,} words ({:,} chars)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(self.total_words_extracted, self.total_chars_extracted)
        
        return f"""
🔍 Unredaction Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Redaction boxes found:   {self.redaction_boxes_found:,}
Words recovered:         {self.words_under_redactions:,}
Characters recovered:    {self.chars_under_redactions:,}
Recovery rate:           {self.recovery_rate:.1f}% of text was hidden
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total extracted:         {self.total_words_extracted:,} words
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def detect_redaction_boxes(pdf_path: str) -> List[List[Tuple[float, float, float, float]]]:
    """
    Detect black filled rectangles (redaction boxes) in each page.
    
    Returns list per page of (x0, y0, x1, y1) bounding boxes.
    """
    doc = fitz.open(pdf_path)
    all_boxes = []
    
    for page in doc:
        page_boxes = []
        
        # Method 1: Check for redaction annotations
        for annot in page.annots() or []:
            if annot.type[0] == 12:  # Redact annotation type
                page_boxes.append(tuple(annot.rect))
        
        # Method 2: Look for black filled rectangles in drawings
        drawings = page.get_drawings()
        for d in drawings:
            # Check if it's a filled rectangle with black/dark fill
            if d.get("fill") is not None:
                fill = d.get("fill")
                # Check for black or very dark fill (RGB all < 0.1)
                if isinstance(fill, (list, tuple)) and len(fill) >= 3:
                    if all(c < 0.1 for c in fill[:3]):
                        rect = d.get("rect")
                        if rect:
                            # Filter out tiny rectangles (likely not redactions)
                            width = rect[2] - rect[0]
                            height = rect[3] - rect[1]
                            if width > 10 and height > 5:  # reasonable size
                                page_boxes.append(tuple(rect))
                elif fill == 0 or fill == (0,) or fill == [0]:
                    # Grayscale black
                    rect = d.get("rect")
                    if rect:
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        if width > 10 and height > 5:
                            page_boxes.append(tuple(rect))
        
        all_boxes.append(page_boxes)
    
    doc.close()
    return all_boxes


def word_overlaps_box(word_bbox: Tuple[float, float, float, float], 
                      box: Tuple[float, float, float, float],
                      overlap_threshold: float = 0.5) -> bool:
    """
    Check if a word bounding box overlaps with a redaction box.
    
    Args:
        word_bbox: (x0, top, x1, bottom) of the word
        box: (x0, y0, x1, y1) of the redaction box
        overlap_threshold: fraction of word that must be covered
    
    Returns:
        True if word is under the redaction box
    """
    wx0, wy0, wx1, wy1 = word_bbox
    bx0, by0, bx1, by1 = box
    
    # Calculate intersection
    ix0 = max(wx0, bx0)
    iy0 = max(wy0, by0)
    ix1 = min(wx1, bx1)
    iy1 = min(wy1, by1)
    
    if ix0 >= ix1 or iy0 >= iy1:
        return False
    
    intersection_area = (ix1 - ix0) * (iy1 - iy0)
    word_area = (wx1 - wx0) * (wy1 - wy0)
    
    if word_area <= 0:
        return False
    
    return (intersection_area / word_area) >= overlap_threshold


def compute_redaction_stats(pdf_path: str, line_tol: float = 2.0) -> RedactionStats:
    """
    Compute statistics about text discovered under redaction boxes.
    """
    # Detect redaction boxes
    redaction_boxes = detect_redaction_boxes(pdf_path)
    total_boxes = sum(len(boxes) for boxes in redaction_boxes)
    
    # Extract words with their bounding boxes
    words_under_redactions = 0
    chars_under_redactions = 0
    total_words = 0
    total_chars = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False,
                extra_attrs=["size", "fontname"]
            )
            
            page_boxes = redaction_boxes[page_idx] if page_idx < len(redaction_boxes) else []
            
            for w in words:
                text = w.get("text", "")
                if not text.strip():
                    continue
                
                total_words += 1
                total_chars += len(text)
                
                # Get word bounding box
                word_bbox = (
                    float(w.get("x0", 0)),
                    float(w.get("top", 0)),
                    float(w.get("x1", 0)),
                    float(w.get("bottom", 0))
                )
                
                # Check if word is under any redaction box
                for box in page_boxes:
                    if word_overlaps_box(word_bbox, box):
                        words_under_redactions += 1
                        chars_under_redactions += len(text)
                        break  # Don't double-count
    
    recovery_rate = (chars_under_redactions / total_chars * 100) if total_chars > 0 else 0.0
    
    return RedactionStats(
        redaction_boxes_found=total_boxes,
        words_under_redactions=words_under_redactions,
        chars_under_redactions=chars_under_redactions,
        total_words_extracted=total_words,
        total_chars_extracted=total_chars,
        recovery_rate=recovery_rate
    )


def group_words_into_lines(words, line_tol=2.0):
    """Cluster words into lines using their 'top' coordinate."""
    if not words:
        return []

    words = sorted(words, key=lambda w: (float(w.get("top", 0.0)), float(w.get("x0", 0.0))))

    lines = []
    current = []
    current_top = None

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


def build_line_text(line_words, space_unit_pts=3.0, min_spaces=1, match_font=False):
    """
    Rebuild a line by inserting spaces based on x-gaps.
    Returns (text, x0, x1, top, font_size_est, font_name).
    """
    line_words = sorted(line_words, key=lambda w: float(w.get("x0", 0.0)))

    # representative font size: median of sizes if present, else bbox height
    # Filter out outliers (very large sizes that are likely artifacts)
    sizes = []
    fontnames = {}
    for w in line_words:
        s = w.get("size", None)
        if s is not None:
            try:
                size_val = float(s)
                # Filter out suspiciously large sizes (likely headers/watermarks/artifacts)
                if 4.0 <= size_val <= 72.0:
                    sizes.append(size_val)
            except Exception:
                pass

        if match_font:
            f = w.get("fontname", None)
            if f is not None:
                try:
                    if fontnames.get(f, None) is not None:
                        fontnames[f] += 1
                    else:
                        fontnames[f] = 1
                except Exception:
                    pass

    if sizes:
        sizes_sorted = sorted(sizes)
        font_size = float(sizes_sorted[len(sizes_sorted) // 2])
    else:
        # fallback: median bbox height
        hs = []
        for w in line_words:
            top = float(w.get("top", 0.0))
            bottom = float(w.get("bottom", top + 10.0))
            height = max(6.0, bottom - top)
            # Filter out suspiciously large heights
            if height <= 72.0:
                hs.append(height)
        if hs:
            hs.sort()
            font_size = float(hs[len(hs) // 2])
        else:
            font_size = 10.0
    
    # Final bounds check: clamp to reasonable range
    font_size = max(6.0, min(12.0, font_size))
            hs.append(max(6.0, bottom - top))
        hs.sort()
        font_size = float(hs[len(hs) // 2]) if hs else 10.0
    

    font_name = "helvetica"
    if fontnames and match_font:
        mode_font = max(fontnames, key=fontnames.get)
        font_name = map_font_to_pymudf(
            mode_font.lower()
        )

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

    return "".join(parts), first_x0, last_x1, top_med, font_size, font_name


def extract_lines_with_positions(pdf_path, line_tol=2.0, space_unit_pts=3.0, min_spaces=1, match_font=False):
    """
    Returns list per page: [(line_text, x0, top, font_size), ...]
    Coordinates are in PDF points with origin at top-left (like pdfplumber/PyMuPDF).
    """
    pages_lines = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                keep_blank_chars=False,
                use_text_flow=False,
                extra_attrs=["size", "fontname"]
            )

            lines = group_words_into_lines(words, line_tol=line_tol)

            out = []
            for lw in lines:
                line_text, x0, x1, top, font_size, font_name = build_line_text(
                    lw, space_unit_pts=space_unit_pts, min_spaces=min_spaces, match_font=match_font
                )
                if line_text.strip():
                    out.append((line_text, x0, top, font_size, font_name))
            pages_lines.append(out)

    return pages_lines


def make_side_by_side(input_pdf, output_pdf, line_tol=2.0, space_unit_pts=3.0, min_spaces=1, match_font=False):
    """
    Output pages are double-width:
      left: original page
      right: rebuilt text drawn at approx original coordinates (x offset by page width)
    """
    src = fitz.open(input_pdf)
    out = fitz.open()

    lines_per_page = extract_lines_with_positions(
        input_pdf, line_tol=line_tol, space_unit_pts=space_unit_pts, min_spaces=min_spaces, match_font=match_font
    )

    for i, src_page in enumerate(src):
        rect = src_page.rect
        w, h = rect.width, rect.height

        new_page = out.new_page(width=2 * w, height=h)

        # Left: embed original page as a vector “form”
        new_page.show_pdf_page(fitz.Rect(0, 0, w, h), src, i)

        # Right: draw rebuilt text
        x_off = w
        page_lines = lines_per_page[i] if i < len(lines_per_page) else []

        for (txt, x0, top, font_size, font_name) in page_lines:
            # y: pdfplumber 'top' is top of bbox; nudge toward baseline
            y = float(top) + float(font_size) * 0.85

            new_page.insert_text(
                fitz.Point(x_off + float(x0), float(y)),
                txt,
                fontsize=float(font_size),
                fontname=font_name,
                color=(0, 0, 0),     # black
                overlay=True
            )

    out.save(output_pdf)
    out.close()
    src.close()
    print(f"Wrote: {output_pdf}")


def make_overlay_white(input_pdf, output_pdf, line_tol=2.0, space_unit_pts=3.0, min_spaces=1, match_font=False):
    """
    Output is the original PDF with extracted text overlaid in white.
    This often “reveals” text on top of black redaction bars without detecting them.
    """
    doc = fitz.open(input_pdf)

    lines_per_page = extract_lines_with_positions(
        input_pdf, line_tol=line_tol, space_unit_pts=space_unit_pts, min_spaces=min_spaces, match_font=match_font
    )

    for i, page in enumerate(doc):
        page_lines = lines_per_page[i] if i < len(lines_per_page) else []
        for (txt, x0, top, font_size, font_name) in page_lines:
            y = float(top) + float(font_size) * 0.85
            page.insert_text(
                fitz.Point(float(x0), float(y)),
                txt,
                fontsize=float(font_size),
                fontname=font_name,
                color=(1, 1, 1),   # white
                overlay=True
            )

    doc.save(output_pdf)
    doc.close()
    print(f"Wrote: {output_pdf}")


def main():
    ap = argparse.ArgumentParser(
        description="Extract and reveal text from redacted PDFs"
    )
    ap.add_argument("input_pdf", help="Path to input PDF")
    ap.add_argument("-o", "--output", default=None, help="Output PDF path")
    ap.add_argument("--mode", choices=["side_by_side", "overlay_white"], default="side_by_side")
    ap.add_argument("--line-tol", type=float, default=2.0, help="Line grouping tolerance (pts). Try 1.5–4.0")
    ap.add_argument("--space-unit", type=float, default=3.0, help="Pts per inserted space (bigger => fewer spaces)")
    ap.add_argument("--min-spaces", type=int, default=1, help="Minimum spaces between words when gap exists")
    
    # Stats options
    ap.add_argument("--stats", action="store_true", help="Display unredaction statistics")
    ap.add_argument("--stats-json", metavar="FILE", help="Write stats to JSON file")
    
    ap.add_argument("--match-font", action="store_true", help="Attempt to match the original fonts from the redacted PDF")
    args = ap.parse_args()



    if not os.path.exists(args.input_pdf):
        raise FileNotFoundError(args.input_pdf)

    if args.output is None:
        base_dir = os.path.dirname(args.input_pdf) # ex: ./files
        new_folder = base_dir + "/unredacted/" # ex: ./files/unredacted/
        pdf_name = Path(args.input_pdf).stem # ex: document1 (note: no extension)
        suffix = "_side_by_side.pdf" if args.mode == "side_by_side" else "_overlay_white.pdf"
        args.output = new_folder + pdf_name + suffix # ex ./files/unredacted/document1_side_by_side.pdf

        # create unredacted directory if not exists
        if os.path.isdir(new_folder):
            pass
        else: os.makedirs(new_folder)

    # Process the PDF
    if args.mode == "side_by_side":
        make_side_by_side(
            args.input_pdf, args.output,
            line_tol=args.line_tol, space_unit_pts=args.space_unit, min_spaces=args.min_spaces, match_font=args.match_font
        )
    else:
        make_overlay_white(
            args.input_pdf, args.output,
            line_tol=args.line_tol, space_unit_pts=args.space_unit, min_spaces=args.min_spaces, match_font=args.match_font
        )
    
    # Compute and output stats if requested
    if args.stats or args.stats_json:
        stats = compute_redaction_stats(args.input_pdf, line_tol=args.line_tol)
        
        if args.stats:
            print(stats.display())
        
        if args.stats_json:
            with open(args.stats_json, 'w') as f:
                f.write(stats.to_json())
            print(f"Stats written to: {args.stats_json}")


if __name__ == "__main__":
    main()