"""Live Karnataka mandi price client.

Fetch order:
1. The daily AGMARKNET mirror (fast, keyless, synced from data.gov.in).
2. The official data.gov.in AGMARKNET resource (used when the mirror is down).

Results are cached in-process (TTL below) so we stay inside the mirror's free
rate limit (100 requests / 15 minutes / IP).
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

import httpx

MIRROR_URL = "https://mandi-api.onrender.com/v1/prices"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
# data.gov.in's documented public demonstration key. Deployments should set
# DATA_GOV_API_KEY to their own key, so rate limits are not shared.
DEMO_API_KEY = "579b464db66ec23bdd0000017e2b72a7"

CACHE_TTL_SECONDS = 10 * 60  # 10 minutes
MIRROR_TIMEOUT = 45.0        # Render free services may cold-start
DATAGOV_TIMEOUT = 15.0


class LiveMarketDataError(Exception):
    """The official live feed could not be read from any source."""


_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


def _number(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _cache_get(key: str) -> dict[str, Any] | None:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry[0] < CACHE_TTL_SECONDS:
            return entry[1]
    return None


def _cache_put(key: str, payload: dict[str, Any]) -> None:
    with _cache_lock:
        _cache[key] = (time.time(), payload)


def _normalise(record: dict[str, Any]) -> dict[str, Any] | None:
    modal = _number(record.get("modal_price"))
    if modal is None:
        return None
    return {
        "state": record.get("state") or "Karnataka",
        "district": record.get("district", ""),
        "mandi": record.get("mandi") or record.get("market") or "Unknown market",
        "commodity": record.get("commodity", ""),
        "variety": record.get("variety", ""),
        "arrival_date": str(record.get("arrival_date", "")),
        "min_price": _number(record.get("min_price")),
        "max_price": _number(record.get("max_price")),
        "modal_price": modal,
        "unit": "₹/quintal",
    }


def _fetch_mirror(commodity: str | None, limit: int) -> dict[str, Any]:
    params: dict[str, Any] = {"state": "Karnataka"}
    if commodity:
        params["commodity"] = commodity
    response = httpx.get(MIRROR_URL, params=params, timeout=MIRROR_TIMEOUT, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise LiveMarketDataError(payload.get("error", {}).get("message", "mirror rejected the query"))

    raw = payload.get("data", [])
    records = [r for r in (_normalise(item) for item in raw) if r]
    synced_at = ""
    for item in raw:
        fetched = item.get("fetched_at")
        if fetched and (not synced_at or fetched > synced_at):
            synced_at = fetched
    updated_at = synced_at or datetime.now(timezone.utc).isoformat()
    return {
        "source": "AGMARKNET / data.gov.in (daily sync)",
        "updated_at": updated_at,
        "records": records[:limit],
    }


def _fetch_datagov(commodity: str | None, limit: int) -> dict[str, Any]:
    params: dict[str, Any] = {
        "api-key": os.getenv("DATA_GOV_API_KEY", DEMO_API_KEY),
        "format": "json",
        "limit": min(max(limit, 1), 100),
        "filters[state]": "Karnataka",
    }
    if commodity:
        params["filters[commodity]"] = commodity
    response = httpx.get(API_URL, params=params, timeout=DATAGOV_TIMEOUT, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    records = [r for r in (_normalise(item) for item in payload.get("records", [])) if r]
    return {
        "source": "AGMARKNET / data.gov.in (live)",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "records": records[:limit],
    }


def get_karnataka_prices(commodity: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Return current Karnataka mandi records, normalised, from the best source."""
    limit = min(max(limit, 1), 200)
    key = (commodity or "").strip().lower()

    cached = _cache_get(key)
    if cached:
        return {**cached, "cached": True}

    failures: list[str] = []
    for fetcher in (_fetch_mirror, _fetch_datagov):
        try:
            payload = fetcher(commodity, limit)
        except Exception as exc:  # network / upstream problems all land here
            failures.append(f"{fetcher.__name__}: {exc}")
            continue
        if not payload["records"]:
            failures.append(f"{fetcher.__name__}: no records")
            continue
        _cache_put(key, payload)
        return {**payload, "cached": False}

    raise LiveMarketDataError(
        "The live mandi feed is temporarily unavailable — both the daily sync "
        "and the official data.gov.in source failed. Please try again in a minute."
    )
