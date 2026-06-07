import base64

import httpx
import pytest
import respx
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from invgate_service_desk_mcp._otel import OTelTelemetry
from invgate_service_desk_mcp.client import InvGateAPIError, InvGateClient
from invgate_service_desk_mcp.config import Config

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"
CONFIG = Config(base_url=BASE, api_token="tok-abc")


def _telemetry(exporter):
    tp = TracerProvider()
    tp.add_span_processor(SimpleSpanProcessor(exporter))
    return OTelTelemetry.for_testing(
        Config(base_url=BASE, api_token="t", telemetry_enabled=True),
        tracer_provider=tp,
        meter_provider=MeterProvider(metric_readers=[InMemoryMetricReader()]),
    )


@pytest.fixture
async def client():
    c = InvGateClient(CONFIG)
    yield c
    await c.aclose()


@respx.mock
async def test_get_sends_basic_auth_with_api_username_and_token(client):
    route = respx.get(f"{BASE}/api/v1/sd.version").mock(
        return_value=httpx.Response(200, json={"version": "10.1"})
    )

    await client.get("sd.version")

    assert route.called
    # InvGate SD uses HTTP Basic auth: username "api", password = API token.
    expected = "Basic " + base64.b64encode(b"api:tok-abc").decode()
    assert route.calls.last.request.headers["Authorization"] == expected


@respx.mock
async def test_get_builds_url_from_base_and_endpoint(client):
    route = respx.get(f"{BASE}/api/v1/incident").mock(
        return_value=httpx.Response(200, json={"id": 42})
    )

    await client.get("incident", params={"id": 42})

    assert route.called
    assert dict(route.calls.last.request.url.params) == {"id": "42"}


@respx.mock
async def test_get_returns_parsed_json(client):
    respx.get(f"{BASE}/api/v1/incident").mock(
        return_value=httpx.Response(200, json={"id": 42, "title": "Printer down"})
    )

    result = await client.get("incident", params={"id": 42})

    assert result == {"id": 42, "title": "Printer down"}


@respx.mock
async def test_api_error_redacts_credentials_leaked_in_body(client):
    # A misbehaving proxy/WAF could reflect the Authorization header in its error
    # body. The raised error must never carry our token or Basic credential.
    cred = base64.b64encode(b"api:tok-abc").decode()
    leaked = f"401 denied; header was Authorization: Basic {cred}; raw token=tok-abc"
    respx.get(f"{BASE}/api/v1/incident").mock(return_value=httpx.Response(401, text=leaked))

    with pytest.raises(InvGateAPIError) as exc:
        await client.get("incident")

    assert "tok-abc" not in str(exc.value)
    assert cred not in str(exc.value)
    assert "tok-abc" not in str(exc.value.body)
    assert cred not in str(exc.value.body)
    assert "REDACTED" in str(exc.value)


@respx.mock
async def test_api_error_truncates_huge_body(client):
    respx.get(f"{BASE}/api/v1/incident").mock(
        return_value=httpx.Response(500, text="x" * 5000)
    )

    with pytest.raises(InvGateAPIError) as exc:
        await client.get("incident")

    assert len(str(exc.value.body)) <= 1100  # capped, not the full 5000


@respx.mock
async def test_get_raises_api_error_on_http_error(client):
    respx.get(f"{BASE}/api/v1/incident").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )

    with pytest.raises(InvGateAPIError) as exc:
        await client.get("incident", params={"id": 999})

    assert exc.value.status_code == 404


@respx.mock
async def test_get_encodes_list_params_php_style(client):
    # InvGate expects ARRAY params as ids[]=1&ids[]=2, not repeated ids=1&ids=2.
    route = respx.get(f"{BASE}/api/v1/users.groups").mock(
        return_value=httpx.Response(200, json=[])
    )

    await client.get("users.groups", params={"ids": [1, 2]})

    params = route.calls.last.request.url.params
    assert params.get_list("ids[]") == ["1", "2"]
    assert params.get_list("ids") == []


async def test_writes_enabled_reflects_config():
    off = InvGateClient(CONFIG)
    on = InvGateClient(Config(base_url=BASE, api_token="tok-abc", enable_writes=True))
    try:
        assert off.writes_enabled is False
        assert on.writes_enabled is True
    finally:
        await off.aclose()
        await on.aclose()


def _profile_client(**kw):
    return InvGateClient(Config(base_url=BASE, api_token="tok-abc", **kw))


def test_writes_enabled_for_support_profile():
    client = _profile_client(write_profile="support")
    assert client.writes_enabled_for("incidents") is True
    assert client.writes_enabled_for("timetracking") is True
    assert client.writes_enabled_for("kb") is False


def test_writes_enabled_for_full_profile():
    client = _profile_client(write_profile="full")
    assert client.writes_enabled_for("kb") is True


def test_writes_enabled_for_none_profile():
    client = _profile_client()
    assert client.writes_enabled_for("incidents") is False


def test_writes_enabled_is_any_write():
    assert _profile_client().writes_enabled is False
    assert _profile_client(write_profile="support").writes_enabled is True


@respx.mock
async def test_post_sends_form_data_and_drops_none(client):
    route = respx.post(f"{BASE}/api/v1/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK", "article_id": 5})
    )

    result = await client.post("kb.articles", data={"title": "Hi", "responsible_id": None})

    assert result == {"status": "OK", "article_id": 5}
    body = bytes(route.calls.last.request.content).decode()
    assert "title=Hi" in body
    assert "responsible_id" not in body


@respx.mock
async def test_put_sends_form_data(client):
    route = respx.put(f"{BASE}/api/v1/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    await client.put("kb.articles", data={"id": 7, "author_id": 18})

    body = bytes(route.calls.last.request.content).decode()
    assert "id=7" in body
    assert "author_id=18" in body


@respx.mock
async def test_delete_sends_query_params(client):
    route = respx.delete(f"{BASE}/api/v1/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    await client.delete("kb.articles", params={"id": 7})

    assert dict(route.calls.last.request.url.params) == {"id": "7"}


@respx.mock
async def test_get_drops_none_valued_params(client):
    route = respx.get(f"{BASE}/api/v1/incidents.by.status").mock(
        return_value=httpx.Response(200, json=[])
    )

    await client.get("incidents.by.status", params={"status_id": 1, "page_key": None})

    assert dict(route.calls.last.request.url.params) == {"status_id": "1"}


@respx.mock
async def test_client_get_emits_a_span_with_status():
    exporter = InMemorySpanExporter()
    client = InvGateClient(Config(base_url=BASE, api_token="t"), telemetry=_telemetry(exporter))
    respx.get(f"{API}/incident").mock(return_value=httpx.Response(200, json={"id": 1}))

    await client.get("incident", params={"id": 1})
    await client.aclose()

    span = exporter.get_finished_spans()[0]
    assert span.attributes["invgate.endpoint"] == "incident"
    assert span.attributes["http.request.method"] == "GET"
    assert span.attributes["http.response.status_code"] == 200


@respx.mock
async def test_client_works_without_telemetry():
    client = InvGateClient(Config(base_url=BASE, api_token="t"))
    respx.get(f"{API}/incident").mock(return_value=httpx.Response(200, json={"id": 1}))
    result = await client.get("incident", params={"id": 1})
    await client.aclose()
    assert result == {"id": 1}
