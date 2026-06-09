import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import incidents
from invgate_service_desk_mcp.normalize import UnexpectedShapeError

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_get_incident_requests_by_id_with_iso_dates_by_default(client):
    route = respx.get(f"{API}/incident").mock(
        return_value=httpx.Response(200, json={"id": 42, "title": "Printer down"})
    )

    result = await incidents.get_incident(client, incident_id=42)

    assert result == {"id": 42, "title": "Printer down"}
    assert dict(route.calls.last.request.url.params) == {
        "id": "42",
        "date_format": "iso8601",
    }


@respx.mock
async def test_get_incident_can_include_comments(client):
    route = respx.get(f"{API}/incident").mock(return_value=httpx.Response(200, json={}))

    await incidents.get_incident(client, incident_id=42, include_comments=True)

    assert route.calls.last.request.url.params["comments"] == "true"


@respx.mock
async def test_list_incidents_by_status_passes_status_id(client):
    route = respx.get(f"{API}/incidents.by.status").mock(
        return_value=httpx.Response(200, json=[{"id": 1}])
    )

    result = await incidents.list_incidents_by_status(client, status_id=2)

    assert result == [{"id": 1}]
    assert dict(route.calls.last.request.url.params) == {"status_id": "2"}


@respx.mock
async def test_list_incidents_by_status_supports_limit_and_offset(client):
    route = respx.get(f"{API}/incidents.by.status").mock(
        return_value=httpx.Response(200, json=[])
    )

    await incidents.list_incidents_by_status(client, status_id=2, limit=50, offset=100)

    params = dict(route.calls.last.request.url.params)
    assert params == {"status_id": "2", "limit": "50", "offset": "100"}


@respx.mock
async def test_list_incidents_by_agent_accepts_email(client):
    route = respx.get(f"{API}/incidents.by.agent").mock(
        return_value=httpx.Response(200, json=[])
    )

    await incidents.list_incidents_by_agent(client, email="agent@acme.com")

    assert dict(route.calls.last.request.url.params) == {"email": "agent@acme.com"}


async def test_list_incidents_by_agent_requires_an_identifier(client):
    with pytest.raises(ValueError, match="id, email or username"):
        await incidents.list_incidents_by_agent(client)


@respx.mock
async def test_list_incidents_by_helpdesk_flattens_request_ids(client):
    route = respx.get(f"{API}/incidents.by.helpdesk").mock(
        return_value=httpx.Response(200, json={"status": "OK", "requestIds": [1, 2]})
    )

    result = await incidents.list_incidents_by_helpdesk(client, helpdesk_id=2)

    # The {status, requestIds: [...]} envelope is flattened to a plain list.
    assert result == [1, 2]
    assert dict(route.calls.last.request.url.params) == {"helpdesk_id": "2"}


@respx.mock
async def test_list_incidents_by_agent_raises_on_unexpected_shape(client):
    # A response that is neither a list nor a known envelope signals a changed
    # API contract; the agent gets a loud, typed error instead of a raw dict.
    respx.get(f"{API}/incidents.by.agent").mock(
        return_value=httpx.Response(200, json={"status": "ERROR"})
    )

    with pytest.raises(UnexpectedShapeError, match=r"incidents\.by\.agent"):
        await incidents.list_incidents_by_agent(client, id=18)


@respx.mock
async def test_list_incidents_by_agent_flattens_requests_map(client):
    envelope = {
        "status": "OK",
        "info": "Returned a list of the requests related to the given agent.",
        "requests": {
            "20318": {"id": 20318, "title": "A"},
            "21574": {"id": 21574, "title": "B"},
        },
    }
    respx.get(f"{API}/incidents.by.agent").mock(
        return_value=httpx.Response(200, json=envelope)
    )

    result = await incidents.list_incidents_by_agent(client, id=18)

    # The {status, info, requests: {id: obj}} envelope becomes a list of objects.
    assert result == [{"id": 20318, "title": "A"}, {"id": 21574, "title": "B"}]


@respx.mock
async def test_get_incident_comments_requires_request_id(client):
    route = respx.get(f"{API}/incident.comment").mock(
        return_value=httpx.Response(200, json=[{"comment": "hi"}])
    )

    result = await incidents.get_incident_comments(client, request_id=42)

    assert result == [{"comment": "hi"}]
    assert dict(route.calls.last.request.url.params) == {
        "request_id": "42",
        "date_format": "iso8601",
    }
