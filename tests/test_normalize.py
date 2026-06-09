"""Tests for the InvGate collection-envelope normalizer.

InvGate wraps incident collections in two shapes:
  - {"status","info","requests": {id: obj, ...}}  -> full objects keyed by id
  - {"status","info","requestIds": [id, ...], ...} -> just ids (+ pagination meta)
`unwrap_list` flattens both to a plain list and leaves every other shape
(single objects, write responses, already-a-list) untouched.
"""

import pytest

from invgate_service_desk_mcp.normalize import (
    UnexpectedShapeError,
    as_list,
    unwrap_list,
)


def test_requests_dict_envelope_becomes_list_of_objects():
    response = {
        "status": "OK",
        "info": "Returned a list of the requests.",
        "requests": {
            "20318": {"id": 20318, "title": "A"},
            "21574": {"id": 21574, "title": "B"},
        },
    }
    assert unwrap_list(response) == [
        {"id": 20318, "title": "A"},
        {"id": 21574, "title": "B"},
    ]


def test_requests_dict_preserves_insertion_order():
    response = {"requests": {"3": {"id": 3}, "1": {"id": 1}, "2": {"id": 2}}}
    assert [o["id"] for o in unwrap_list(response)] == [3, 1, 2]


def test_request_ids_envelope_becomes_list_of_ids():
    response = {
        "status": "OK",
        "info": "Returned a list of the requests.",
        "requestIds": [1, 2, 3],
        "total": 3,
        "limit": None,
        "offset": 0,
    }
    assert unwrap_list(response) == [1, 2, 3]


def test_empty_requests_dict_envelope_becomes_empty_list():
    assert unwrap_list({"status": "OK", "requests": {}}) == []


def test_empty_requests_list_envelope_becomes_empty_list():
    """InvGate sends requests as [] (not {}) when an agent has no tickets."""
    response = {
        "status": "OK",
        "info": "Returned a list of the requests related to the given agent.",
        "requests": [],
    }
    assert unwrap_list(response) == []


def test_plain_list_is_returned_unchanged():
    payload = [{"id": 1}, {"id": 2}]
    assert unwrap_list(payload) == payload


def test_single_object_is_returned_unchanged():
    incident = {"id": 21574, "title": "X", "attachments": [], "custom_fields": []}
    assert unwrap_list(incident) == incident


def test_write_status_response_is_returned_unchanged():
    assert unwrap_list({"status": "OK", "article_id": 5}) == {"status": "OK", "article_id": 5}


def test_error_status_response_is_returned_unchanged():
    assert unwrap_list({"status": "ERROR"}) == {"status": "ERROR"}


def test_object_with_a_nested_list_requests_field_is_unchanged():
    # incidents.by.cis items look like {group, ci_id, requests: [...]}. A bare
    # `requests` LIST is a nested field, not the keyed envelope, so it must not
    # be mistaken for a collection to flatten.
    item = {"group": "g", "ci_id": 5, "requests": [{"id": 1}, {"id": 2}]}
    assert unwrap_list(item) == item


# --- as_list: strict variant for endpoints that promise a list --------------


def test_as_list_returns_flattened_envelope():
    response = {"status": "OK", "requests": {"1": {"id": 1}, "2": {"id": 2}}}
    assert as_list(response, source="incidents.by.agent") == [{"id": 1}, {"id": 2}]


def test_as_list_returns_request_ids_and_plain_lists():
    assert as_list({"requestIds": [1, 2]}, source="x") == [1, 2]
    assert as_list([{"id": 1}], source="x") == [{"id": 1}]


def test_as_list_raises_on_unexpected_shape():
    with pytest.raises(UnexpectedShapeError):
        as_list({"status": "ERROR"}, source="incidents.by.agent")


def test_as_list_error_names_the_source_and_observed_keys():
    with pytest.raises(UnexpectedShapeError) as exc:
        as_list({"status": "ERROR", "weird": 1}, source="incidents.by.agent")
    message = str(exc.value)
    assert "incidents.by.agent" in message
    assert "status" in message and "weird" in message


def test_as_list_logs_warning_on_unexpected_shape(caplog):
    import contextlib
    import logging
    with (
        caplog.at_level(logging.WARNING, logger="invgate_service_desk_mcp.normalize"),
        contextlib.suppress(UnexpectedShapeError),
    ):
        as_list({"status": "ERROR"}, source="incidents.by.agent")
    assert any("incidents.by.agent" in r.message for r in caplog.records)
