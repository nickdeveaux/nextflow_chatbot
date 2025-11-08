"""Unit tests for logging configuration."""
import logging
import os
from logging_config import RailwayLogFilter, setup_logging


def test_railway_log_filter_app_logs():
    """Test that app logs pass through the filter."""
    filter_obj = RailwayLogFilter()
    record = logging.LogRecord(
        name="main",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is True


def test_railway_log_filter_backend_logs():
    """Test that backend logs pass through."""
    filter_obj = RailwayLogFilter()
    record = logging.LogRecord(
        name="backend.llm_client",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is True


def test_railway_log_filter_errors():
    """Test that ERROR level logs always pass through."""
    filter_obj = RailwayLogFilter()
    record = logging.LogRecord(
        name="transformers",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Error",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is True


def test_railway_log_filter_third_party_info():
    """Test that third-party INFO logs are blocked."""
    filter_obj = RailwayLogFilter()
    record = logging.LogRecord(
        name="transformers",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Info",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is False


def test_railway_log_filter_third_party_debug():
    """Test that third-party DEBUG logs are blocked."""
    filter_obj = RailwayLogFilter()
    record = logging.LogRecord(
        name="sentence_transformers",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="Debug",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is False


def test_setup_logging():
    """Test that logging setup works."""
    # Save original level
    original_level = logging.getLogger().level
    
    try:
        logger = setup_logging()
        assert logger is not None
        assert logger.level <= logging.INFO
    finally:
        # Restore original level
        logging.getLogger().setLevel(original_level)

