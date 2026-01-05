# PDF Redaction Text Recovery & Display Tool

This repository contains a Python utility for extracting selectable (but visually redacted) text from PDF files and presenting it in a clear, human-readable format while preserving pagination and layout as closely as possible.

The tool is intended for document analysis, archival review, research, and verification of redaction practices It does not bypass encryption or security controls; it only extracts text that remains present in the PDF content stream.

Note - not all files can be unredacted. This tool only works for pooly redacted files. If you get blank spaces, the file has been properly redacted. 

---

## What This Tool Does

Many PDFs are “redacted” by placing opaque black rectangles over text without actually removing the underlying text objects. In such cases, the text remains selectable and copy-pastable.

This tool:
- Extracts that underlying text using positional information
- Reconstructs lines to avoid word overlap and run-on text
- Preserves original page size and pagination
- Produces display-friendly output in one of two modes

---

## Output Modes

### 1) Side-by-Side (Recommended)

Each output page is double-width:

- **Left:** Original PDF page (unchanged)
- **Right:** Rebuilt, unredacted text positioned to match the original layout

This mode is ideal for:
- Review and comparison
- Presentations or exhibits
- Auditing redaction practices

Example:

![Side-by-side example](https://raw.githubusercontent.com/leedrake5/unredact/master/examples/an_example.png)

---

### 2) White-Text Overlay

The extracted text is drawn in white directly on top of the original PDF.

If black redaction bars are present, the text often becomes visible without explicitly detecting or modifying the bars.

This mode is useful for:
- Visual inspection
- Demonstrating improper redactions

---

## How It Works

1. `pdfplumber` extracts words along with their bounding boxes
2. Words are grouped into lines based on vertical proximity
3. Horizontal spacing is reconstructed from word gaps
4. `PyMuPDF (pymupdf)` is used to:
   - Embed original pages
   - Draw rebuilt text with precise positioning
   - Generate side-by-side or overlay output

No OCR is performed.

---

## Installation

```bash
uv sync
```
## Use
```bash
uv run redact_extract.py
```

```bash
usage: redact_extract.py [-h] [-o OUTPUT] [--mode {side_by_side,overlay_white}] [--line-tol LINE_TOL] [--space-unit SPACE_UNIT]
                         [--min-spaces MIN_SPACES]
                         input_pdf
redact_extract.py: error: the following arguments are required: input_pdf
```

### Statistics

Track what text was **actually recovered from under redaction bars** with the `--stats` flag:

```bash
python redact_extract.py example.pdf --stats
```

Output:
```
🔍 Unredaction Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Redaction boxes found:   42
Words recovered:         387
Characters recovered:    2,156
Recovery rate:           12.3% of text was hidden
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total extracted:         3,429 words
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Export stats to JSON:

```bash
python redact_extract.py example.pdf --stats-json stats.json
```

The tool detects black-filled rectangles (redaction boxes) and measures which extracted words were hidden underneath them.
