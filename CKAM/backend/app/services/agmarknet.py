"""Live Karnataka mandi price client.

Fetch order (freshness-aware):
1. The daily AGMARKNET mirror (fast, keyless, synced from data.gov.in) —
   used when its newest sync is younger than MIRROR_MAX_AGE.
2. The official data.gov.in AGMARKNET resource (preferred while the mirror
   is stale or down; needs DATA_GOV_API_KEY — the public demo key is dead).
3. If both fail, the stale mirror data is still served, flagged ``stale=True``
   so the UI can label it honestly instead of pretending it is today's rate.

Results are cached in-process (TTL below) so we stay inside the mirror's free
rate limit (100 requests / 15 minutes / IP).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

log = logging.getLogger("mandiwise.agmarknet")

MIRROR_URL = "https://mandi-api.onrender.com/v1/prices"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
# data.gov.in's documented public demonstration key. Deployments should set
# DATA_GOV_API_KEY to their own key, so rate limits are not shared.
DEMO_API_KEY = "579b464db66ec23bdd0000017e2b72a7"

CACHE_TTL_SECONDS = 10 * 60  # 10 minutes
MIRROR_TIMEOUT = 45.0        # Render free services may cold-start
DATAGOV_TIMEOUT = 30.0       # official API is slow from outside India
# A mirror sync older than this is treated as stale: prefer data.gov.in, and
# if that fails too, serve the stale data with an honest flag.
MIRROR_MAX_AGE = timedelta(hours=48)


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


def _data_age(updated_at: Any) -> timedelta | None:
    """How old the payload's newest sync is; None when it cannot be parsed."""
    if not updated_at:
        return None
    try:
        stamp = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - stamp


def _api_key() -> str:
    # Empty string on Render must fall back to the demo key, not be sent as-is.
    return (os.getenv("DATA_GOV_API_KEY") or "").strip() or DEMO_API_KEY


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
        "api-key": _api_key(),
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
    """Return current Karnataka mandi records, normalised, from the freshest source."""
    limit = min(max(limit, 1), 200)
    key = (commodity or "").strip().lower()

    cached = _cache_get(key)
    if cached:
        return {**cached, "cached": True}

    failures: list[str] = []

    # 1) Mirror first — fast and keyless, but only trusted while its own sync
    #    is recent (its daily job has been known to silently die for weeks).
    mirror_payload: dict[str, Any] | None = None
    try:
        mirror_payload = _fetch_mirror(commodity, limit)
    except Exception as exc:
        failures.append(f"_fetch_mirror: {exc}")
        log.warning("live-price mirror failed: %s", exc)

    if mirror_payload is not None:
        age = _data_age(mirror_payload.get("updated_at"))
        if age is not None and age <= MIRROR_MAX_AGE:
            payload = {**mirror_payload, "stale": False}
            _cache_put(key, payload)
            return {**payload, "cached": False}
        failures.append(f"_fetch_mirror: newest sync is {age} old (limit {MIRROR_MAX_AGE})")
        log.warning("mirror stale (%s old) — trying official data.gov.in", age)

    # 2) Mirror stale or down → official data.gov.in (needs a real API key).
    try:
        payload = _fetch_datagov(commodity, limit)
        if payload["records"]:
            fresh = {**payload, "stale": False}
            _cache_put(key, fresh)
            return {**fresh, "cached": False}
        failures.append("_fetch_datagov: no records")
        log.warning("data.gov.in returned no records")
    except Exception as exc:
        failures.append(f"_fetch_datagov: {exc}")
        log.warning("data.gov.in failed: %s", exc)

    # 3) Nothing fresh: serve the last mirror data, honestly flagged as stale,
    #    so the UI can show the real sync date instead of implying it is live.
    if mirror_payload is not None and mirror_payload["records"]:
        log.warning("serving stale mirror data (sync %s) — %s",
                    mirror_payload.get("updated_at"), "; ".join(failures))
        stale_payload = {**mirror_payload, "stale": True}
        _cache_put(key, stale_payload)
        return {**stale_payload, "cached": False}

    raise LiveMarketDataError(
        "The live mandi feed is temporarily unavailable — both the daily sync "
        "and the official data.gov.in source failed. Please try again in a minute."
    )
