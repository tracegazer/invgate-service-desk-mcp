"""Users & Groups domain (Phase 2, read-only).

Thin, typed wrappers over the read-only user/group/company endpoints. These power
agent/customer lookups and assignment context for AI agents. Write operations
(create/convert/disable users) are deferred to a later phase behind explicit opt-in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def get_user(
    client: InvGateClient,
    user_id: int,
    *,
    include_disabled: bool = False,
) -> Any:
    """Get a single user by ID."""
    return await client.get(
        "user",
        params={
            "id": user_id,
            "include_disabled": True if include_disabled else None,
        },
    )


async def list_users(
    client: InvGateClient,
    *,
    ids: list[int] | None = None,
    include_disabled: bool = False,
) -> Any:
    """List users, optionally filtered to specific IDs."""
    return await client.get(
        "users",
        params={
            "ids": ids,
            "include_disabled": True if include_disabled else None,
        },
    )


async def find_users(
    client: InvGateClient,
    *,
    username: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    employee_number: str | None = None,
    exact_match: bool = False,
    include_disabled: bool = False,
    page_key: str | None = None,
) -> Any:
    """Search users by username, email, phone number (any kind) or employee number.

    Returns a paginated map: ``{"next_page_key": <key|None>, "data": {"<id>": {...}}}``.
    Pass ``page_key`` to fetch the next page.
    """
    if not username and not email and not phone and not employee_number:
        raise ValueError("Provide one of: username, email, phone or employee_number.")
    return await client.get(
        "users.by",
        params={
            "username": username,
            "email": email,
            "phones": phone,
            "employee_number": employee_number,
            "exact_match": True if exact_match else None,
            "include_disabled": True if include_disabled else None,
            "page_key": page_key,
        },
    )


async def get_user_groups(client: InvGateClient, user_ids: list[int]) -> Any:
    """Get the groups, companies, helpdesks and locations for the given users."""
    # Explicit guard: the spec marks `ids` as required, but an empty-but-present
    # list[int] is a failure mode the type system can't catch.
    if not user_ids:
        raise ValueError("Provide a non-empty list of user_ids.")
    return await client.get("users.groups", params={"ids": user_ids})


async def list_groups(
    client: InvGateClient,
    *,
    group_id: int | None = None,
    name: str | None = None,
) -> Any:
    """List active groups, or one in particular by ID or name."""
    return await client.get("groups", params={"id": group_id, "name": name})


async def list_group_members(
    client: InvGateClient,
    group_id: int,
    *,
    user_id: int | None = None,
) -> Any:
    """List the members of a group, optionally checking a single user's membership."""
    return await client.get(
        "groups.users",
        params={"id": group_id, "user_id": user_id},
    )


async def list_companies(
    client: InvGateClient,
    *,
    company_id: int | None = None,
    name: str | None = None,
    external_id: str | None = None,
) -> Any:
    """List active companies, optionally filtered by ID, name or external ID."""
    return await client.get(
        "companies",
        params={"id": company_id, "name": name, "external_id": external_id},
    )


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only user/group tools on the given MCP server."""

    @mcp.tool()
    async def get_user(user_id: int, include_disabled: bool = False) -> Any:
        """Get a single user by ID."""
        return await get_user_fn(client, user_id=user_id, include_disabled=include_disabled)

    @mcp.tool()
    async def list_users(
        ids: list[int] | None = None,
        include_disabled: bool = False,
    ) -> Any:
        """List users, optionally filtered to specific IDs."""
        return await list_users_fn(client, ids=ids, include_disabled=include_disabled)

    @mcp.tool()
    async def find_users(
        username: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        employee_number: str | None = None,
        exact_match: bool = False,
        include_disabled: bool = False,
        page_key: str | None = None,
    ) -> Any:
        """Search users by username, email, phone number or employee number."""
        return await find_users_fn(
            client,
            username=username,
            email=email,
            phone=phone,
            employee_number=employee_number,
            exact_match=exact_match,
            include_disabled=include_disabled,
            page_key=page_key,
        )

    @mcp.tool()
    async def get_user_groups(user_ids: list[int]) -> Any:
        """Get the groups, companies, helpdesks and locations for the given users."""
        return await get_user_groups_fn(client, user_ids)

    @mcp.tool()
    async def list_groups(group_id: int | None = None, name: str | None = None) -> Any:
        """List active groups, or one in particular by ID or name."""
        return await list_groups_fn(client, group_id=group_id, name=name)

    @mcp.tool()
    async def list_group_members(group_id: int, user_id: int | None = None) -> Any:
        """List the members of a group (optionally check one user's membership)."""
        return await list_group_members_fn(client, group_id, user_id=user_id)

    @mcp.tool()
    async def list_companies(
        company_id: int | None = None,
        name: str | None = None,
        external_id: str | None = None,
    ) -> Any:
        """List active companies, optionally filtered by ID, name or external ID."""
        return await list_companies_fn(
            client,
            company_id=company_id,
            name=name,
            external_id=external_id,
        )


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
get_user_fn = get_user
list_users_fn = list_users
find_users_fn = find_users
get_user_groups_fn = get_user_groups
list_groups_fn = list_groups
list_group_members_fn = list_group_members
list_companies_fn = list_companies
