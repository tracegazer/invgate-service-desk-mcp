import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import workflows as wf

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_get_workflow_initial_fields(client):
    route = respx.get(f"{API}/wf.initialfields.by.category").mock(
        return_value=httpx.Response(200, json=[])
    )

    await wf.get_workflow_initial_fields(client, category_id=200)

    assert dict(route.calls.last.request.url.params) == {"category_id": "200"}


@respx.mock
async def test_get_workflow_process_lists_all_with_iso_dates(client):
    route = respx.get(f"{API}/workflow.process").mock(
        return_value=httpx.Response(200, json={"next_page_key": None, "data": []})
    )

    await wf.get_workflow_process(client)

    assert dict(route.calls.last.request.url.params) == {"date_format": "iso8601"}


@respx.mock
async def test_get_workflow_process_by_id_with_paging(client):
    route = respx.get(f"{API}/workflow.process").mock(
        return_value=httpx.Response(200, json={"next_page_key": "k", "data": []})
    )

    await wf.get_workflow_process(client, process_id=5, page_key="abc", limit=10)

    params = dict(route.calls.last.request.url.params)
    assert params == {"id": "5", "date_format": "iso8601", "page_key": "abc", "limit": "10"}


@respx.mock
async def test_get_workflow_field_list_values(client):
    route = respx.get(f"{API}/workflow.field.list.values").mock(
        return_value=httpx.Response(200, json={"values": []})
    )

    await wf.get_workflow_field_list_values(client, request_id=42, field_id=9)

    assert dict(route.calls.last.request.url.params) == {"request_id": "42", "field_id": "9"}
