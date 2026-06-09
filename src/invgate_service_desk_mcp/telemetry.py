"""OpenTelemetry instrumentation for the MCP server.

Lazy and opt-in: when telemetry is disabled (the default), `build_telemetry`
returns the no-op `Telemetry` base and `opentelemetry` is never imported. When
enabled, `OTelTelemetry` (in a later task) sets up providers and emits spans and
metrics. Telemetry must never break a tool, and must never write to stdout (the
stdio transport uses it for the MCP protocol).
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from .config import Config

DETAIL_METADATA = "metadata"
DETAIL_IDS = "ids"
DETAIL_FULL = "full"


class _NoopClientSpan:
    def set_status_code(self, code: int) -> None:
        pass

    def set_result(self, data: Any) -> None:
        pass


class Telemetry:
    """No-op base. Subclassed by `OTelTelemetry` when telemetry is enabled."""

    enabled = False

    @contextlib.contextmanager
    def tool_span(self, name: str, arguments: dict[str, Any]):
        yield

    @contextlib.contextmanager
    def client_span(self, method: str, endpoint: str, params: dict[str, Any] | None = None):
        yield _NoopClientSpan()

    def shutdown(self) -> None:
        pass


def build_telemetry(config: Config) -> Telemetry:
    """Return a no-op `Telemetry` unless the operator opted in.

    The OTel import and provider setup are deferred to `OTelTelemetry` so the
    base install never imports `opentelemetry`.
    """
    if not config.telemetry_enabled:
        return Telemetry()
    from ._otel import OTelTelemetry

    return OTelTelemetry(config)


class InstrumentedFastMCP(FastMCP):
    """FastMCP subclass that wraps the central `call_tool` dispatch in a tool span."""

    def __init__(self, *args: Any, telemetry: Telemetry, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._telemetry = telemetry

    async def call_tool(self, name: str, arguments: dict[str, Any]):
        with self._telemetry.tool_span(name, arguments):
            return await super().call_tool(name, arguments)
