"""Live smoke test against a real InvGate Service Desk instance.

Skipped by default. Opt in with INVGATE_LIVE_TEST=1 and real credentials in env:

    INVGATE_LIVE_TEST=1 \
    INVGATE_BASE_URL="https://acme.sd.cloud.invgate.net" \
    INVGATE_API_TOKEN="..." \
    python -m pytest tests/test_live_smoke.py -v

Never runs in CI: the guard env var is intentionally absent there.
"""

from __future__ import annotations

import os

import pytest

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import incidents, timetracking, users

pytestmark = pytest.mark.skipif(
    os.environ.get("INVGATE_LIVE_TEST") != "1",
    reason="Set INVGATE_LIVE_TEST=1 (plus real credentials) to run the live smoke test.",
)

# Override with your own instance IDs via env vars.
SMOKE_INCIDENT_ID = int(os.environ.get("INVGATE_SMOKE_INCIDENT_ID", "1"))


@pytest.fixture
async def live_client():
    config = Config.load(os.environ)
    client = InvGateClient(config)
    yield client
    await client.aclose()


async def test_live_basic_auth_fetches_incident(live_client):
    result = await live_client.get("incident", params={"id": SMOKE_INCIDENT_ID})

    # InvGate returns the single incident as an object when filtered by id.
    incident = result[0] if isinstance(result, list) else result
    assert incident["id"] == SMOKE_INCIDENT_ID
    assert incident.get("pretty_id") == f"#{SMOKE_INCIDENT_ID}"


# --- Normalization contract: incident collections must come back as flat lists.
# These catch a SILENT change to InvGate's collection envelopes. If the API
# stops returning the {requests: {...}} / {requestIds: [...]} shapes, unwrap_list
# passes the raw payload through and the isinstance(list) assertions fail loudly,
# instead of the change going unnoticed until production.

SMOKE_AGENT_ID = int(os.environ.get("INVGATE_SMOKE_AGENT_ID", "1"))
SMOKE_STATUS_ID = int(os.environ.get("INVGATE_SMOKE_STATUS_ID", "1"))


async def test_live_incidents_by_agent_returns_flat_list_of_objects(live_client):
    result = await incidents.list_incidents_by_agent(live_client, id=SMOKE_AGENT_ID)

    # {status, info, requests: {id: obj}} envelope -> list of objects.
    assert isinstance(result, list)
    if result:
        assert isinstance(result[0], dict)
        assert "id" in result[0]


async def test_live_incidents_by_status_returns_flat_list_of_ids(live_client):
    result = await incidents.list_incidents_by_status(
        live_client, status_id=SMOKE_STATUS_ID
    )

    # {status, info, requestIds: [...]} envelope -> list of ids.
    assert isinstance(result, list)
    if result:
        assert all(isinstance(request_id, int) for request_id in result[:10])


# --- Phase 2: Users/Groups domain (read-only) -------------------------------


async def test_live_list_groups(live_client):
    result = await users.list_groups(live_client)

    assert isinstance(result, list)
    if result:  # instance may have zero groups, but shape must hold
        assert "id" in result[0]
        assert "name" in result[0]


async def test_live_list_companies(live_client):
    result = await users.list_companies(live_client)

    assert isinstance(result, list)
    if result:
        assert "id" in result[0]
        assert "name" in result[0]


# --- Phase 8: Time tracking domain (read-only) ------------------------------


async def test_live_list_time_tracking_categories(live_client):
    result = await timetracking.list_time_tracking_categories(live_client)

    assert isinstance(result, list)
    if result:
        assert "id" in result[0]
        assert "name" in result[0]


# NOTE: no live write test for time tracking. The InvGate API does not support
# deletion of time entries (they are permanent), so any live write test would
# irreversibly pollute the instance. Shape coverage is in tests/test_timetracking.py.
