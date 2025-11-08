"""Unit tests for context formatter."""
import pytest
from context_formatter import format_context


def test_format_context_empty():
    """Test formatting empty results."""
    assert format_context([]) == ""


def test_format_context_single_result():
    """Test formatting a single result."""
    results = [
        ("This is some text", 0.9, {"url": "https://example.com"})
    ]
    formatted = format_context(results)
    assert "This is some text" in formatted
    assert "Source: https://example.com" in formatted


def test_format_context_multiple_results():
    """Test formatting multiple results."""
    results = [
        ("Text 1", 0.9, {"url": "https://example.com/1"}),
        ("Text 2", 0.8, {"url": "https://example.com/2"}),
    ]
    formatted = format_context(results)
    assert "Text 1" in formatted
    assert "Text 2" in formatted
    assert "https://example.com/1" in formatted
    assert "https://example.com/2" in formatted


def test_format_context_duplicate_urls():
    """Test that duplicate URLs are only shown once."""
    results = [
        ("Text 1", 0.9, {"url": "https://example.com"}),
        ("Text 2", 0.8, {"url": "https://example.com"}),
    ]
    formatted = format_context(results)
    # Should only appear once
    assert formatted.count("Source: https://example.com") == 1


def test_format_context_no_metadata():
    """Test formatting results without metadata."""
    results = [
        ("Text 1", 0.9, {}),
        ("Text 2", 0.8, None),
    ]
    formatted = format_context(results)
    assert "Text 1" in formatted
    assert "Text 2" in formatted
    assert "Source:" not in formatted


def test_format_context_invalid_format():
    """Test handling of invalid result formats."""
    results = [
        "invalid",
        ("valid", 0.9, {"url": "https://example.com"}),
    ]
    formatted = format_context(results)
    # Should only include valid results
    assert "valid" in formatted
    assert "invalid" not in formatted

