# unredact

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python utility for extracting selectable (but visually redacted) text from PDF files and presenting it in a clear, human-readable format while preserving pagination and layout.

> **Note:** This tool is intended for document analysis, archival review, research, and verification of redaction practices. It does not bypass encryption or security controls; it only extracts text that remains present in the PDF content stream.

## What This Tool Does

Many PDFs are "redacted" by placing opaque black rectangles over text without actually removing the underlying text objects. In such cases, the text remains selectable and copy-pastable.

This tool:
- Extracts that underlying text using positional information
- Reconstructs lines to avoid word overlap and run-on text
- Preserves original page size and pagination
- Produces display-friendly output in one of two modes

## Installation

### From PyPI (recommended)

```bash
pip install unredact
```

### From Source

```bash
git clone https://github.com/leedrake5/unredact.git
cd unredact
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Side-by-side mode (default) - original on left, recovered text on right
unredact document.pdf

# White overlay mode - white text drawn over black redaction bars
unredact document.pdf --mode overlay_white

# Custom output path
unredact document.pdf -o recovered.pdf

# Adjust spacing parameters
unredact document.pdf --line-tol 3.0 --space-unit 4.0
```

### As a Library

```python
from unredact import extract_lines_with_positions, make_side_by_side, make_overlay_white

# Extract text with positions
pages = extract_lines_with_positions("document.pdf")
for page_num, lines in enumerate(pages):
    print(f"Page {page_num + 1}:")
    for text, x0, top, font_size in lines:
        print(f"  {text}")

# Generate side-by-side comparison PDF
make_side_by_side("input.pdf", "comparison.pdf")

# Generate white overlay PDF
make_overlay_white("input.pdf", "overlay.pdf")
```

## Output Modes

### Side-by-Side (Recommended)

Each output page is double-width:
- **Left:** Original PDF page (unchanged)
- **Right:** Rebuilt, unredacted text positioned to match the original layout

This mode is ideal for:
- Review and comparison
- Presentations or exhibits
- Auditing redaction practices

![Side-by-side example](https://raw.githubusercontent.com/leedrake5/unredact/master/examples/an_example.png)

### White-Text Overlay

The extracted text is drawn in white directly on top of the original PDF. If black redaction bars are present, the text often becomes visible without explicitly detecting or modifying the bars.

This mode is useful for:
- Visual inspection
- Demonstrating improper redactions

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `input_pdf` | Path to input PDF | (required) |
| `-o, --output` | Output PDF path | `<input>_side_by_side.pdf` or `<input>_overlay_white.pdf` |
| `--mode` | Output mode: `side_by_side` or `overlay_white` | `side_by_side` |
| `--line-tol` | Line grouping tolerance in points | `2.0` |
| `--space-unit` | Points per inserted space | `3.0` |
| `--min-spaces` | Minimum spaces between words | `1` |

## How It Works

1. `pdfplumber` extracts words along with their bounding boxes
2. Words are grouped into lines based on vertical proximity
3. Horizontal spacing is reconstructed from word gaps
4. `PyMuPDF (pymupdf)` is used to:
   - Embed original pages
   - Draw rebuilt text with precise positioning
   - Generate side-by-side or overlay output

No OCR is performed.

## Dependencies

- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF rendering and manipulation

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Author

Created by [leedrake5](https://github.com/leedrake5)
