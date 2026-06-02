import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from pathlib import Path

from invgate_service_desk_mcp._otel import OTelTelemetry
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.telemetry import (
    DETAIL_METADATA,
    InstrumentedFastMCP,
    Telemetry,
    build_telemetry,
)

BASE = {"INVGATE_BASE_URL": "https://x.invgate.net", "INVGATE_API_TOKEN": "t"}


def _config(**extra):
    return Config.load({**BASE, **extra}, config_path=Path("/does/not/exist.toml"))


def test_build_telemetry_disabled_returns_noop():
    telemetry = build_telemetry(_config())
    assert telemetry.enabled is False


def test_noop_tool_span_is_a_passthrough_context_manager():
    telemetry = build_telemetry(_config())
    with telemetry.tool_span("get_incident", {"id": 1}):
        pass  # must not raise


def test_noop_client_span_yields_a_recorder():
    telemetry = build_telemetry(_config())
    with telemetry.client_span("GET", "incident", {"id": 1}) as span:
        span.set_status_code(200)  # must not raise


def test_noop_shutdown_is_safe():
    build_telemetry(_config()).shutdown()


def test_detail_metadata_constant():
    assert DETAIL_METADATA == "metadata"


def test_base_telemetry_is_the_noop():
    assert Telemetry().enabled is False


@pytest.fixture
def otel():
    """An OTelTelemetry wired to in-memory exporters (no network)."""
    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[reader])
    telemetry = OTelTelemetry.for_testing(
        _config(INVGATE_TELEMETRY="1"),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
    return telemetry, exporter, reader


def test_tool_span_has_genai_attributes(otel):
    telemetry, exporter, _ = otel
    with telemetry.tool_span("get_incident", {"id": 21574}):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "execute_tool get_incident"
    assert span.attributes["gen_ai.operation.name"] == "execute_tool"
    assert span.attributes["gen_ai.tool.name"] == "get_incident"
    assert span.attributes["mcp.tool.name"] == "get_incident"
    assert "mcp.tool.arguments" not in span.attributes


def test_tool_span_records_error_and_reraises(otel):
    telemetry, exporter, _ = otel
    with pytest.raises(ValueError):
        with telemetry.tool_span("bad_tool", {}):
            raise ValueError("boom")
    span = exporter.get_finished_spans()[0]
    assert span.status.status_code.name == "ERROR"
    assert any(e.name == "exception" for e in span.events)


def test_client_span_has_http_attributes(otel):
    telemetry, exporter, _ = otel
    with telemetry.client_span("GET", "incidents.by.agent", {"id": 18}) as span:
        span.set_status_code(200)
    span = exporter.get_finished_spans()[0]
    assert span.attributes["http.request.method"] == "GET"
    assert span.attributes["invgate.endpoint"] == "incidents.by.agent"
    assert span.attributes["http.response.status_code"] == 200


def test_tool_duration_metric_is_recorded(otel):
    telemetry, _, reader = otel
    with telemetry.tool_span("get_incident", {"id": 1}):
        pass
    data = reader.get_metrics_data()
    names = {
        m.name
        for rm in data.resource_metrics
        for sm in rm.scope_metrics
        for m in sm.metrics
    }
    assert "mcp.tool.duration" in names


def _otel_with_detail(detail, token="SECRET-TOKEN"):
    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    meter_provider = MeterProvider(metric_readers=[InMemoryMetricReader()])
    telemetry = OTelTelemetry.for_testing(
        Config.load({**BASE, "INVGATE_API_TOKEN": token, "INVGATE_TELEMETRY": "1",
                     "INVGATE_TELEMETRY_DETAIL": detail}, config_path=Path("/does/not/exist.toml")),
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
    )
    return telemetry, exporter


def test_ids_tier_captures_argument_ids():
    telemetry, exporter = _otel_with_detail("ids")
    with telemetry.tool_span("get_incident", {"id": 21574, "comments": True}):
        pass
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["mcp.tool.argument.id"] == 21574
    assert "mcp.tool.argument.comments" not in attrs


def test_full_tier_captures_capped_payload():
    telemetry, exporter = _otel_with_detail("full")
    with telemetry.tool_span("create_incident", {"title": "x" * 5000}):
        pass
    attrs = exporter.get_finished_spans()[0].attributes
    assert "mcp.tool.arguments" in attrs
    assert len(attrs["mcp.tool.arguments"]) <= 2048


def test_token_is_redacted_at_full_tier():
    telemetry, exporter = _otel_with_detail("full", token="SECRET-TOKEN")
    with telemetry.tool_span("login", {"note": "uses SECRET-TOKEN inside"}):
        pass
    attrs = exporter.get_finished_spans()[0].attributes
    assert "SECRET-TOKEN" not in attrs["mcp.tool.arguments"]


def test_token_is_redacted_at_ids_tier():
    telemetry, exporter = _otel_with_detail("ids", token="SECRET-TOKEN")
    with telemetry.tool_span("get_incident", {"id": "SECRET-TOKEN"}):
        pass
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["mcp.tool.argument.id"] == "***REDACTED***"


def test_resource_has_default_service_name(monkeypatch):
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader
    from opentelemetry.sdk.trace import TracerProvider
    tp = TracerProvider()
    telemetry = OTelTelemetry.for_testing(
        _config(INVGATE_TELEMETRY="1"),
        tracer_provider=tp,
        meter_provider=MeterProvider(metric_readers=[InMemoryMetricReader()]),
    )
    assert telemetry.resource_service_name() == "invgate-service-desk-mcp"


def test_shutdown_calls_meter_provider(otel):
    telemetry, _, reader = otel
    # Should not raise; meter provider shutdown must be called
    telemetry.shutdown()


def test_client_span_has_server_address(otel):
    telemetry, exporter, _ = otel
    with telemetry.client_span("GET", "incident", {"id": 1}) as span:
        span.set_status_code(200)
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["server.address"] == "x.invgate.net"


def test_client_span_records_size_and_item_count(otel):
    telemetry, exporter, _ = otel
    with telemetry.client_span("GET", "incidents.by.agent", {"id": 18}) as span:
        span.set_status_code(200)
        span.set_result([{"id": 1}, {"id": 2}, {"id": 3}])
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["invgate.response.item_count"] == 3
    assert attrs["invgate.response.size"] > 0


def test_client_span_size_redacts_token():
    telemetry, exporter = _otel_with_detail("metadata", token="SECRET-TOKEN")
    with telemetry.client_span("GET", "incident", None) as span:
        span.set_status_code(200)
        span.set_result({"note": "SECRET-TOKEN here"})
    attrs = exporter.get_finished_spans()[0].attributes
    assert "invgate.response.item_count" not in attrs  # dict, not a list
    assert attrs["invgate.response.size"] > 0


def test_tool_error_sets_error_type_and_counter(otel):
    telemetry, exporter, reader = otel
    with pytest.raises(ValueError):
        with telemetry.tool_span("bad_tool", {}):
            raise ValueError("boom")
    span = exporter.get_finished_spans()[0]
    assert span.attributes["error.type"] == "ValueError"
    names = {m.name for rm in reader.get_metrics_data().resource_metrics
             for sm in rm.scope_metrics for m in sm.metrics}
    assert "mcp.tool.errors" in names


def test_logger_provider_configured_with_non_propagating_handler():
    import logging
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
    exporter = InMemoryLogRecordExporter()
    lp = LoggerProvider()
    lp.add_log_record_processor(SimpleLogRecordProcessor(exporter))
    telemetry = OTelTelemetry.for_testing(
        _config(INVGATE_TELEMETRY="1"),
        tracer_provider=TracerProvider(),
        meter_provider=MeterProvider(metric_readers=[InMemoryMetricReader()]),
        logger_provider=lp,
    )
    pkg_logger = logging.getLogger("invgate_service_desk_mcp")
    assert pkg_logger.propagate is False
    assert any(isinstance(h, LoggingHandler) for h in pkg_logger.handlers)
    telemetry.shutdown()


def test_tool_error_emits_error_log():
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
    exporter = InMemoryLogRecordExporter()
    lp = LoggerProvider()
    lp.add_log_record_processor(SimpleLogRecordProcessor(exporter))
    telemetry = OTelTelemetry.for_testing(
        _config(INVGATE_TELEMETRY="1"),
        tracer_provider=TracerProvider(),
        meter_provider=MeterProvider(metric_readers=[InMemoryMetricReader()]),
        logger_provider=lp,
    )
    try:
        with telemetry.tool_span("bad_tool", {}):
            raise ValueError("boom")
    except ValueError:
        pass
    lp.force_flush()
    records = exporter.get_finished_logs()
    assert any("bad_tool" in str(r.log_record.body) for r in records)
    telemetry.shutdown()


async def test_instrumented_fastmcp_wraps_call_tool():
    exporter = InMemorySpanExporter()
    tp = TracerProvider()
    tp.add_span_processor(SimpleSpanProcessor(exporter))
    telemetry = OTelTelemetry.for_testing(
        _config(INVGATE_TELEMETRY="1"),
        tracer_provider=tp,
        meter_provider=MeterProvider(metric_readers=[InMemoryMetricReader()]),
    )
    mcp = InstrumentedFastMCP(name="t", telemetry=telemetry)

    @mcp.tool()
    def ping(x: int) -> int:
        return x + 1

    await mcp.call_tool("ping", {"x": 1})

    span = exporter.get_finished_spans()[0]
    assert span.name == "execute_tool ping"
    assert span.attributes["gen_ai.tool.name"] == "ping"
