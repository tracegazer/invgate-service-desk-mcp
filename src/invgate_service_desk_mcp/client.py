"""Async HTTP client for the InvGate Service Desk API."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from .config import Config
from .telemetry import Telemetry

# InvGate Service Desk REST API prefix. Isolated here so it is trivial to confirm
# against a live instance (the public docs render endpoints without the prefix).
API_PREFIX = "/api/v1"

# Cap on error text we surface, so a huge upstream body can't flood the caller/LLM.
MAX_ERROR_LEN = 1000
_REDACTED = "***REDACTED***"


class InvGateAPIError(Exception):
    """Raised when the InvGate API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, body: Any = None):
        super().__init__(f"InvGate API error {status_code}: {message}")
        self.status_code = status_code
        self.body = body


class InvGateClient:
    """Thin async wrapper around the InvGate SD REST API.

    Read-only by design for now: only GET is exposed.
    """

    def __init__(
        self,
        config: Config,
        http_client: httpx.AsyncClient | None = None,
        telemetry: Telemetry | None = None,
    ):
        self._telemetry = telemetry or Telemetry()
        self._config = config
        self._client = http_client or httpx.AsyncClient(
            base_url=f"{config.base_url}{API_PREFIX}",
            auth=httpx.BasicAuth(config.api_username, config.api_token),
            timeout=30.0,
        )
        # Secrets to scrub from any error text before it reaches the caller/LLM:
        # the raw token and the Basic credential a proxy might reflect back.
        basic = base64.b64encode(
            f"{config.api_username}:{config.api_token}".encode()
        ).decode()
        self._secrets = [s for s in (config.api_token, basic) if s]

    @property
    def writes_enabled(self) -> bool:
        """Whether write tools may be registered (operator opt-in)."""
        return self._config.enable_writes

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Issue a GET to an InvGate endpoint key (e.g. 'incident', 'incidents.by.status')."""
        with self._telemetry.client_span("GET", endpoint, params) as span:
            response = await self._client.get(f"/{endpoint}", params=self._clean(params))
            span.set_status_code(response.status_code)
            result = self._handle(response)
            span.set_result(result)
            return result

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Issue a form-encoded POST (InvGate writes use form params, not JSON)."""
        with self._telemetry.client_span("POST", endpoint, data) as span:
            response = await self._client.post(f"/{endpoint}", data=self._clean(data))
            span.set_status_code(response.status_code)
            result = self._handle(response)
            span.set_result(result)
            return result

    async def put(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Issue a form-encoded PUT (InvGate writes use form params, not JSON)."""
        with self._telemetry.client_span("PUT", endpoint, data) as span:
            response = await self._client.put(f"/{endpoint}", data=self._clean(data))
            span.set_status_code(response.status_code)
            result = self._handle(response)
            span.set_result(result)
            return result

    async def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Issue a DELETE with query params."""
        with self._telemetry.client_span("DELETE", endpoint, params) as span:
            response = await self._client.request(
                "DELETE", f"/{endpoint}", params=self._clean(params)
            )
            span.set_status_code(response.status_code)
            result = self._handle(response)
            span.set_result(result)
            return result

    @staticmethod
    def _clean(values: dict[str, Any] | None) -> dict[str, Any]:
        """Drop None values and encode lists PHP-style (ids[]=1&ids[]=2)."""
        clean: dict[str, Any] = {}
        for key, value in (values or {}).items():
            if value is None:
                continue
            clean[f"{key}[]" if isinstance(value, list) else key] = value
        return clean

    def _handle(self, response: httpx.Response) -> Any:
        if response.is_success:
            return response.json()
        try:
            body = response.json()
            message = body.get("error") or body.get("info") or response.text
        except Exception:
            body = response.text
            message = response.text
        raise InvGateAPIError(
            response.status_code,
            self._sanitize(message),
            self._sanitize(body),
        )

    def _sanitize(self, value: Any) -> Any:
        """Redact credentials and cap length on any value we surface in errors."""
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, _REDACTED)
            if len(value) > MAX_ERROR_LEN:
                value = value[:MAX_ERROR_LEN] + "...[truncated]"
            return value
        if isinstance(value, dict):
            return {k: self._sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        return value

    async def aclose(self) -> None:
        await self._client.aclose()
