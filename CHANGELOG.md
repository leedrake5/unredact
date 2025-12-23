# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-23

### Added
- Initial release as a Python package
- `unredact` CLI command with two output modes:
  - `side_by_side`: Double-width PDF with original and recovered text
  - `overlay_white`: White text overlay on original pages
- Library API for programmatic usage:
  - `extract_lines_with_positions()` - Extract text with coordinates
  - `group_words_into_lines()` - Cluster words by vertical position
  - `build_line_text()` - Reconstruct lines with proper spacing
  - `make_side_by_side()` - Generate comparison PDF
  - `make_overlay_white()` - Generate overlay PDF
- Configurable parameters: `--line-tol`, `--space-unit`, `--min-spaces`
- Type hints and PEP 561 compliance (`py.typed`)
- Unit tests for extraction module
- Modern `pyproject.toml` packaging with hatchling

### Changed
- Restructured from single script to proper Python package
- Modularized into `extraction`, `rendering`, and `cli` modules

[1.0.0]: https://github.com/leedrake5/unredact/releases/tag/v1.0.0
