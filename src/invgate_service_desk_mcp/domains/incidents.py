"""Incidents domain (Phase 1, read-only).

InvGate calls incidents "requests" in some API responses. These functions are thin,
typed wrappers over the read-only incident endpoints. Write operations are deferred
to a later phase behind explicit opt-in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient
from ..normalize import as_list, bool_flag

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

DateFormat = str  # "iso8601" or "epoch"


async def get_incident(
    client: InvGateClient,
    incident_id: int,
    *,
    include_comments: bool = False,
    date_format: DateFormat = "iso8601",
) -> Any:
    """Get a single incident (request) by its ID."""
    return await client.get(
        "incident",
        params={
            "id": incident_id,
            "date_format": date_format,
            "comments": True if include_comments else None,
        },
    )


async def get_incident_comments(
    client: InvGateClient,
    request_id: int,
    *,
    date_format: DateFormat = "iso8601",
    is_solution: bool | None = None,
) -> Any:
    """Get the replies/comments of a given incident."""
    return await client.get(
        "incident.comment",
        params={
            "request_id": request_id,
            "date_format": date_format,
            "is_solution": is_solution,
        },
    )


async def list_incidents_by_status(
    client: InvGateClient,
    *,
    status_id: int | None = None,
    status_ids: list[int] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Any:
    """List open incidents matching a status (or several status IDs)."""
    return as_list(
        await client.get(
            "incidents.by.status",
            params={
                "status_id": status_id,
                "status_ids": status_ids,
                "limit": limit,
                "offset": offset,
            },
        ),
        source="incidents.by.status",
    )


async def list_incidents_by_agent(
    client: InvGateClient,
    *,
    id: int | None = None,
    email: str | None = None,
    username: str | None = None,
    include_comments: bool | None = None,
    limit: int | None = None,
    page_key: str | None = None,
) -> Any:
    """List incidents assigned to an agent, identified by id, email or username."""
    _require_identifier(id, email, username)
    return as_list(
        await client.get(
            "incidents.by.agent",
            params={
                "id": id,
                "email": email,
                "username": username,
                "comments": include_comments,
                "limit": limit,
                "page_key": page_key,
            },
        ),
        source="incidents.by.agent",
    )


async def list_incidents_by_customer(
    client: InvGateClient,
    *,
    id: int | None = None,
    email: str | None = None,
    username: str | None = None,
    include_comments: bool | None = None,
    limit: int | None = None,
    page_key: str | None = None,
) -> Any:
    """List open incidents from a customer, identified by id, email or username."""
    _require_identifier(id, email, username)
    return as_list(
        await client.get(
            "incidents.by.customer",
            params={
                "id": id,
                "email": email,
                "username": username,
                "comments": include_comments,
                "limit": limit,
                "page_key": page_key,
            },
        ),
        source="incidents.by.customer",
    )


async def list_incidents_by_helpdesk(
    client: InvGateClient,
    *,
    helpdesk_id: int | None = None,
    helpdesk_ids: list[int] | None = None,
) -> Any:
    """List open incidents in a help desk (or several help desk IDs)."""
    return as_list(
        await client.get(
            "incidents.by.helpdesk",
            params={"helpdesk_id": helpdesk_id, "helpdesk_ids": helpdesk_ids},
        ),
        source="incidents.by.helpdesk",
    )


def _require_identifier(id: int | None, email: str | None, username: str | None) -> None:
    if id is None and not email and not username:
        raise ValueError("Provide one of: id, email or username.")


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only incident tools on the given MCP server."""

    @mcp.tool()
    async def get_incident(
        incident_id: int,
        include_comments: bool = False,
        date_format: DateFormat = "iso8601",
    ) -> Any:
        """Get a single incident (request) by its ID."""
        return await get_incident_fn(
            client,
            incident_id=incident_id,
            include_comments=include_comments,
            date_format=date_format,
        )

    @mcp.tool()
    async def get_incident_comments(
        request_id: int,
        date_format: DateFormat = "iso8601",
        is_solution: bool | None = None,
    ) -> Any:
        """Get the replies/comments of a given incident."""
        return await get_incident_comments_fn(
            client,
            request_id=request_id,
            date_format=date_format,
            is_solution=is_solution,
        )

    @mcp.tool()
    async def list_incidents_by_status(
        status_id: int | None = None,
        status_ids: list[int] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        """List open incidents matching a status (or several status IDs)."""
        return await list_incidents_by_status_fn(
            client,
            status_id=status_id,
            status_ids=status_ids,
            limit=limit,
            offset=offset,
        )

    @mcp.tool()
    async def list_incidents_by_agent(
        id: int | None = None,
        email: str | None = None,
        username: str | None = None,
        include_comments: bool | None = None,
        limit: int | None = None,
        page_key: str | None = None,
    ) -> Any:
        """List incidents assigned to an agent (by id, email or username)."""
        return await list_incidents_by_agent_fn(
            client,
            id=id,
            email=email,
            username=username,
            include_comments=include_comments,
            limit=limit,
            page_key=page_key,
        )

    @mcp.tool()
    async def list_incidents_by_customer(
        id: int | None = None,
        email: str | None = None,
        username: str | None = None,
        include_comments: bool | None = None,
        limit: int | None = None,
        page_key: str | None = None,
    ) -> Any:
        """List open incidents from a customer (by id, email or username)."""
        return await list_incidents_by_customer_fn(
            client,
            id=id,
            email=email,
            username=username,
            include_comments=include_comments,
            limit=limit,
            page_key=page_key,
        )

    @mcp.tool()
    async def list_incidents_by_helpdesk(
        helpdesk_id: int | None = None,
        helpdesk_ids: list[int] | None = None,
    ) -> Any:
        """List open incidents in a help desk (or several help desk IDs)."""
        return await list_incidents_by_helpdesk_fn(
            client, helpdesk_id=helpdesk_id, helpdesk_ids=helpdesk_ids
        )

    # Write tools are registered only when the operator has opted in.
    if client.writes_enabled:
        _register_writes(mcp, client)


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
get_incident_fn = get_incident
get_incident_comments_fn = get_incident_comments
list_incidents_by_status_fn = list_incidents_by_status
list_incidents_by_agent_fn = list_incidents_by_agent
list_incidents_by_customer_fn = list_incidents_by_customer
list_incidents_by_helpdesk_fn = list_incidents_by_helpdesk


# --- Write operations (registered only when the operator opts in) ------------
#
# There is no DELETE endpoint for a request: a created ticket can be cancelled
# (cancel_incident) but not deleted. POST/PUT send form params; the one DELETE
# (custom field value) uses query params.


_flag = bool_flag


async def create_incident(
    client: InvGateClient,
    *,
    creator_id: int,
    customer_id: int,
    category_id: int,
    priority_id: int,
    type_id: int,
    title: str,
    source_id: int | None = None,
    description: str | None = None,
    date: str | None = None,
    attachments: list[Any] | None = None,
    related_to: list[int] | None = None,
    location_id: int | None = None,
) -> Any:
    """Create a new request (ticket). Returns the created request."""
    return await client.post(
        "incident",
        data={
            "creator_id": creator_id,
            "customer_id": customer_id,
            "category_id": category_id,
            "priority_id": priority_id,
            "type_id": type_id,
            "title": title,
            "source_id": source_id,
            "description": description,
            "date": date,
            "attachments": attachments,
            "related_to": related_to,
            "location_id": location_id,
        },
    )


async def update_incident(
    client: InvGateClient,
    incident_id: int,
    *,
    customer_id: int | None = None,
    category_id: int | None = None,
    reassignment: bool | None = None,
    priority_id: int | None = None,
    type_id: int | None = None,
    source_id: int | None = None,
    title: str | None = None,
    description: str | None = None,
    location_id: int | None = None,
    date: str | None = None,
    date_format: str | None = None,
) -> Any:
    """Change attributes of a request."""
    return await client.put(
        "incident",
        data={
            "id": incident_id,
            "customer_id": customer_id,
            "category_id": category_id,
            "reassignment": _flag(reassignment),
            "priority_id": priority_id,
            "type_id": type_id,
            "source_id": source_id,
            "title": title,
            "description": description,
            "location_id": location_id,
            "date": date,
            "date_format": date_format,
        },
    )


async def reopen_incident(
    client: InvGateClient, request_id: int, *, author_id: int | None = None
) -> Any:
    """Reopen a request."""
    return await client.put(
        "incident.reopen", data={"request_id": request_id, "author_id": author_id}
    )


async def reject_incident(client: InvGateClient, request_id: int, author_id: int) -> Any:
    """Reject a request."""
    return await client.post(
        "incident.reject", data={"request_id": request_id, "author_id": author_id}
    )


async def cancel_incident(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    *,
    comment: str | None = None,
) -> Any:
    """Cancel a request."""
    return await client.post(
        "incident.cancel",
        data={"request_id": request_id, "author_id": author_id, "comment": comment},
    )


async def promote_incident_to_major(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    *,
    confirm: bool | None = None,
) -> Any:
    """Promote a request to a major incident."""
    return await client.post(
        "incident.promote.to.major.incident",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "confirm": _flag(confirm),
        },
    )


async def reassign_incident(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    group_id: int,
    *,
    agent_id: int | None = None,
) -> Any:
    """Reassign a request to a help desk and/or agent."""
    return await client.post(
        "incident.reassign",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "group_id": group_id,
            "agent_id": agent_id,
        },
    )


async def add_incident_comment(
    client: InvGateClient,
    request_id: int,
    comment: str,
    author_id: int,
    *,
    is_solution: bool | None = None,
    customer_visible: bool | None = None,
    attachments: list[Any] | None = None,
    is_propagation: bool | None = None,
) -> Any:
    """Add a reply/comment to a request."""
    return await client.post(
        "incident.comment",
        data={
            "request_id": request_id,
            "comment": comment,
            "author_id": author_id,
            "is_solution": _flag(is_solution),
            "customer_visible": _flag(customer_visible),
            "attachments": attachments,
            "is_propagation": _flag(is_propagation),
        },
    )


async def set_incident_custom_field(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    custom_field_uid: int,
    values: list[Any],
) -> Any:
    """Set the value(s) of a custom field on a request."""
    return await client.post(
        "incident.custom_field",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "custom_field_uid": custom_field_uid,
            "values": values,
        },
    )


async def delete_incident_custom_field(
    client: InvGateClient, request_id: int, author_id: int, custom_field_uid: int
) -> Any:
    """Delete the value of a custom field on a request."""
    return await client.delete(
        "incident.custom_field",
        params={
            "request_id": request_id,
            "author_id": author_id,
            "custom_field_uid": custom_field_uid,
        },
    )


async def add_incident_observer(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    *,
    user_id: int | None = None,
    user_ids: list[int] | None = None,
) -> Any:
    """Add one or more users as observers of a request."""
    return await client.post(
        "incident.observer",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "user_id": user_id,
            "users_id": user_ids,
        },
    )


async def add_incident_collaborator(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    *,
    user_id: int | None = None,
    user_ids: list[int] | None = None,
) -> Any:
    """Request collaboration from one or more users on a request."""
    return await client.post(
        "incident.collaborator",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "user_id": user_id,
            "users_id": user_ids,
        },
    )


async def link_incident(
    client: InvGateClient, request_id: int, request_ids: list[int]
) -> Any:
    """Link a request to one or more other requests."""
    return await client.post(
        "incident.link", data={"request_id": request_id, "request_ids": request_ids}
    )


async def link_incident_to_external_entity(
    client: InvGateClient,
    request_id: int,
    external_entity_id: int,
    *,
    external_entity_ref_id: str | None = None,
) -> Any:
    """Link a request to an external entity."""
    return await client.post(
        "incident.external_entity",
        data={
            "request_id": request_id,
            "external_entity_id": external_entity_id,
            "external_entity_ref_id": external_entity_ref_id,
        },
    )


async def relate_incident_to_cis_by_keyword(
    client: InvGateClient,
    request_id: int,
    keyword: str,
    *,
    exact_match: bool | None = None,
) -> Any:
    """Relate a request to every CI that matches a keyword."""
    return await client.post(
        "incident.relate.ci.by.keyword",
        data={
            "request_id": request_id,
            "keyword": keyword,
            "exact_match": _flag(exact_match),
        },
    )


async def set_incident_waiting_for_incident(
    client: InvGateClient, request_id: int, wait_request_id: int
) -> Any:
    """Set a request to "waiting for another request"."""
    return await client.post(
        "incident.waitingfor.incident",
        data={"request_id": request_id, "wait_request_id": wait_request_id},
    )


async def set_incident_waiting_for_external_entity(
    client: InvGateClient, request_id: int, entity_link_id: int
) -> Any:
    """Set a request to "waiting for external entity"."""
    return await client.post(
        "incident.waitingfor.external_entity",
        data={"request_id": request_id, "entity_link_id": entity_link_id},
    )


async def set_incident_waiting_for_agent(client: InvGateClient, request_id: int) -> Any:
    """Set a request to "waiting for agent"."""
    return await client.post(
        "incident.waitingfor.agent", data={"request_id": request_id}
    )


async def set_incident_waiting_for_customer(
    client: InvGateClient, request_id: int
) -> Any:
    """Set a request to "waiting for customer"."""
    return await client.post(
        "incident.waitingfor.customer", data={"request_id": request_id}
    )


async def set_incident_waiting_for_date(
    client: InvGateClient, request_id: int, timestamp: int
) -> Any:
    """Set a request to "waiting until a date" (epoch timestamp)."""
    return await client.post(
        "incident.waitingfor.date",
        data={"request_id": request_id, "timestamp": timestamp},
    )


async def accept_incident_approval(
    client: InvGateClient,
    approval_id: int,
    user_id: int,
    *,
    note: str | None = None,
) -> Any:
    """Accept an approval."""
    return await client.put(
        "incident.approval.accept",
        data={"approval_id": approval_id, "user_id": user_id, "note": note},
    )


async def reject_incident_approval(
    client: InvGateClient,
    approval_id: int,
    user_id: int,
    *,
    note: str | None = None,
) -> Any:
    """Reject an approval."""
    return await client.put(
        "incident.approval.reject",
        data={"approval_id": approval_id, "user_id": user_id, "note": note},
    )


async def cancel_incident_approval(
    client: InvGateClient, approval_id: int, user_id: int
) -> Any:
    """Cancel an approval."""
    return await client.put(
        "incident.approval.cancel",
        data={"approval_id": approval_id, "user_id": user_id},
    )


async def add_incident_approval_voter(
    client: InvGateClient, approval_id: int, user_id: int
) -> Any:
    """Add a voter to an approval."""
    return await client.post(
        "incident.approval.add_voter",
        data={"approval_id": approval_id, "user_id": user_id},
    )


async def create_incident_spontaneous_approval(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    approval_user_id: int,
    description: str,
) -> Any:
    """Create a spontaneous approval on a request."""
    return await client.post(
        "incident.spontaneous_approval",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "approval_user_id": approval_user_id,
            "description": description,
        },
    )


async def request_incident_custom_approval(
    client: InvGateClient,
    request_id: int,
    author_id: int,
    approval_id: int,
    *,
    description: str | None = None,
) -> Any:
    """Request a custom approval (by template) on a request."""
    return await client.post(
        "incident.custom_approval",
        data={
            "request_id": request_id,
            "author_id": author_id,
            "approval_id": approval_id,
            "description": description,
        },
    )


async def accept_incident_solution(
    client: InvGateClient,
    incident_id: int,
    rating: int,
    *,
    comment: str | None = None,
) -> Any:
    """Accept the solution of a request, with a rating."""
    return await client.put(
        "incident.solution.accept",
        data={"id": incident_id, "rating": rating, "comment": comment},
    )


async def reject_incident_solution(
    client: InvGateClient, incident_id: int, comment: str
) -> Any:
    """Reject the solution of a request, with a comment."""
    return await client.put(
        "incident.solution.reject", data={"id": incident_id, "comment": comment}
    )


def _register_writes(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the incident write tools. Called only when writes are enabled."""

    @mcp.tool()
    async def create_incident(
        creator_id: int,
        customer_id: int,
        category_id: int,
        priority_id: int,
        type_id: int,
        title: str,
        source_id: int | None = None,
        description: str | None = None,
        date: str | None = None,
        attachments: list[Any] | None = None,
        related_to: list[int] | None = None,
        location_id: int | None = None,
    ) -> Any:
        """Create a new request (ticket)."""
        return await create_incident_fn(
            client,
            creator_id=creator_id,
            customer_id=customer_id,
            category_id=category_id,
            priority_id=priority_id,
            type_id=type_id,
            title=title,
            source_id=source_id,
            description=description,
            date=date,
            attachments=attachments,
            related_to=related_to,
            location_id=location_id,
        )

    @mcp.tool()
    async def update_incident(
        incident_id: int,
        customer_id: int | None = None,
        category_id: int | None = None,
        reassignment: bool | None = None,
        priority_id: int | None = None,
        type_id: int | None = None,
        source_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        location_id: int | None = None,
        date: str | None = None,
        date_format: str | None = None,
    ) -> Any:
        """Change attributes of a request."""
        return await update_incident_fn(
            client,
            incident_id,
            customer_id=customer_id,
            category_id=category_id,
            reassignment=reassignment,
            priority_id=priority_id,
            type_id=type_id,
            source_id=source_id,
            title=title,
            description=description,
            location_id=location_id,
            date=date,
            date_format=date_format,
        )

    @mcp.tool()
    async def reopen_incident(request_id: int, author_id: int | None = None) -> Any:
        """Reopen a request."""
        return await reopen_incident_fn(client, request_id, author_id=author_id)

    @mcp.tool()
    async def reject_incident(request_id: int, author_id: int) -> Any:
        """Reject a request."""
        return await reject_incident_fn(client, request_id, author_id)

    @mcp.tool()
    async def cancel_incident(
        request_id: int, author_id: int, comment: str | None = None
    ) -> Any:
        """Cancel a request."""
        return await cancel_incident_fn(client, request_id, author_id, comment=comment)

    @mcp.tool()
    async def promote_incident_to_major(
        request_id: int, author_id: int, confirm: bool | None = None
    ) -> Any:
        """Promote a request to a major incident."""
        return await promote_incident_to_major_fn(
            client, request_id, author_id, confirm=confirm
        )

    @mcp.tool()
    async def reassign_incident(
        request_id: int, author_id: int, group_id: int, agent_id: int | None = None
    ) -> Any:
        """Reassign a request to a help desk and/or agent."""
        return await reassign_incident_fn(
            client, request_id, author_id, group_id, agent_id=agent_id
        )

    @mcp.tool()
    async def add_incident_comment(
        request_id: int,
        comment: str,
        author_id: int,
        is_solution: bool | None = None,
        customer_visible: bool | None = None,
        attachments: list[Any] | None = None,
        is_propagation: bool | None = None,
    ) -> Any:
        """Add a reply/comment to a request."""
        return await add_incident_comment_fn(
            client,
            request_id,
            comment,
            author_id,
            is_solution=is_solution,
            customer_visible=customer_visible,
            attachments=attachments,
            is_propagation=is_propagation,
        )

    @mcp.tool()
    async def set_incident_custom_field(
        request_id: int, author_id: int, custom_field_uid: int, values: list[Any]
    ) -> Any:
        """Set the value(s) of a custom field on a request."""
        return await set_incident_custom_field_fn(
            client, request_id, author_id, custom_field_uid, values
        )

    @mcp.tool()
    async def delete_incident_custom_field(
        request_id: int, author_id: int, custom_field_uid: int
    ) -> Any:
        """Delete the value of a custom field on a request."""
        return await delete_incident_custom_field_fn(
            client, request_id, author_id, custom_field_uid
        )

    @mcp.tool()
    async def add_incident_observer(
        request_id: int,
        author_id: int,
        user_id: int | None = None,
        user_ids: list[int] | None = None,
    ) -> Any:
        """Add one or more users as observers of a request."""
        return await add_incident_observer_fn(
            client, request_id, author_id, user_id=user_id, user_ids=user_ids
        )

    @mcp.tool()
    async def add_incident_collaborator(
        request_id: int,
        author_id: int,
        user_id: int | None = None,
        user_ids: list[int] | None = None,
    ) -> Any:
        """Request collaboration from one or more users on a request."""
        return await add_incident_collaborator_fn(
            client, request_id, author_id, user_id=user_id, user_ids=user_ids
        )

    @mcp.tool()
    async def link_incident(request_id: int, request_ids: list[int]) -> Any:
        """Link a request to one or more other requests."""
        return await link_incident_fn(client, request_id, request_ids)

    @mcp.tool()
    async def link_incident_to_external_entity(
        request_id: int,
        external_entity_id: int,
        external_entity_ref_id: str | None = None,
    ) -> Any:
        """Link a request to an external entity."""
        return await link_incident_to_external_entity_fn(
            client,
            request_id,
            external_entity_id,
            external_entity_ref_id=external_entity_ref_id,
        )

    @mcp.tool()
    async def relate_incident_to_cis_by_keyword(
        request_id: int, keyword: str, exact_match: bool | None = None
    ) -> Any:
        """Relate a request to every CI that matches a keyword."""
        return await relate_incident_to_cis_by_keyword_fn(
            client, request_id, keyword, exact_match=exact_match
        )

    @mcp.tool()
    async def set_incident_waiting_for_incident(
        request_id: int, wait_request_id: int
    ) -> Any:
        """Set a request to waiting for another request."""
        return await set_incident_waiting_for_incident_fn(
            client, request_id, wait_request_id
        )

    @mcp.tool()
    async def set_incident_waiting_for_external_entity(
        request_id: int, entity_link_id: int
    ) -> Any:
        """Set a request to waiting for an external entity."""
        return await set_incident_waiting_for_external_entity_fn(
            client, request_id, entity_link_id
        )

    @mcp.tool()
    async def set_incident_waiting_for_agent(request_id: int) -> Any:
        """Set a request to waiting for agent."""
        return await set_incident_waiting_for_agent_fn(client, request_id)

    @mcp.tool()
    async def set_incident_waiting_for_customer(request_id: int) -> Any:
        """Set a request to waiting for customer."""
        return await set_incident_waiting_for_customer_fn(client, request_id)

    @mcp.tool()
    async def set_incident_waiting_for_date(request_id: int, timestamp: int) -> Any:
        """Set a request to waiting until a date (epoch timestamp)."""
        return await set_incident_waiting_for_date_fn(client, request_id, timestamp)

    @mcp.tool()
    async def accept_incident_approval(
        approval_id: int, user_id: int, note: str | None = None
    ) -> Any:
        """Accept an approval."""
        return await accept_incident_approval_fn(
            client, approval_id, user_id, note=note
        )

    @mcp.tool()
    async def reject_incident_approval(
        approval_id: int, user_id: int, note: str | None = None
    ) -> Any:
        """Reject an approval."""
        return await reject_incident_approval_fn(
            client, approval_id, user_id, note=note
        )

    @mcp.tool()
    async def cancel_incident_approval(approval_id: int, user_id: int) -> Any:
        """Cancel an approval."""
        return await cancel_incident_approval_fn(client, approval_id, user_id)

    @mcp.tool()
    async def add_incident_approval_voter(approval_id: int, user_id: int) -> Any:
        """Add a voter to an approval."""
        return await add_incident_approval_voter_fn(client, approval_id, user_id)

    @mcp.tool()
    async def create_incident_spontaneous_approval(
        request_id: int, author_id: int, approval_user_id: int, description: str
    ) -> Any:
        """Create a spontaneous approval on a request."""
        return await create_incident_spontaneous_approval_fn(
            client, request_id, author_id, approval_user_id, description
        )

    @mcp.tool()
    async def request_incident_custom_approval(
        request_id: int, author_id: int, approval_id: int, description: str | None = None
    ) -> Any:
        """Request a custom approval (by template) on a request."""
        return await request_incident_custom_approval_fn(
            client, request_id, author_id, approval_id, description=description
        )

    @mcp.tool()
    async def accept_incident_solution(
        incident_id: int, rating: int, comment: str | None = None
    ) -> Any:
        """Accept the solution of a request, with a rating."""
        return await accept_incident_solution_fn(
            client, incident_id, rating, comment=comment
        )

    @mcp.tool()
    async def reject_incident_solution(incident_id: int, comment: str) -> Any:
        """Reject the solution of a request, with a comment."""
        return await reject_incident_solution_fn(client, incident_id, comment)


create_incident_fn = create_incident
update_incident_fn = update_incident
reopen_incident_fn = reopen_incident
reject_incident_fn = reject_incident
cancel_incident_fn = cancel_incident
promote_incident_to_major_fn = promote_incident_to_major
reassign_incident_fn = reassign_incident
add_incident_comment_fn = add_incident_comment
set_incident_custom_field_fn = set_incident_custom_field
delete_incident_custom_field_fn = delete_incident_custom_field
add_incident_observer_fn = add_incident_observer
add_incident_collaborator_fn = add_incident_collaborator
link_incident_fn = link_incident
link_incident_to_external_entity_fn = link_incident_to_external_entity
relate_incident_to_cis_by_keyword_fn = relate_incident_to_cis_by_keyword
set_incident_waiting_for_incident_fn = set_incident_waiting_for_incident
set_incident_waiting_for_external_entity_fn = set_incident_waiting_for_external_entity
set_incident_waiting_for_agent_fn = set_incident_waiting_for_agent
set_incident_waiting_for_customer_fn = set_incident_waiting_for_customer
set_incident_waiting_for_date_fn = set_incident_waiting_for_date
accept_incident_approval_fn = accept_incident_approval
reject_incident_approval_fn = reject_incident_approval
cancel_incident_approval_fn = cancel_incident_approval
add_incident_approval_voter_fn = add_incident_approval_voter
create_incident_spontaneous_approval_fn = create_incident_spontaneous_approval
request_incident_custom_approval_fn = request_incident_custom_approval
accept_incident_solution_fn = accept_incident_solution
reject_incident_solution_fn = reject_incident_solution
