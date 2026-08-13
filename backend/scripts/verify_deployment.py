"""Read-only smoke checks for an Epicenter deployment."""

from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None) -> tuple[int, dict, object]:
    request = Request(url, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - caller supplies the deployment URL
            body = response.read().decode()
            try:
                payload: object = json.loads(body) if body else {}
            except JSONDecodeError:
                payload = body
            return response.status, {key.lower(): value for key, value in response.headers.items()}, payload
    except HTTPError as exc:
        body = exc.read().decode()
        raise RuntimeError(f"{method} {url} returned {exc.code}: {body[:300]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Railway origin, without /api/v1")
    parser.add_argument("--frontend-origin", action="append", default=[])
    parser.add_argument("--expected-commit")
    parser.add_argument("--require-production", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    status, _, health = request_json(f"{base_url}/healthz")
    if status != 200 or health.get("status") != "ok":
        raise RuntimeError(f"Unhealthy deployment: {health}")

    if args.require_production:
        expected = {"database": "supabase", "authentication": "clerk", "openai": "configured"}
        if health.get("demo_mode") is not False or health.get("providers") != expected:
            raise RuntimeError(f"Production providers are not ready: {health}")

    actual_commit = health.get("deployment", {}).get("commit_sha")
    if args.expected_commit and not str(actual_commit).startswith(args.expected_commit):
        raise RuntimeError(f"Expected commit {args.expected_commit}, got {actual_commit}")

    for origin in args.frontend_origin:
        _, headers, _ = request_json(
            f"{base_url}/api/v1/dashboard",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        allowed_origin = headers.get("access-control-allow-origin")
        if allowed_origin != origin:
            raise RuntimeError(f"CORS did not allow {origin}; response allowed {allowed_origin!r}")

    for path in ("/mcp/operations/healthz", "/mcp/insurance-registry/healthz"):
        mcp_status, _, body = request_json(f"{base_url}{path}")
        if mcp_status != 200:
            raise RuntimeError(f"MCP health check failed for {path}: {body}")

    print(
        json.dumps(
            {
                "status": "passed",
                "commit_sha": actual_commit,
                "service": health.get("deployment", {}).get("service"),
                "origins": args.frontend_origin,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
