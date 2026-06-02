"""Tests for the catalog/reference-data domain."""

from __future__ import annotations

import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import catalog

BASE = "https://acme.sd.cloud.invgate.net/api/v1"


@pytest.fixture
def client():
    config = Config(base_url="https://acme.sd.cloud.invgate.net", api_token="tok")
    return InvGateClient(config, http_client=httpx.AsyncClient(base_url=BASE))


# --- Individual tool tests ---------------------------------------------------


@respx.mock
async def test_list_priorities(client):
    payload = [{"id": 1, "name": "Low"}, {"id": 2, "name": "Medium"}]
    respx.get(f"{BASE}/incident.attributes.priority").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_priorities(client)
    assert result == payload


@respx.mock
async def test_list_priorities_by_id(client):
    payload = [{"id": 3, "name": "High"}]
    respx.get(f"{BASE}/incident.attributes.priority", params={"id": "3"}).mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_priorities(client, id=3)
    assert result == payload


@respx.mock
async def test_list_statuses(client):
    payload = [{"id": 1, "name": "Open"}, {"id": 2, "name": "In Progress"}]
    respx.get(f"{BASE}/incident.attributes.status").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_statuses(client)
    assert result == payload


@respx.mock
async def test_list_incident_types(client):
    payload = [{"id": 1, "name": "Incident"}, {"id": 2, "name": "Service Request"}]
    respx.get(f"{BASE}/incident.attributes.type").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_incident_types(client)
    assert result == payload


@respx.mock
async def test_list_categories(client):
    payload = [{"id": 10, "name": "Network", "parent_category_id": None}]
    respx.get(f"{BASE}/incident.attributes.category").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_categories(client)
    assert result == payload


@respx.mock
async def test_list_categories_with_search_and_pagination(client):
    payload = [{"id": 20, "name": "Network LAN", "parent_category_id": 10}]
    respx.get(
        f"{BASE}/incident.attributes.category",
        params={"search": "network", "page": "1", "page_size": "50"},
    ).mock(return_value=httpx.Response(200, json=payload))
    result = await catalog.list_categories(client, search="network", page=1, page_size=50)
    assert result == payload


@respx.mock
async def test_list_sources(client):
    payload = [{"id": 1, "name": "Portal"}, {"id": 2, "name": "Email"}]
    respx.get(f"{BASE}/incident.attributes.source").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await catalog.list_sources(client)
    assert result == payload


# --- Registration test --------------------------------------------------------


def test_catalog_register_adds_tools():
    from unittest.mock import MagicMock

    mcp = MagicMock()
    # mcp.tool() returns a decorator; the decorator is called with the function.
    decorator = MagicMock(side_effect=lambda fn: fn)
    mcp.tool.return_value = decorator
    mock_client = MagicMock(spec=InvGateClient)

    catalog.register(mcp, mock_client)

    assert mcp.tool.call_count == 5
    registered = {call.args[0].__name__ for call in decorator.call_args_list}
    assert registered == {
        "list_priorities",
        "list_statuses",
        "list_incident_types",
        "list_categories",
        "list_sources",
    }
