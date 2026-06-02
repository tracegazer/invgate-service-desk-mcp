import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import triggers as trg

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_list_triggers(client):
    route = respx.get(f"{API}/triggers").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "trigger_name": "Auto-assign"}])
    )

    result = await trg.list_triggers(client)

    assert result == [{"id": 1, "trigger_name": "Auto-assign"}]
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_triggers_by_id(client):
    route = respx.get(f"{API}/triggers").mock(return_value=httpx.Response(200, json=[]))

    await trg.list_triggers(client, trigger_id=7)

    assert dict(route.calls.last.request.url.params) == {"trigger_id": "7"}


@respx.mock
async def test_list_trigger_executions(client):
    route = respx.get(f"{API}/triggers.executions").mock(
        return_value=httpx.Response(200, json=[{"executed_at": 1700000000}])
    )

    result = await trg.list_trigger_executions(client, trigger_id=7)

    assert result == [{"executed_at": 1700000000}]
    assert dict(route.calls.last.request.url.params) == {"trigger_id": "7"}
