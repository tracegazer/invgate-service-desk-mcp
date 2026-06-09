"""Organizational structure domain (Phase 5, read-only).

Thin, typed wrappers over the read-only help desk, level, location and company
sub-resource endpoints. These describe how the service desk is organized: help
desks and their levels, locations and their members, and company membership and
observers.

``list_companies`` (the top-level company list) already lives in the users
domain; this module adds the company sub-resources (members/groups/observers).
Managing observers and company/location membership (writes) is deferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


# --- Help desks & levels -----------------------------------------------------


async def list_helpdesks(
    client: InvGateClient,
    *,
    helpdesk_id: int | None = None,
    name: str | None = None,
    include_deleted: bool = False,
) -> Any:
    """List active help desks, or one in particular by ID or name."""
    return await client.get(
        "helpdesks",
        params={
            "id": helpdesk_id,
            "name": name,
            "include_deleted": True if include_deleted else None,
        },
    )


async def list_helpdesk_levels(
    client: InvGateClient,
    *,
    level_id: int | None = None,
    include_deleted: bool = False,
) -> Any:
    """List active help desk levels, or one in particular by ID."""
    return await client.get(
        "levels",
        params={"id": level_id, "include_deleted": True if include_deleted else None},
    )


async def list_helpdesks_and_levels(
    client: InvGateClient,
    *,
    helpdesk_id: int | None = None,
    include_deleted: bool = False,
) -> Any:
    """List help desks together with their levels, or one in particular by ID."""
    return await client.get(
        "helpdesksandlevels",
        params={"id": helpdesk_id, "include_deleted": True if include_deleted else None},
    )


async def list_helpdesk_observers(
    client: InvGateClient, *, ids: list[int] | None = None
) -> Any:
    """List help desks and their observers, optionally filtered to specific IDs."""
    return await client.get("helpdesks.observers", params={"ids": ids})


async def list_level_observers(
    client: InvGateClient, *, ids: list[int] | None = None
) -> Any:
    """List help desk levels and their observers, optionally filtered to specific IDs."""
    return await client.get("levels.observers", params={"ids": ids})


# --- Locations ---------------------------------------------------------------


async def list_locations(client: InvGateClient, *, location_id: int | None = None) -> Any:
    """List active locations, or one in particular by ID."""
    return await client.get("locations", params={"id": location_id})


async def list_location_members(
    client: InvGateClient, location_id: int, *, user_id: int | None = None
) -> Any:
    """List the members of a location, optionally checking a single user."""
    return await client.get(
        "locations.users", params={"id": location_id, "user_id": user_id}
    )


async def list_location_observers(
    client: InvGateClient, *, ids: list[int] | None = None
) -> Any:
    """List locations and their observers, optionally filtered to specific IDs."""
    return await client.get("locations.observers", params={"ids": ids})


# --- Company sub-resources ---------------------------------------------------


async def list_company_members(
    client: InvGateClient, company_id: int, *, user_id: int | None = None
) -> Any:
    """List the members of a company, optionally checking a single user."""
    return await client.get(
        "companies.users", params={"id": company_id, "user_id": user_id}
    )


async def list_company_groups(client: InvGateClient, company_id: int) -> Any:
    """List the user groups related to a company."""
    return await client.get("companies.groups", params={"id": company_id})


async def list_company_observers(
    client: InvGateClient, *, ids: list[int] | None = None
) -> Any:
    """List companies and their observers, optionally filtered to specific IDs."""
    return await client.get("companies.observers", params={"ids": ids})


def register(mcp: FastMCP, client: InvGateClient) -> None:
    """Register the read-only organizational-structure tools on the MCP server."""

    @mcp.tool()
    async def list_helpdesks(
        helpdesk_id: int | None = None,
        name: str | None = None,
        include_deleted: bool = False,
    ) -> Any:
        """List active help desks, or one in particular by ID or name."""
        return await list_helpdesks_fn(
            client, helpdesk_id=helpdesk_id, name=name, include_deleted=include_deleted
        )

    @mcp.tool()
    async def list_helpdesk_levels(
        level_id: int | None = None, include_deleted: bool = False
    ) -> Any:
        """List active help desk levels, or one in particular by ID."""
        return await list_helpdesk_levels_fn(
            client, level_id=level_id, include_deleted=include_deleted
        )

    @mcp.tool()
    async def list_helpdesks_and_levels(
        helpdesk_id: int | None = None, include_deleted: bool = False
    ) -> Any:
        """List help desks together with their levels, or one by ID."""
        return await list_helpdesks_and_levels_fn(
            client, helpdesk_id=helpdesk_id, include_deleted=include_deleted
        )

    @mcp.tool()
    async def list_helpdesk_observers(ids: list[int] | None = None) -> Any:
        """List help desks and their observers (optionally filtered by IDs)."""
        return await list_helpdesk_observers_fn(client, ids=ids)

    @mcp.tool()
    async def list_level_observers(ids: list[int] | None = None) -> Any:
        """List help desk levels and their observers (optionally filtered by IDs)."""
        return await list_level_observers_fn(client, ids=ids)

    @mcp.tool()
    async def list_locations(location_id: int | None = None) -> Any:
        """List active locations, or one in particular by ID."""
        return await list_locations_fn(client, location_id=location_id)

    @mcp.tool()
    async def list_location_members(location_id: int, user_id: int | None = None) -> Any:
        """List the members of a location (optionally check one user)."""
        return await list_location_members_fn(client, location_id, user_id=user_id)

    @mcp.tool()
    async def list_location_observers(ids: list[int] | None = None) -> Any:
        """List locations and their observers (optionally filtered by IDs)."""
        return await list_location_observers_fn(client, ids=ids)

    @mcp.tool()
    async def list_company_members(company_id: int, user_id: int | None = None) -> Any:
        """List the members of a company (optionally check one user)."""
        return await list_company_members_fn(client, company_id, user_id=user_id)

    @mcp.tool()
    async def list_company_groups(company_id: int) -> Any:
        """List the user groups related to a company."""
        return await list_company_groups_fn(client, company_id)

    @mcp.tool()
    async def list_company_observers(ids: list[int] | None = None) -> Any:
        """List companies and their observers (optionally filtered by IDs)."""
        return await list_company_observers_fn(client, ids=ids)


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
list_helpdesks_fn = list_helpdesks
list_helpdesk_levels_fn = list_helpdesk_levels
list_helpdesks_and_levels_fn = list_helpdesks_and_levels
list_helpdesk_observers_fn = list_helpdesk_observers
list_level_observers_fn = list_level_observers
list_locations_fn = list_locations
list_location_members_fn = list_location_members
list_location_observers_fn = list_location_observers
list_company_members_fn = list_company_members
list_company_groups_fn = list_company_groups
list_company_observers_fn = list_company_observers
