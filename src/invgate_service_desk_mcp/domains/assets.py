"""Assets & CIs domain (Phase 6, read-only).

Thin, typed wrappers over the read-only asset/CI endpoints. Assets and CIs live
in InvGate's inventory module and are referenced by a source ID plus their IDs.
These tools surface the requests linked to assets/CIs, the CIs themselves, and
status counters. Linking CIs to requests (write) is deferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient
from ..normalize import as_list

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def list_incidents_by_asset(client: InvGateClient, asset_id: int) -> Any:
    """List the requests related to an asset."""
    return as_list(
        await client.get("incidents.by.asset", params={"asset_id": asset_id}),
        source="incidents.by.asset",
    )


async def list_requests_related_to_assets(
    client: InvGateClient, assets_source_id: int, asset_ids: list[int]
) -> Any:
    """List the requests related to assets, by inventory source ID and asset IDs."""
    return as_list(
        await client.get(
            "assets",
            params={"assets_source_id": assets_source_id, "assets_ids": asset_ids},
        ),
        source="assets",
    )


async def get_linked_assets_counters(
    client: InvGateClient, assets_source_id: int, from_status: str
) -> Any:
    """Get counters of linked assets from a given starting point."""
    return await client.get(
        "assets.linked.assets.counters.from",
        params={"assets_source_id": assets_source_id, "from": from_status},
    )


async def get_cis_by_id(
    client: InvGateClient, ci_source_id: int, ci_internal_ids: list[int]
) -> Any:
    """Get CIs by their internal IDs and inventory source ID."""
    return await client.get(
        "cis.by.id",
        params={"ci_source_id": ci_source_id, "ci_internal_ids": ci_internal_ids},
    )


async def list_incidents_by_cis(
    client: InvGateClient,
    cis_source_id: int,
    *,
    ci_ids: list[int] | None = None,
    group: str | None = None,
) -> Any:
    """List the requests linked to CIs, by inventory source ID and CI IDs."""
    return as_list(
        await client.get(
            "incidents.by.cis",
            params={"cis_source_id": cis_source_id, "group": group, "ci_ids": ci_ids},
        ),
        source="incidents.by.cis",
    )


async def get_linked_cis_counters(
    client: InvGateClient, cis_source_id: int, from_status: str
) -> Any:
    """Get counters of incidents per status for CIs from a given starting point."""
    return await client.get(
        "incident.linked_cis.counters.from",
        params={"cis_source_id": cis_source_id, "from": from_status},
    )


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only asset/CI tools on the given MCP server."""

    @mcp.tool()
    async def list_incidents_by_asset(asset_id: int) -> Any:
        """List the requests related to an asset."""
        return await list_incidents_by_asset_fn(client, asset_id)

    @mcp.tool()
    async def list_requests_related_to_assets(
        assets_source_id: int, asset_ids: list[int]
    ) -> Any:
        """List the requests related to assets (by source ID and asset IDs)."""
        return await list_requests_related_to_assets_fn(
            client, assets_source_id, asset_ids
        )

    @mcp.tool()
    async def get_linked_assets_counters(assets_source_id: int, from_status: str) -> Any:
        """Get counters of linked assets from a given starting point."""
        return await get_linked_assets_counters_fn(client, assets_source_id, from_status)

    @mcp.tool()
    async def get_cis_by_id(ci_source_id: int, ci_internal_ids: list[int]) -> Any:
        """Get CIs by their internal IDs and inventory source ID."""
        return await get_cis_by_id_fn(client, ci_source_id, ci_internal_ids)

    @mcp.tool()
    async def list_incidents_by_cis(
        cis_source_id: int,
        ci_ids: list[int] | None = None,
        group: str | None = None,
    ) -> Any:
        """List the requests linked to CIs (by source ID and CI IDs)."""
        return await list_incidents_by_cis_fn(
            client, cis_source_id, ci_ids=ci_ids, group=group
        )

    @mcp.tool()
    async def get_linked_cis_counters(cis_source_id: int, from_status: str) -> Any:
        """Get counters of incidents per status for CIs from a given starting point."""
        return await get_linked_cis_counters_fn(client, cis_source_id, from_status)


# Aliases so the tool wrappers above can call the module-level implementations.
list_incidents_by_asset_fn = list_incidents_by_asset
list_requests_related_to_assets_fn = list_requests_related_to_assets
get_linked_assets_counters_fn = get_linked_assets_counters
get_cis_by_id_fn = get_cis_by_id
list_incidents_by_cis_fn = list_incidents_by_cis
get_linked_cis_counters_fn = get_linked_cis_counters
