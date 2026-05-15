from __future__ import annotations

import logging
from typing import Any

import httpx

from .fahrplan import build_fahrplan_body
from .models import FahrplanSearchInput, OrtSearchInput
from .proxy import ProxyPool

logger = logging.getLogger(__name__)

BAHN_API_BASE = "https://www.bahn.de/web/api"
LOCATIONS_URL = f"{BAHN_API_BASE}/reiseloesung/orte"
FAHRPLAN_URL = f"{BAHN_API_BASE}/angebote/fahrplan"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
}

RETRYABLE_STATUS = frozenset({429, 403, 502, 503, 504})


class BahnWebClient:
    """Thin HTTP client for bahn.de web API — returns upstream JSON unchanged."""

    def __init__(self, *, proxy_pool: ProxyPool | None = None, max_retries: int = 3) -> None:
        self._client: httpx.AsyncClient | None = None
        self._proxy_pool = proxy_pool
        self._max_retries = max(1, max_retries)
        self._station_cache: dict[str, dict[str, Any]] = {}

    async def __aenter__(self) -> BahnWebClient:
        self._client = httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=60.0)
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Use 'async with BahnWebClient()'")
        return self._client

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        attempts = self._max_retries
        if self._proxy_pool:
            attempts = max(attempts, len(self._proxy_pool))

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            proxy_url = self._proxy_pool.next() if self._proxy_pool else None
            client = self._get_client()
            req_client = client
            close_client = False
            if proxy_url:
                req_client = httpx.AsyncClient(
                    headers=client.headers,
                    timeout=client.timeout,
                    proxy=proxy_url,
                    follow_redirects=client.follow_redirects,
                )
                close_client = True
            try:
                response = await req_client.request(method, url, **kwargs)
                if response.status_code in RETRYABLE_STATUS and attempt < attempts:
                    logger.warning("HTTP %s %s (retry %d/%d)", response.status_code, url, attempt, attempts)
                    continue
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < attempts:
                    logger.warning("Request failed %s (retry %d/%d): %s", url, attempt, attempts, exc)
                    continue
                raise
            finally:
                if close_client:
                    await req_client.aclose()

        if last_error:
            raise last_error
        raise httpx.HTTPError(f"Request failed: {method} {url}")

    async def search_orte(self, search: OrtSearchInput) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            LOCATIONS_URL,
            params={"suchbegriff": search.query, "typ": search.typ, "limit": search.limit},
        )
        return response.json()

    async def resolve_station(self, name: str) -> dict[str, Any]:
        cached = self._station_cache.get(name.casefold())
        if cached:
            return cached
        stations = await self.search_orte(OrtSearchInput(query=name, limit=5))
        if not stations:
            raise ValueError(f"No station found for {name!r}")
        station = stations[0]
        self._station_cache[name.casefold()] = station
        return station

    async def search_fahrplan(self, search: FahrplanSearchInput) -> dict[str, Any]:
        from_station = await self.resolve_station(search.origin)
        to_station = await self.resolve_station(search.destination)
        body = build_fahrplan_body(from_station["id"], to_station["id"], search)
        response = await self._request("POST", FAHRPLAN_URL, json=body)
        payload: dict[str, Any] = response.json()
        return {
            "request": {
                "origin": search.origin,
                "destination": search.destination,
                "fromStation": from_station,
                "toStation": to_station,
                "body": body,
            },
            "response": payload,
        }
