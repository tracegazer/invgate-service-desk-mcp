"""Catalog / reference data domain.

Exposes the lookup tables an AI agent needs to discover valid IDs before
creating or modifying incidents: priorities, statuses, types, categories,
and sources. All read-only, no opt-in required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def list_priorities(client: InvGateClient, *, id: int | None = None) -> Any:
    """List incident priorities (e.g. Low, Medium, High, Urgent, Critical)."""
    return await client.get("incident.attributes.priority", params={"id": id})


async def list_statuses(client: InvGateClient, *, id: int | None = None) -> Any:
    """List incident statuses."""
    return await client.get("incident.attributes.status", params={"id": id})


async def list_incident_types(client: InvGateClient, *, id: int | None = None) -> Any:
    """List incident types (e.g. Incident, Service Request, Problem, Change)."""
    return await client.get("incident.attributes.type", params={"id": id})


async def list_categories(
    client: InvGateClient,
    *,
    id: int | None = None,
    search: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> Any:
    """List incident categories. Hierarchical via parent_category_id. Supports search."""
    return await client.get(
        "incident.attributes.category",
        params={"id": id, "search": search, "page": page, "page_size": page_size},
    )


async def list_sources(client: InvGateClient, *, id: int | None = None) -> Any:
    """List incident sources (e.g. Portal, Email, Phone, API)."""
    return await client.get("incident.attributes.source", params={"id": id})


def register(mcp: FastMCP, client: InvGateClient) -> None:
    """Register the catalog/reference-data tools on the given MCP server."""

    @mcp.tool()
    async def list_priorities(id: int | None = None) -> Any:
        """List incident priorities (e.g. Low, Medium, High, Urgent, Critical)."""
        return await list_priorities_fn(client, id=id)

    @mcp.tool()
    async def list_statuses(id: int | None = None) -> Any:
        """List incident statuses."""
        return await list_statuses_fn(client, id=id)

    @mcp.tool()
    async def list_incident_types(id: int | None = None) -> Any:
        """List incident types (e.g. Incident, Service Request, Problem, Change)."""
        return await list_incident_types_fn(client, id=id)

    @mcp.tool()
    async def list_categories(
        id: int | None = None,
        search: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Any:
        """List incident categories. Hierarchical via parent_category_id. Supports search."""
        return await list_categories_fn(
            client, id=id, search=search, page=page, page_size=page_size
        )

    @mcp.tool()
    async def list_sources(id: int | None = None) -> Any:
        """List incident sources (e.g. Portal, Email, Phone, API)."""
        return await list_sources_fn(client, id=id)


list_priorities_fn = list_priorities
list_statuses_fn = list_statuses
list_incident_types_fn = list_incident_types
list_categories_fn = list_categories
list_sources_fn = list_sources
