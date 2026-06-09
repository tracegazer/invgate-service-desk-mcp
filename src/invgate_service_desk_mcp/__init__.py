"""MCP server for the InvGate Service Desk API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("invgate-service-desk-mcp")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
