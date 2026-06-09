"""Shared pytest fixtures and test-isolation helpers."""

import logging

import pytest


@pytest.fixture(autouse=True)
def _reset_pkg_logger():
    """Restore the package logger to a clean state after each test.

    OTelTelemetry._init sets propagate=False on the package logger and installs a
    LoggingHandler.  Without cleanup, subsequent tests that rely on caplog (which
    needs propagation to the root logger) would silently get empty records.
    """
    yield
    pkg_logger = logging.getLogger("invgate_service_desk_mcp")
    pkg_logger.handlers.clear()
    pkg_logger.propagate = True
