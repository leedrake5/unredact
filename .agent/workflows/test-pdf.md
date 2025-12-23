---
description: Test the unredact module with a PDF file
---

# Test PDF Workflow

This workflow tests the unredact module using a PDF placed in `tests/test.pdf`.

## Prerequisites

1. Place your test PDF file at `tests/test.pdf`
2. Ensure the package is installed: `pip install -e .`

## Steps

// turbo
1. Run unit tests to verify the module works:
```bash
pytest tests/ -v
```

// turbo
2. Test side-by-side mode (creates `tests/test_side_by_side.pdf`):
```bash
unredact tests/test.pdf -o tests/test_side_by_side.pdf --mode side_by_side
```

// turbo
3. Test white overlay mode (creates `tests/test_overlay_white.pdf`):
```bash
unredact tests/test.pdf -o tests/test_overlay_white.pdf --mode overlay_white
```

4. Open the output files to verify results:
```bash
open tests/test_side_by_side.pdf tests/test_overlay_white.pdf
```

## Cleanup

Remove generated test output files:
```bash
rm -f tests/test_side_by_side.pdf tests/test_overlay_white.pdf
```

## Library Usage Test

You can also test programmatically:

```python
from unredact import extract_lines_with_positions, make_side_by_side

# Extract text
pages = extract_lines_with_positions("tests/test.pdf")
for i, lines in enumerate(pages):
    print(f"Page {i+1}: {len(lines)} lines")

# Generate output
make_side_by_side("tests/test.pdf", "tests/output.pdf")
```
