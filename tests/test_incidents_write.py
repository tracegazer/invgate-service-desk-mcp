"""Write-operation tests for the incidents domain (Phase 7).

The module-level functions work regardless of the opt-in; registration as MCP
tools is gated separately (see test_server). POST/PUT send form params, DELETE
uses query params.
"""

import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import incidents

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


def form(route):
    return bytes(route.calls.last.request.content).decode()


@respx.mock
async def test_create_incident(client):
    route = respx.post(f"{API}/incident").mock(
        return_value=httpx.Response(200, json={"id": 100})
    )

    result = await incidents.create_incident(
        client,
        creator_id=1,
        customer_id=2,
        category_id=3,
        priority_id=2,
        type_id=1,
        title="Printer down",
        description="<p>broken</p>",
    )

    assert result == {"id": 100}
    body = form(route)
    for token in ("creator_id=1", "customer_id=2", "category_id=3", "priority_id=2",
                  "type_id=1", "title=Printer+down"):
        assert token in body


@respx.mock
async def test_update_incident_maps_id(client):
    route = respx.put(f"{API}/incident").mock(return_value=httpx.Response(200, json={}))

    await incidents.update_incident(client, incident_id=100, priority_id=3, reassignment=True)

    body = form(route)
    assert "id=100" in body
    assert "priority_id=3" in body
    assert "reassignment=1" in body  # bool -> 1/0


@respx.mock
async def test_reopen_incident(client):
    route = respx.put(f"{API}/incident.reopen").mock(return_value=httpx.Response(200, json={}))

    await incidents.reopen_incident(client, request_id=100, author_id=5)

    body = form(route)
    assert "request_id=100" in body
    assert "author_id=5" in body


@respx.mock
async def test_reject_incident(client):
    route = respx.post(f"{API}/incident.reject").mock(return_value=httpx.Response(200, json={}))

    await incidents.reject_incident(client, request_id=100, author_id=5)

    body = form(route)
    assert "request_id=100" in body and "author_id=5" in body


@respx.mock
async def test_cancel_incident_with_comment(client):
    route = respx.post(f"{API}/incident.cancel").mock(return_value=httpx.Response(200, json={}))

    await incidents.cancel_incident(client, request_id=100, author_id=5, comment="dup")

    body = form(route)
    assert "request_id=100" in body and "comment=dup" in body


@respx.mock
async def test_promote_incident_to_major(client):
    route = respx.post(f"{API}/incident.promote.to.major.incident").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.promote_incident_to_major(client, request_id=100, author_id=5, confirm=True)

    body = form(route)
    assert "request_id=100" in body and "confirm=1" in body


@respx.mock
async def test_reassign_incident(client):
    route = respx.post(f"{API}/incident.reassign").mock(return_value=httpx.Response(200, json={}))

    await incidents.reassign_incident(client, request_id=100, author_id=5, group_id=159, agent_id=343)

    body = form(route)
    for token in ("request_id=100", "author_id=5", "group_id=159", "agent_id=343"):
        assert token in body


@respx.mock
async def test_add_incident_comment(client):
    route = respx.post(f"{API}/incident.comment").mock(return_value=httpx.Response(200, json={}))

    await incidents.add_incident_comment(
        client, request_id=100, comment="hello", author_id=5, is_solution=True
    )

    body = form(route)
    assert "request_id=100" in body and "comment=hello" in body and "is_solution=1" in body


@respx.mock
async def test_set_incident_custom_field_encodes_values(client):
    route = respx.post(f"{API}/incident.custom_field").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    await incidents.set_incident_custom_field(
        client, request_id=100, author_id=5, custom_field_uid=328, values=["A", "B"]
    )

    body = form(route)
    assert "custom_field_uid=328" in body
    assert "values%5B%5D=A" in body and "values%5B%5D=B" in body  # values[]=A&values[]=B


@respx.mock
async def test_delete_incident_custom_field_uses_query(client):
    route = respx.delete(f"{API}/incident.custom_field").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    await incidents.delete_incident_custom_field(
        client, request_id=100, author_id=5, custom_field_uid=328
    )

    assert dict(route.calls.last.request.url.params) == {
        "request_id": "100",
        "author_id": "5",
        "custom_field_uid": "328",
    }


@respx.mock
async def test_add_incident_observer(client):
    route = respx.post(f"{API}/incident.observer").mock(return_value=httpx.Response(200, json={}))

    await incidents.add_incident_observer(client, request_id=100, author_id=5, user_id=7)

    body = form(route)
    assert "request_id=100" in body and "user_id=7" in body


@respx.mock
async def test_add_incident_collaborator(client):
    route = respx.post(f"{API}/incident.collaborator").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.add_incident_collaborator(client, request_id=100, author_id=5, user_ids=[7, 8])

    body = form(route)
    assert "users_id%5B%5D=7" in body and "users_id%5B%5D=8" in body


@respx.mock
async def test_link_incident_encodes_request_ids(client):
    route = respx.post(f"{API}/incident.link").mock(return_value=httpx.Response(200, json={}))

    await incidents.link_incident(client, request_id=100, request_ids=[101, 102])

    body = form(route)
    assert "request_ids%5B%5D=101" in body and "request_ids%5B%5D=102" in body


@respx.mock
async def test_link_incident_to_external_entity(client):
    route = respx.post(f"{API}/incident.external_entity").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.link_incident_to_external_entity(
        client, request_id=100, external_entity_id=9
    )

    body = form(route)
    assert "request_id=100" in body and "external_entity_id=9" in body


@respx.mock
async def test_relate_incident_to_cis_by_keyword(client):
    route = respx.post(f"{API}/incident.relate.ci.by.keyword").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.relate_incident_to_cis_by_keyword(
        client, request_id=100, keyword="laptop", exact_match=True
    )

    body = form(route)
    assert "keyword=laptop" in body and "exact_match=1" in body


@respx.mock
async def test_set_incident_waiting_for_incident(client):
    route = respx.post(f"{API}/incident.waitingfor.incident").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.set_incident_waiting_for_incident(client, request_id=100, wait_request_id=200)

    body = form(route)
    assert "request_id=100" in body and "wait_request_id=200" in body


@respx.mock
async def test_set_incident_waiting_for_external_entity(client):
    route = respx.post(f"{API}/incident.waitingfor.external_entity").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.set_incident_waiting_for_external_entity(
        client, request_id=100, entity_link_id=9
    )

    assert "entity_link_id=9" in form(route)


@respx.mock
async def test_set_incident_waiting_for_agent(client):
    route = respx.post(f"{API}/incident.waitingfor.agent").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.set_incident_waiting_for_agent(client, request_id=100)

    assert "request_id=100" in form(route)


@respx.mock
async def test_set_incident_waiting_for_customer(client):
    route = respx.post(f"{API}/incident.waitingfor.customer").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.set_incident_waiting_for_customer(client, request_id=100)

    assert "request_id=100" in form(route)


@respx.mock
async def test_set_incident_waiting_for_date(client):
    route = respx.post(f"{API}/incident.waitingfor.date").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.set_incident_waiting_for_date(client, request_id=100, timestamp=1780000000)

    body = form(route)
    assert "request_id=100" in body and "timestamp=1780000000" in body


@respx.mock
async def test_accept_incident_approval(client):
    route = respx.put(f"{API}/incident.approval.accept").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.accept_incident_approval(client, approval_id=11, user_id=5, note="ok")

    body = form(route)
    assert "approval_id=11" in body and "user_id=5" in body and "note=ok" in body


@respx.mock
async def test_reject_incident_approval(client):
    route = respx.put(f"{API}/incident.approval.reject").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.reject_incident_approval(client, approval_id=11, user_id=5)

    body = form(route)
    assert "approval_id=11" in body and "user_id=5" in body


@respx.mock
async def test_cancel_incident_approval(client):
    route = respx.put(f"{API}/incident.approval.cancel").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.cancel_incident_approval(client, approval_id=11, user_id=5)

    assert "approval_id=11" in form(route)


@respx.mock
async def test_add_incident_approval_voter(client):
    route = respx.post(f"{API}/incident.approval.add_voter").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.add_incident_approval_voter(client, approval_id=11, user_id=7)

    body = form(route)
    assert "approval_id=11" in body and "user_id=7" in body


@respx.mock
async def test_create_incident_spontaneous_approval(client):
    route = respx.post(f"{API}/incident.spontaneous_approval").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.create_incident_spontaneous_approval(
        client, request_id=100, author_id=5, approval_user_id=9, description="please approve"
    )

    body = form(route)
    assert "approval_user_id=9" in body and "description=please+approve" in body


@respx.mock
async def test_request_incident_custom_approval(client):
    route = respx.post(f"{API}/incident.custom_approval").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.request_incident_custom_approval(
        client, request_id=100, author_id=5, approval_id=3
    )

    body = form(route)
    assert "request_id=100" in body and "approval_id=3" in body


@respx.mock
async def test_accept_incident_solution(client):
    route = respx.put(f"{API}/incident.solution.accept").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.accept_incident_solution(client, incident_id=100, rating=5, comment="thanks")

    body = form(route)
    assert "id=100" in body and "rating=5" in body and "comment=thanks" in body


@respx.mock
async def test_reject_incident_solution(client):
    route = respx.put(f"{API}/incident.solution.reject").mock(
        return_value=httpx.Response(200, json={})
    )

    await incidents.reject_incident_solution(client, incident_id=100, comment="not fixed")

    body = form(route)
    assert "id=100" in body and "comment=not+fixed" in body
