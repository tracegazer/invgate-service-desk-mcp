"""Real OpenTelemetry implementation. Imported lazily by `telemetry.build_telemetry`
only when the operator opts in, so the base install never depends on it."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import time
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from .normalize import unwrap_list
from .telemetry import DETAIL_FULL, DETAIL_IDS, Telemetry

if TYPE_CHECKING:
    from .config import Config

_log = logging.getLogger("invgate_service_desk_mcp.telemetry")

_SCOPE = "invgate_service_desk_mcp"
_MAX_PAYLOAD = 2048
_ID_KEY = re.compile(r"(?:^id$|_id$|_ids$)")


def _service_name() -> str:
    return os.environ.get("OTEL_SERVICE_NAME") or "invgate-service-desk-mcp"


def _package_version() -> str:
    try:
        return version("invgate-service-desk-mcp")
    except PackageNotFoundError:
        return "0.0.0"


class _ClientSpan:
    def __init__(self, span, telemetry: OTelTelemetry, endpoint: str):
        self._span = span
        self._telemetry = telemetry
        self._endpoint = endpoint
        self._status_code: int | None = None
        self.item_count: int | None = None
        self.size: int | None = None

    def set_status_code(self, code: int) -> None:
        self._span.set_attribute("http.response.status_code", code)
        self._status_code = code

    def set_result(self, data: Any) -> None:
        flat = unwrap_list(data)
        if isinstance(flat, list):
            self.item_count = len(flat)
            self._span.set_attribute("invgate.response.item_count", self.item_count)
        self.size = len(self._telemetry._redact(json.dumps(data, default=str)))
        self._span.set_attribute("invgate.response.size", self.size)


class OTelTelemetry(Telemetry):
    enabled = True

    def __init__(self, config: Config):
        ver = _package_version()
        resource = Resource.create({"service.name": _service_name(), "service.version": ver})
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
        )
        trace.set_tracer_provider(tracer_provider)
        metrics.set_meter_provider(meter_provider)
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
        set_logger_provider(logger_provider)
        self._init(config, tracer_provider, meter_provider, logger_provider, ver)

    @classmethod
    def for_testing(cls, config, *, tracer_provider, meter_provider, logger_provider=None):
        """Build an instance against caller-supplied providers (no global state,
        no network). Used by tests."""
        self = cls.__new__(cls)
        self._init(
            config, tracer_provider, meter_provider,
            logger_provider or LoggerProvider(), _package_version(),
        )
        return self

    def _init(self, config, tracer_provider, meter_provider, logger_provider, ver):
        self._detail = config.telemetry_detail
        self._token = config.api_token
        self._tracer_provider = tracer_provider
        self._meter_provider = meter_provider
        self._service_name = _service_name()
        self._server_address = urlparse(config.base_url).hostname or ""
        self._tracer = tracer_provider.get_tracer(_SCOPE, ver)
        meter = meter_provider.get_meter(_SCOPE, ver)
        self._tool_duration = meter.create_histogram(
            "mcp.tool.duration", unit="s", description="MCP tool execution time"
        )
        self._request_duration = meter.create_histogram(
            "invgate.client.request.duration",
            unit="s",
            description="InvGate API request time",
        )
        self._response_count = meter.create_histogram(
            "invgate.response.item_count", unit="{item}", description="InvGate response item count"
        )
        self._response_size = meter.create_histogram(
            "invgate.response.size",
            unit="{character}",
            description="InvGate response size in chars",
        )
        self._tool_errors = meter.create_counter(
            "mcp.tool.errors", description="MCP tool failures"
        )
        self._logger_provider = logger_provider
        pkg_logger = logging.getLogger("invgate_service_desk_mcp")
        pkg_logger.setLevel(logging.INFO)
        # We attach the SDK LoggingHandler directly (not opentelemetry-instrumentation-
        # logging, which targets the root logger) and set propagate=False so records
        # never reach the root logger / stdout — stdout carries the MCP stdio protocol.
        pkg_logger.propagate = False
        pkg_logger.handlers = [
            h for h in pkg_logger.handlers if not isinstance(h, LoggingHandler)
        ]
        pkg_logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    def resource_service_name(self) -> str:
        return self._service_name

    def _redact(self, text: str) -> str:
        return text.replace(self._token, "***REDACTED***") if self._token else text

    def _payload_attr(self, value: Any) -> str:
        text = self._redact(json.dumps(value, default=str, ensure_ascii=False))
        return text[:_MAX_PAYLOAD]

    def _apply_arg_attrs(self, span, arguments: dict[str, Any]) -> None:
        if self._detail == DETAIL_FULL:
            span.set_attribute("mcp.tool.arguments", self._payload_attr(arguments))
        elif self._detail == DETAIL_IDS:
            for key, val in arguments.items():
                if _ID_KEY.search(key) and isinstance(val, (int, str)):
                    safe = self._redact(val) if isinstance(val, str) else val
                    span.set_attribute(f"mcp.tool.argument.{key}", safe)

    @contextlib.contextmanager
    def tool_span(self, name: str, arguments: dict[str, Any]):
        start = time.perf_counter()
        outcome = "ok"
        error_type = None
        with self._tracer.start_as_current_span(
            f"execute_tool {name}", kind=trace.SpanKind.SERVER
        ) as span:
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", name)
            span.set_attribute("mcp.tool.name", name)
            self._apply_arg_attrs(span, arguments)
            try:
                yield
            except Exception as exc:
                outcome = "error"
                error_type = type(exc).__name__
                span.set_attribute("error.type", error_type)
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                _log.error("tool %s failed: %s: %s", name, error_type, exc)
                raise
            finally:
                self._tool_duration.record(
                    time.perf_counter() - start,
                    {"tool": name, "outcome": outcome},
                )
                if error_type is not None:
                    self._tool_errors.add(1, {"tool": name, "error.type": error_type})

    @contextlib.contextmanager
    def client_span(self, method: str, endpoint: str, params: dict[str, Any] | None = None):
        start = time.perf_counter()
        with self._tracer.start_as_current_span(
            f"{method} {endpoint}", kind=trace.SpanKind.CLIENT
        ) as span:
            span.set_attribute("http.request.method", method)
            span.set_attribute("invgate.endpoint", endpoint)
            if self._server_address:
                span.set_attribute("server.address", self._server_address)
            if params and self._detail in (DETAIL_IDS, DETAIL_FULL):
                self._apply_arg_attrs(span, params)
            recorder = _ClientSpan(span, self, endpoint)
            try:
                yield recorder
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
            finally:
                attrs: dict[str, Any] = {"endpoint": endpoint}
                if recorder._status_code is not None:
                    attrs["http.response.status_code"] = recorder._status_code
                self._request_duration.record(time.perf_counter() - start, attrs)
                if recorder.item_count is not None:
                    self._response_count.record(recorder.item_count, {"endpoint": endpoint})
                if recorder.size is not None:
                    self._response_size.record(recorder.size, {"endpoint": endpoint})

    def shutdown(self) -> None:
        with contextlib.suppress(Exception):
            self._tracer_provider.shutdown()
        with contextlib.suppress(Exception):
            self._meter_provider.shutdown()
        with contextlib.suppress(Exception):
            self._logger_provider.shutdown()
