"""
Tests for citation extraction.
Run with: pytest test_citations.py -v
"""
import pytest
from citations import CitationExtractor
from unittest.mock import Mock, MagicMock


def test_citation_extractor_init():
    """Test CitationExtractor initialization."""
    extractor = CitationExtractor()
    assert extractor.vector_store is None
    
    mock_store = Mock()
    extractor = CitationExtractor(mock_store)
    assert extractor.vector_store == mock_store


def test_extract_from_query_no_store():
    """Test extraction when no vector store."""
    extractor = CitationExtractor()
    result = extractor.extract_from_query("test query")
    assert result == []


def test_extract_from_query_with_store():
    """Test extraction with vector store."""
    mock_store = MagicMock()
    mock_store.search.return_value = [
        ("text1", 0.9, {"url": "https://example.com/doc1"}),
        ("text2", 0.8, {"url": "https://example.com/doc2"}),
        ("text3", 0.7, {"url": "https://example.com/doc1"}),  # Duplicate
    ]
    
    extractor = CitationExtractor(mock_store)
    result = extractor.extract_from_query("test query")
    
    assert len(result) == 2
    assert "https://example.com/doc1" in result
    assert "https://example.com/doc2" in result
    # Check that search was called with config defaults
    mock_store.search.assert_called_once()
    call_args = mock_store.search.call_args
    assert call_args[0][0] == "test query"


def test_extract_from_query_no_urls():
    """Test extraction when results have no URLs."""
    mock_store = MagicMock()
    mock_store.search.return_value = [
        ("text1", 0.9, {}),
        ("text2", 0.8, {"category": "general"}),
    ]
    
    extractor = CitationExtractor(mock_store)
    result = extractor.extract_from_query("test query")
    assert result == []


def test_extract_from_query_store_error():
    """Test extraction handles store errors gracefully."""
    mock_store = MagicMock()
    mock_store.search.side_effect = Exception("Store error")
    
    extractor = CitationExtractor(mock_store)
    result = extractor.extract_from_query("test query")
    assert result == []


def test_extract_urls_deduplication():
    """Test URL deduplication."""
    extractor = CitationExtractor()
    results = [
        ("text1", 0.9, {"url": "https://example.com/doc1"}),
        ("text2", 0.8, {"url": "https://example.com/doc2"}),
        ("text3", 0.7, {"url": "https://example.com/doc1"}),  # Duplicate
        ("text4", 0.6, {"url": "https://example.com/doc3"}),
    ]
    
    urls = extractor._extract_urls(results)
    assert len(urls) == 3
    assert urls.count("https://example.com/doc1") == 1

