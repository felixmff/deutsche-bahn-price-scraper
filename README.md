# Deutsche Bahn Web API Scraper

Standalone [Apify Actor](https://docs.apify.com) — thin wrapper around the unofficial **bahn.de web API**. No dependency on RailCal or other app code.

## API surface

Documented in [`openapi/bahn-web-api.openapi.json`](openapi/bahn-web-api.openapi.json):

| Endpoint | bahn.de path | Method |
|----------|----------------|--------|
| `orte` | `/web/api/reiseloesung/orte` | GET |
| `fahrplan` | `/web/api/angebote/fahrplan` | POST |

Each run writes **one dataset item** with `request` + `response` (upstream JSON, unchanged).

## Local run

```bash
cd deutsche-bahn-price-scraper
uv sync
apify login
apify run --input-file .actor/example-input.json
```

## Deploy

```bash
apify push
```

Self-contained — no sibling repos required.
