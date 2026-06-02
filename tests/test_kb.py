import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import kb

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_search_kb_articles_passes_keywords(client):
    # KB article endpoints wrap results in an envelope: {status, data: [...]}.
    payload = {"status": "success", "data": [{"id": 1, "title": "Reset password"}]}
    route = respx.get(f"{API}/kb.articles.by.keywords").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await kb.search_kb_articles(client, keywords="reset password")

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"keywords": "reset password"}


@respx.mock
async def test_search_kb_articles_supports_scoring_and_limit(client):
    route = respx.get(f"{API}/kb.articles.by.keywords").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": []})
    )

    await kb.search_kb_articles(
        client, keywords="vpn", min_search_scoring=0.5, limit=10
    )

    params = dict(route.calls.last.request.url.params)
    assert params == {"keywords": "vpn", "min_search_scoring": "0.5", "limit": "10"}


@respx.mock
async def test_list_kb_articles_supports_sort_and_paging(client):
    route = respx.get(f"{API}/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": [], "total_count": 0})
    )

    await kb.list_kb_articles(client, sort_by="title", order_by="asc", limit=50, offset=0)

    params = dict(route.calls.last.request.url.params)
    assert params == {"sort_by": "title", "order_by": "asc", "limit": "50", "offset": "0"}


@respx.mock
async def test_get_kb_articles_by_ids_encodes_array(client):
    payload = {"status": "success", "data": [{"id": 3}, {"id": 7}]}
    route = respx.get(f"{API}/kb.articles.by.ids").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await kb.get_kb_articles_by_ids(client, article_ids=[3, 7])

    assert result == payload
    assert route.calls.last.request.url.params.get_list("ids[]") == ["3", "7"]


async def test_get_kb_articles_by_ids_requires_ids(client):
    with pytest.raises(ValueError, match="article_ids"):
        await kb.get_kb_articles_by_ids(client, article_ids=[])


@respx.mock
async def test_list_kb_articles_by_category_requires_category_id(client):
    route = respx.get(f"{API}/kb.articles.by.category").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": [], "total_count": 0})
    )

    await kb.list_kb_articles_by_category(client, category_id=12, visibility=1)

    params = dict(route.calls.last.request.url.params)
    assert params == {"category_id": "12", "visibility": "1"}


@respx.mock
async def test_get_kb_article_attachments_passes_article_id(client):
    payload = {"status": "success", "data": [{"id": 99, "filename": "guide.pdf"}]}
    route = respx.get(f"{API}/kb.articles.attachments").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await kb.get_kb_article_attachments(client, article_id=5)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"article_id": "5"}


@respx.mock
async def test_list_kb_categories_takes_no_params(client):
    route = respx.get(f"{API}/kb.categories").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "How-to"}])
    )

    result = await kb.list_kb_categories(client)

    assert result == [{"id": 1, "name": "How-to"}]
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_get_kb_categories_by_ids_encodes_array(client):
    route = respx.get(f"{API}/kb.categories.by.ids").mock(
        return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}])
    )

    result = await kb.get_kb_categories_by_ids(client, category_ids=[1, 2])

    assert result == [{"id": 1}, {"id": 2}]
    assert route.calls.last.request.url.params.get_list("ids[]") == ["1", "2"]


async def test_get_kb_categories_by_ids_requires_ids(client):
    with pytest.raises(ValueError, match="category_ids"):
        await kb.get_kb_categories_by_ids(client, category_ids=[])


# --- Write operations (opt-in) ----------------------------------------------


@respx.mock
async def test_create_kb_article_posts_form(client):
    route = respx.post(f"{API}/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK", "article_id": 42})
    )

    result = await kb.create_kb_article(
        client,
        title="VPN setup",
        content="<p>steps</p>",
        author_id=18,
        category_id=2,
        is_private=True,
    )

    assert result == {"status": "OK", "article_id": 42}
    body = bytes(route.calls.last.request.content).decode()
    assert "title=VPN+setup" in body
    assert "author_id=18" in body
    assert "category_id=2" in body
    assert "is_private=1" in body  # bool mapped to 1/0


@respx.mock
async def test_update_kb_article_puts_form_with_id_and_author(client):
    route = respx.put(f"{API}/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    await kb.update_kb_article(client, article_id=42, author_id=18, title="New title")

    body = bytes(route.calls.last.request.content).decode()
    assert "id=42" in body
    assert "author_id=18" in body
    assert "title=New+title" in body


@respx.mock
async def test_delete_kb_article_deletes_by_id(client):
    route = respx.delete(f"{API}/kb.articles").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    result = await kb.delete_kb_article(client, article_id=42)

    assert result == {"status": "OK"}
    assert dict(route.calls.last.request.url.params) == {"id": "42"}
