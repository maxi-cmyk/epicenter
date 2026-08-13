from __future__ import annotations

from typing import Any

import httpx


class SupabaseDataError(RuntimeError):
    def __init__(self, message: str, *, code: str | None = None, status_code: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class SupabaseDataApi:
    """Small server-only PostgREST client; the secret key never leaves FastAPI."""

    def __init__(self, url: str, secret_key: str, *, timeout_seconds: float = 10.0) -> None:
        self.base_url = url.rstrip("/") + "/rest/v1"
        self._client = httpx.Client(
            headers={"apikey": secret_key, "Accept": "application/json"},
            timeout=timeout_seconds,
        )

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: object | None = None,
        prefer: str | None = None,
    ) -> Any:
        headers = {"Prefer": prefer} if prefer else None
        try:
            response = self._client.request(
                method,
                f"{self.base_url}/{path.lstrip('/')}",
                params=params,
                json=payload,
                headers=headers,
            )
        except httpx.RequestError as exc:
            raise SupabaseDataError("Supabase could not be reached.", status_code=503) from exc
        if response.is_success:
            if not response.content:
                return None
            return response.json()
        try:
            error = response.json()
        except ValueError:
            error = {"message": "Supabase returned a non-JSON error."}
        raise SupabaseDataError(
            str(error.get("message", "Supabase request failed.")),
            code=error.get("code"),
            status_code=response.status_code,
        )

    def select(
        self,
        table: str,
        fields: str = "*",
        *,
        filters: dict[str, str] | None = None,
        order: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        params = {"select": fields, **(filters or {})}
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        result = self._request("GET", table, params=params)
        return list(result or [])

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self._request("POST", table, payload=payload, prefer="return=representation")
        if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
            raise SupabaseDataError(f"Insert into {table} returned an invalid response.")
        return result[0]

    def patch(
        self,
        table: str,
        payload: dict[str, Any],
        *,
        filters: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """PATCH (update) rows matching filters."""
        params = dict(filters or {})
        result = self._request("PATCH", table, params=params, payload=payload, prefer="return=representation")
        return list(result or [])

    def rpc(self, function_name: str, parameters: dict[str, Any]) -> Any:
        """Call a Postgres function via PostgREST. Returns whatever the function returns."""
        result = self._request("POST", f"rpc/{function_name}", payload=parameters)
        return result

    def update(
        self,
        table: str,
        payload: dict[str, Any],
        *,
        filters: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Compatibility alias for callers that describe PATCH as update."""
        return self.patch(table, payload, filters=filters)
