"""Apify Actor — passthrough to bahn.de web API."""

from __future__ import annotations

from typing import Any, Literal

from apify import Actor

from .bahn.client import BahnWebClient
from .bahn.models import FahrplanSearchInput, OrtSearchInput
from .bahn.proxy import proxy_pool_from_apify

Endpoint = Literal["orte", "fahrplan"]


async def main() -> None:
    async with Actor:
        raw: dict[str, Any] = await Actor.get_input() or {}
        endpoint: Endpoint = raw.get("endpoint", "fahrplan")  # type: ignore[assignment]
        proxy_input = raw.get("proxyConfiguration") or {}

        proxy_cfg = await Actor.create_proxy_configuration(
            actor_proxy_input=proxy_input or None,
        )
        proxy_pool = None
        if proxy_cfg is not None:
            proxy_pool = await proxy_pool_from_apify(proxy_cfg, pool_size=10)
            Actor.log.info("Using Apify Proxy")

        async with BahnWebClient(proxy_pool=proxy_pool) as client:
            if endpoint == "orte":
                search = OrtSearchInput(
                    query=str(raw["query"]).strip(),
                    typ=raw.get("stationType", "ALL"),  # type: ignore[arg-type]
                    limit=int(raw.get("limit", 5)),
                )
                data = await client.search_orte(search)
                await Actor.push_data(
                    {
                        "endpoint": "orte",
                        "method": "GET",
                        "path": "/reiseloesung/orte",
                        "request": search.model_dump(),
                        "response": data,
                    }
                )
                Actor.log.info("orte: %d station(s)", len(data))
                return

            if endpoint == "fahrplan":
                search = FahrplanSearchInput.from_actor_input(raw)
                result = await client.search_fahrplan(search)
                verbindungen = result["response"].get("verbindungen", [])
                await Actor.push_data(
                    {
                        "endpoint": "fahrplan",
                        "method": "POST",
                        "path": "/angebote/fahrplan",
                        "request": {
                            **search.model_dump(mode="json"),
                            **result["request"],
                        },
                        "response": result["response"],
                        "connectionCount": len(verbindungen),
                    }
                )
                Actor.log.info("fahrplan: %d connection(s)", len(verbindungen))
                return

            raise ValueError(f"Unknown endpoint: {endpoint!r}. Use 'orte' or 'fahrplan'.")
