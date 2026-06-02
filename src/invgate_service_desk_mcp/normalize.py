"""Normalize InvGate collection-envelope responses to plain lists.

InvGate wraps incident collections in one of two envelopes:

  - ``{"status", "info", "requests": {id: obj, ...}}``  -- full objects keyed by id
    (``incidents.by.agent`` / ``incidents.by.customer``)
  - ``{"status", "info", "requestIds": [id, ...], ...}`` -- ids only, plus
    pagination meta (``incidents.by.status`` / ``incidents.by.helpdesk``)

``unwrap_list`` flattens both to a plain list and returns anything else
unchanged, so single-object reads and write/status responses pass through
untouched. NOTE: for the ``requestIds`` shape the pagination meta
(``total``/``limit``/``offset``) is dropped in favour of a flat list.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)


class UnexpectedShapeError(Exception):
    """A collection endpoint returned a shape that can't be normalized to a list.

    Raised by :func:`as_list` so the calling agent gets an explicit, actionable
    signal (instead of a silently-confusing payload) when InvGate's response
    contract appears to have changed.
    """


def unwrap_list(response: Any) -> Any:
    """Flatten an InvGate collection envelope to a list; pass anything else through.

    Matches the known envelopes by both key AND container type:

      - ``requests`` as a {id: obj} **dict** -> list of the objects
      - ``requests`` as a **list** inside a status envelope (empty results) -> that list
      - ``requestIds`` as a **list** of ids -> that list

    A ``requests`` list inside a non-envelope dict (e.g. ``incidents.by.cis``
    items with ``{group, ci_id, requests: [...]}``) is left unchanged because
    the surrounding dict lacks the ``status`` key that marks a collection envelope.
    """
    if isinstance(response, dict):
        requests = response.get("requests")
        if isinstance(requests, dict):
            return list(requests.values())
        if isinstance(requests, list) and "status" in response:
            return requests
        request_ids = response.get("requestIds")
        if isinstance(request_ids, list):
            return request_ids
    return response


def bool_flag(value: bool | None) -> int | None:
    """Convert a Python bool to an InvGate 1/0 int flag, passing None through."""
    return None if value is None else (1 if value else 0)


def as_list(response: Any, *, source: str) -> list:
    """Normalize a collection response and assert it is a list.

    For endpoints that promise a list, this turns a silent contract change into
    a loud, actionable error: if :func:`unwrap_list` can't reduce the payload to
    a list, raise :class:`UnexpectedShapeError` naming the ``source`` endpoint
    and the keys observed, so the agent can report what happened cleanly.
    """
    flat = unwrap_list(response)
    if isinstance(flat, list):
        return flat
    detail = f" with keys {sorted(flat)}" if isinstance(flat, dict) else ""
    _log.warning(
        "Unexpected shape for '%s': got %s; InvGate response contract may have changed.",
        source, type(flat).__name__,
    )
    raise UnexpectedShapeError(
        f"InvGate returned an unexpected shape for '{source}': expected a list "
        f"or a known collection envelope, got {type(flat).__name__}{detail}. "
        "The API response contract may have changed."
    )
