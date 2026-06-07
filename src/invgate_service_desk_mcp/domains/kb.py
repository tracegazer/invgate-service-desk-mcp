"""Knowledge Base domain (Phase 3, read-only).

Thin, typed wrappers over the read-only Knowledge Base endpoints. Keyword search
is the headline use case: it lets an AI agent find and cite relevant articles.
Write operations (create/update/delete articles) are deferred to a later phase
behind explicit opt-in.

Response shapes (confirmed against a live instance): the ARTICLE endpoints wrap
results in an envelope ``{"status": ..., "data": [ ... ]}`` (list/by_category also
add ``total_count``/``offset``/``limit``). The CATEGORY endpoints return a bare
list. Wrappers return the raw JSON as-is.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient
from ..normalize import bool_flag

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def search_kb_articles(
    client: InvGateClient,
    keywords: str,
    *,
    min_search_scoring: float | None = None,
    limit: int | None = None,
) -> Any:
    """Search Knowledge Base articles by keywords (relevance-ranked)."""
    return await client.get(
        "kb.articles.by.keywords",
        params={
            "keywords": keywords,
            "min_search_scoring": min_search_scoring,
            "limit": limit,
        },
    )


async def list_kb_articles(
    client: InvGateClient,
    *,
    sort_by: str | None = None,
    order_by: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Any:
    """List Knowledge Base articles with their properties."""
    return await client.get(
        "kb.articles",
        params={
            "sort_by": sort_by,
            "order_by": order_by,
            "limit": limit,
            "offset": offset,
        },
    )


async def get_kb_articles_by_ids(client: InvGateClient, article_ids: list[int]) -> Any:
    """Get Knowledge Base articles by their IDs."""
    if not article_ids:
        raise ValueError("Provide a non-empty list of article_ids.")
    return await client.get("kb.articles.by.ids", params={"ids": article_ids})


async def list_kb_articles_by_category(
    client: InvGateClient,
    category_id: int,
    *,
    limit: int | None = None,
    offset: int | None = None,
    visibility: int | None = None,
) -> Any:
    """List articles in a category (visibility: 1=public, others per instance config)."""
    return await client.get(
        "kb.articles.by.category",
        params={
            "category_id": category_id,
            "limit": limit,
            "offset": offset,
            "visibility": visibility,
        },
    )


async def get_kb_article_attachments(client: InvGateClient, article_id: int) -> Any:
    """List the attachments of a Knowledge Base article."""
    return await client.get("kb.articles.attachments", params={"article_id": article_id})


async def list_kb_categories(client: InvGateClient) -> Any:
    """List all Knowledge Base categories."""
    return await client.get("kb.categories")


async def get_kb_categories_by_ids(client: InvGateClient, category_ids: list[int]) -> Any:
    """Get Knowledge Base categories by their IDs."""
    if not category_ids:
        raise ValueError("Provide a non-empty list of category_ids.")
    return await client.get("kb.categories.by.ids", params={"ids": category_ids})


# --- Write operations (registered only when the operator opts in) ------------


_bool_flag = bool_flag


async def create_kb_article(
    client: InvGateClient,
    *,
    title: str,
    content: str,
    author_id: int,
    category_id: int,
    description: str | None = None,
    is_private: bool | None = None,
    responsible_id: int | None = None,
) -> Any:
    """Create a Knowledge Base article. Returns ``{"status": ..., "article_id": <id>}``."""
    return await client.post(
        "kb.articles",
        data={
            "title": title,
            "content": content,
            "author_id": author_id,
            "category_id": category_id,
            "description": description,
            "is_private": _bool_flag(is_private),
            "responsible_id": responsible_id,
        },
    )


async def update_kb_article(
    client: InvGateClient,
    article_id: int,
    *,
    author_id: int,
    title: str | None = None,
    content: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
    is_private: bool | None = None,
    responsible_id: int | None = None,
) -> Any:
    """Update a Knowledge Base article. ``author_id`` is required by the API."""
    return await client.put(
        "kb.articles",
        data={
            "id": article_id,
            "author_id": author_id,
            "title": title,
            "content": content,
            "description": description,
            "category_id": category_id,
            "is_private": _bool_flag(is_private),
            "responsible_id": responsible_id,
        },
    )


async def delete_kb_article(client: InvGateClient, article_id: int) -> Any:
    """Delete a Knowledge Base article by ID."""
    return await client.delete("kb.articles", params={"id": article_id})


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only Knowledge Base tools on the given MCP server."""

    @mcp.tool()
    async def search_kb_articles(
        keywords: str,
        min_search_scoring: float | None = None,
        limit: int | None = None,
    ) -> Any:
        """Search Knowledge Base articles by keywords (relevance-ranked)."""
        return await search_kb_articles_fn(
            client,
            keywords,
            min_search_scoring=min_search_scoring,
            limit=limit,
        )

    @mcp.tool()
    async def list_kb_articles(
        sort_by: str | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Any:
        """List Knowledge Base articles with their properties."""
        return await list_kb_articles_fn(
            client,
            sort_by=sort_by,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )

    @mcp.tool()
    async def get_kb_articles_by_ids(article_ids: list[int]) -> Any:
        """Get Knowledge Base articles by their IDs."""
        return await get_kb_articles_by_ids_fn(client, article_ids)

    @mcp.tool()
    async def list_kb_articles_by_category(
        category_id: int,
        limit: int | None = None,
        offset: int | None = None,
        visibility: int | None = None,
    ) -> Any:
        """List articles in a category (visibility: 1=public)."""
        return await list_kb_articles_by_category_fn(
            client,
            category_id,
            limit=limit,
            offset=offset,
            visibility=visibility,
        )

    @mcp.tool()
    async def get_kb_article_attachments(article_id: int) -> Any:
        """List the attachments of a Knowledge Base article."""
        return await get_kb_article_attachments_fn(client, article_id)

    @mcp.tool()
    async def list_kb_categories() -> Any:
        """List all Knowledge Base categories."""
        return await list_kb_categories_fn(client)

    @mcp.tool()
    async def get_kb_categories_by_ids(category_ids: list[int]) -> Any:
        """Get Knowledge Base categories by their IDs."""
        return await get_kb_categories_by_ids_fn(client, category_ids)

    # Write tools are registered only when the operator has opted in.
    if client.writes_enabled_for("kb"):
        _register_writes(mcp, client)


def _register_writes(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the KB write tools. Called only when writes are enabled."""

    @mcp.tool()
    async def create_kb_article(
        title: str,
        content: str,
        author_id: int,
        category_id: int,
        description: str | None = None,
        is_private: bool | None = None,
        responsible_id: int | None = None,
    ) -> Any:
        """Create a Knowledge Base article."""
        return await create_kb_article_fn(
            client,
            title=title,
            content=content,
            author_id=author_id,
            category_id=category_id,
            description=description,
            is_private=is_private,
            responsible_id=responsible_id,
        )

    @mcp.tool()
    async def update_kb_article(
        article_id: int,
        author_id: int,
        title: str | None = None,
        content: str | None = None,
        description: str | None = None,
        category_id: int | None = None,
        is_private: bool | None = None,
        responsible_id: int | None = None,
    ) -> Any:
        """Update a Knowledge Base article (author_id required by the API)."""
        return await update_kb_article_fn(
            client,
            article_id,
            author_id=author_id,
            title=title,
            content=content,
            description=description,
            category_id=category_id,
            is_private=is_private,
            responsible_id=responsible_id,
        )

    @mcp.tool()
    async def delete_kb_article(article_id: int) -> Any:
        """Delete a Knowledge Base article by ID."""
        return await delete_kb_article_fn(client, article_id)


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
search_kb_articles_fn = search_kb_articles
list_kb_articles_fn = list_kb_articles
get_kb_articles_by_ids_fn = get_kb_articles_by_ids
list_kb_articles_by_category_fn = list_kb_articles_by_category
get_kb_article_attachments_fn = get_kb_article_attachments
list_kb_categories_fn = list_kb_categories
get_kb_categories_by_ids_fn = get_kb_categories_by_ids
create_kb_article_fn = create_kb_article
update_kb_article_fn = update_kb_article
delete_kb_article_fn = delete_kb_article
