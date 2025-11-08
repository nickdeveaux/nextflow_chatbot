"""Unit tests for logging configuration."""
import logging
import os
import sys
from io import StringIO
from logging_config import InfoFilter, setup_logging


def test_info_filter_debug():
    """Test that DEBUG logs pass through InfoFilter."""
    filter_obj = InfoFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="Debug message",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is True


def test_info_filter_info():
    """Test that INFO logs pass through InfoFilter."""
    filter_obj = InfoFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Info message",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is True


def test_info_filter_warning():
    """Test that WARNING logs are blocked by InfoFilter (go to stderr instead)."""
    filter_obj = InfoFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="Warning message",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is False


def test_info_filter_error():
    """Test that ERROR logs are blocked by InfoFilter (go to stderr instead)."""
    filter_obj = InfoFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Error message",
        args=(),
        exc_info=None
    )
    assert filter_obj.filter(record) is False


def test_setup_logging():
    """Test that logging setup works and returns a logger."""
    # Save original handlers and level
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    try:
        logger = setup_logging()
        assert logger is not None
        assert logger.name == 'main'
        assert logger.level <= logging.INFO
        
        # Verify root logger has handlers
        assert len(root_logger.handlers) == 2
    finally:
        # Restore original state
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_setup_logging_handlers():
    """Test that setup_logging creates correct handlers."""
    # Save original state
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    try:
        setup_logging()
        
        # Check we have exactly 2 handlers
        assert len(root_logger.handlers) == 2
        
        # Check handler types and levels
        handlers = root_logger.handlers
        stdout_handler = None
        stderr_handler = None
        
        for handler in handlers:
            if isinstance(handler, logging.StreamHandler):
                if handler.stream == sys.stdout:
                    stdout_handler = handler
                elif handler.stream == sys.stderr:
                    stderr_handler = handler
        
        assert stdout_handler is not None, "Should have stdout handler"
        assert stderr_handler is not None, "Should have stderr handler"
        assert stdout_handler.level == logging.DEBUG
        assert stderr_handler.level == logging.WARNING
        
        # Check that stdout handler has InfoFilter
        assert len(stdout_handler.filters) > 0
        assert isinstance(stdout_handler.filters[0], InfoFilter)
    finally:
        # Restore original state
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)


def test_third_party_logger_suppression():
    """Test that third-party loggers are set to WARNING level."""
    # Save original state
    transformers_logger = logging.getLogger('transformers')
    original_level = transformers_logger.level
    original_propagate = transformers_logger.propagate
    
    try:
        setup_logging()
        
        # Check that transformers logger is set to WARNING
        assert transformers_logger.level == logging.WARNING
        assert transformers_logger.propagate is False
    finally:
        # Restore original state
        transformers_logger.setLevel(original_level)
        transformers_logger.propagate = original_propagate


def test_logging_output_streams():
    """Test that INFO logs go to stdout and WARNING logs go to stderr."""
    # Save original state
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    try:
        setup_logging()
        
        # Capture stdout and stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        # Replace handlers with captured streams
        root_logger.handlers.clear()
        stdout_handler = logging.StreamHandler(stdout_capture)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.addFilter(InfoFilter())
        root_logger.addHandler(stdout_handler)
        
        stderr_handler = logging.StreamHandler(stderr_capture)
        stderr_handler.setLevel(logging.WARNING)
        root_logger.addHandler(stderr_handler)
        
        # Test INFO log goes to stdout
        root_logger.info("Test info message")
        assert "Test info message" in stdout_capture.getvalue()
        assert "Test info message" not in stderr_capture.getvalue()
        
        # Test WARNING log goes to stderr
        root_logger.warning("Test warning message")
        assert "Test warning message" in stderr_capture.getvalue()
        assert "Test warning message" not in stdout_capture.getvalue()
    finally:
        # Restore original state
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
