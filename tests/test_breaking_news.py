import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import breaking_news as bn

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_get_breaking_news_by_id_with_iso_dates(client):
    route = respx.get(f"{API}/breakingnews").mock(
        return_value=httpx.Response(200, json={"id": 3, "title": "Outage"})
    )

    result = await bn.get_breaking_news(client, breaking_news_id=3)

    assert result == {"id": 3, "title": "Outage"}
    assert dict(route.calls.last.request.url.params) == {"id": "3", "date_format": "iso8601"}


@respx.mock
async def test_list_breaking_news(client):
    route = respx.get(f"{API}/breakingnews.all").mock(
        return_value=httpx.Response(200, json=[])
    )

    await bn.list_breaking_news(client)

    assert dict(route.calls.last.request.url.params) == {"date_format": "iso8601"}


@respx.mock
async def test_get_breaking_news_status(client):
    route = respx.get(f"{API}/breakingnews.status").mock(
        return_value=httpx.Response(200, json={"id": 3, "updates": []})
    )

    await bn.get_breaking_news_status(client, breaking_news_id=3)

    assert dict(route.calls.last.request.url.params) == {"id": "3", "date_format": "iso8601"}


@respx.mock
async def test_list_breaking_news_types(client):
    route = respx.get(f"{API}/breakingnews.attributes.type").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "High"}])
    )

    result = await bn.list_breaking_news_types(client)

    assert result == [{"id": 1, "name": "High"}]
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_breaking_news_statuses_by_id(client):
    route = respx.get(f"{API}/breakingnews.attributes.status").mock(
        return_value=httpx.Response(200, json=[{"id": 2, "name": "Active"}])
    )

    await bn.list_breaking_news_statuses(client, status_id=2)

    assert dict(route.calls.last.request.url.params) == {"id": "2"}
