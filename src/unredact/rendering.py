"""
PDF rendering module for redaction text recovery.

This module handles generating output PDFs with recovered text,
either as side-by-side comparison or white text overlay.
"""

import fitz  # PyMuPDF

from unredact.extraction import extract_lines_with_positions


def make_side_by_side(
    input_pdf: str, 
    output_pdf: str, 
    line_tol: float = 2.0, 
    space_unit_pts: float = 3.0, 
    min_spaces: int = 1
) -> None:
    """
    Create a side-by-side PDF with original and recovered text.
    
    Output pages are double-width:
      - Left: Original PDF page (unchanged)
      - Right: Rebuilt text drawn at approximate original coordinates
      
    Args:
        input_pdf: Path to the input PDF file.
        output_pdf: Path for the output PDF file.
        line_tol: Vertical tolerance for line grouping.
        space_unit_pts: Points per inserted space.
        min_spaces: Minimum spaces between words.
    """
    src = fitz.open(input_pdf)
    out = fitz.open()

    lines_per_page = extract_lines_with_positions(
        input_pdf, 
        line_tol=line_tol, 
        space_unit_pts=space_unit_pts, 
        min_spaces=min_spaces
    )

    for i, src_page in enumerate(src):
        rect = src_page.rect
        w, h = rect.width, rect.height

        new_page = out.new_page(width=2 * w, height=h)

        # Left: embed original page as a vector "form"
        new_page.show_pdf_page(fitz.Rect(0, 0, w, h), src, i)

        # Right: draw rebuilt text
        x_off = w
        page_lines = lines_per_page[i] if i < len(lines_per_page) else []

        for (txt, x0, top, font_size) in page_lines:
            # y: pdfplumber 'top' is top of bbox; nudge toward baseline
            y = float(top) + float(font_size) * 0.85

            new_page.insert_text(
                fitz.Point(x_off + float(x0), float(y)),
                txt,
                fontsize=float(font_size),
                fontname="helv",     # built-in Helvetica
                color=(0, 0, 0),     # black
                overlay=True
            )

    out.save(output_pdf)
    out.close()
    src.close()
    print(f"Wrote: {output_pdf}")


def make_overlay_white(
    input_pdf: str, 
    output_pdf: str, 
    line_tol: float = 2.0, 
    space_unit_pts: float = 3.0, 
    min_spaces: int = 1
) -> None:
    """
    Create a PDF with white text overlay on original pages.
    
    The extracted text is drawn in white directly on top of the original PDF.
    If black redaction bars are present, the text often becomes visible 
    without explicitly detecting or modifying the bars.
    
    Args:
        input_pdf: Path to the input PDF file.
        output_pdf: Path for the output PDF file.
        line_tol: Vertical tolerance for line grouping.
        space_unit_pts: Points per inserted space.
        min_spaces: Minimum spaces between words.
    """
    doc = fitz.open(input_pdf)

    lines_per_page = extract_lines_with_positions(
        input_pdf, 
        line_tol=line_tol, 
        space_unit_pts=space_unit_pts, 
        min_spaces=min_spaces
    )

    for i, page in enumerate(doc):
        page_lines = lines_per_page[i] if i < len(lines_per_page) else []
        for (txt, x0, top, font_size) in page_lines:
            y = float(top) + float(font_size) * 0.85
            page.insert_text(
                fitz.Point(float(x0), float(y)),
                txt,
                fontsize=float(font_size),
                fontname="helv",
                color=(1, 1, 1),   # white
                overlay=True
            )

    doc.save(output_pdf)
    doc.close()
    print(f"Wrote: {output_pdf}")
