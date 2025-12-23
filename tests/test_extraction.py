"""
Tests for the extraction module.
"""

import pytest
from unredact.extraction import group_words_into_lines, build_line_text


class TestGroupWordsIntoLines:
    """Tests for group_words_into_lines function."""

    def test_empty_words(self):
        """Empty input returns empty output."""
        assert group_words_into_lines([]) == []

    def test_single_word(self):
        """Single word returns single line."""
        words = [{"text": "hello", "top": 10.0, "x0": 0.0}]
        lines = group_words_into_lines(words)
        assert len(lines) == 1
        assert len(lines[0]) == 1
        assert lines[0][0]["text"] == "hello"

    def test_words_on_same_line(self):
        """Words with similar 'top' values are grouped together."""
        words = [
            {"text": "hello", "top": 10.0, "x0": 0.0},
            {"text": "world", "top": 10.5, "x0": 50.0},
        ]
        lines = group_words_into_lines(words, line_tol=2.0)
        assert len(lines) == 1
        assert len(lines[0]) == 2

    def test_words_on_different_lines(self):
        """Words with different 'top' values are separated."""
        words = [
            {"text": "line1", "top": 10.0, "x0": 0.0},
            {"text": "line2", "top": 30.0, "x0": 0.0},
        ]
        lines = group_words_into_lines(words, line_tol=2.0)
        assert len(lines) == 2

    def test_line_tolerance(self):
        """Line tolerance affects grouping behavior."""
        words = [
            {"text": "word1", "top": 10.0, "x0": 0.0},
            {"text": "word2", "top": 14.0, "x0": 50.0},
        ]
        
        # With small tolerance, they're separate
        lines_small = group_words_into_lines(words, line_tol=2.0)
        assert len(lines_small) == 2
        
        # With larger tolerance, they're grouped
        lines_large = group_words_into_lines(words, line_tol=5.0)
        assert len(lines_large) == 1


class TestBuildLineText:
    """Tests for build_line_text function."""

    def test_single_word(self):
        """Single word line returns that word."""
        words = [{"text": "hello", "x0": 0.0, "x1": 30.0, "top": 10.0, "bottom": 20.0}]
        text, x0, x1, top, font_size = build_line_text(words)
        assert text == "hello"
        assert x0 == 0.0

    def test_multiple_words_with_gaps(self):
        """Multiple words with gaps get spaces inserted."""
        words = [
            {"text": "hello", "x0": 0.0, "x1": 30.0, "top": 10.0, "bottom": 20.0},
            {"text": "world", "x0": 40.0, "x1": 70.0, "top": 10.0, "bottom": 20.0},
        ]
        text, x0, x1, top, font_size = build_line_text(words, space_unit_pts=3.0)
        assert "hello" in text
        assert "world" in text
        assert " " in text  # Space was inserted

    def test_words_with_size_attribute(self):
        """Words with size attribute use that for font size."""
        words = [
            {"text": "hello", "x0": 0.0, "x1": 30.0, "top": 10.0, "bottom": 20.0, "size": 12.0},
        ]
        text, x0, x1, top, font_size = build_line_text(words)
        assert font_size == 12.0

    def test_words_sorted_by_x0(self):
        """Words are sorted by x0 position."""
        words = [
            {"text": "world", "x0": 40.0, "x1": 70.0, "top": 10.0, "bottom": 20.0},
            {"text": "hello", "x0": 0.0, "x1": 30.0, "top": 10.0, "bottom": 20.0},
        ]
        text, x0, x1, top, font_size = build_line_text(words)
        assert text.startswith("hello")
