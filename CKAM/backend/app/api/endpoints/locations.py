"""Place search for the manual location picker.

Two sources, in order:
1. Local: the mandis already in our database + a bundled list of Karnataka
   towns — instant, offline-safe, and covers what farmers actually need.
2. OpenStreetMap (Nominatim) for everything else, called politely: proper
   User-Agent, short timeout, an in-memory cache, and a 1 request/second
   guard per their usage policy.
"""
import time

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.session import SessionLocal
from app.models.models import Mandi

router = APIRouter()

# Karnataka district headquarters and major towns: (name, lat, lng).
KARNATAKA_TOWNS = [
    ("Bengaluru", 12.9716, 77.5946),
    ("Mysuru", 12.2958, 76.6394),
    ("Mangaluru", 12.9141, 74.8560),
    ("Hubballi-Dharwad", 15.3647, 75.1240),
    ("Belagavi", 15.8497, 74.4977),
    ("Kalaburagi", 17.3290, 76.8342),
    ("Davanagere", 14.4644, 75.9219),
    ("Ballari", 15.1394, 76.9214),
    ("Vijayapura", 16.8299, 75.7143),
    ("Shivamogga", 13.9299, 75.5681),
    ("Tumakuru", 13.3392, 77.1139),
    ("Udupi", 13.3409, 74.7551),
    ("Kolar", 13.1367, 78.1287),
    ("Chitradurga", 14.2305, 76.3985),
    ("Hassan", 13.0000, 76.0967),
    ("Mandya", 12.5218, 76.8951),
    ("Raichur", 16.2055, 77.3556),
    ("Bidar", 17.9104, 77.5197),
    ("Karwar", 14.8135, 74.1297),
    ("Haveri", 14.7936, 75.4029),
    ("Gadag", 15.4294, 75.6290),
    ("Koppal", 15.3500, 76.1500),
    ("Yadgir", 16.7700, 77.1375),
    ("Chamarajanagar", 11.9200, 76.9400),
    ("Chikkamagaluru", 13.3152, 75.7755),
    ("Madikeri (Kodagu)", 12.4244, 75.7382),
    ("Bagalkote", 16.1697, 75.6964),
    ("Ramanagara", 12.7200, 77.2800),
    ("Chikkaballapur", 13.4300, 77.7300),
    ("Gokak", 15.8300, 74.8200),
    ("Krishnarajapete", 12.7000, 76.4900),
    ("Doddaballapura", 13.2900, 77.5700),
    ("Tarikere", 13.7100, 75.8100),
    ("Sagara", 14.1700, 75.0300),
    ("Sirsi", 14.6200, 74.8300),
    ("Bhatkal", 13.9800, 74.5500),
    ("Athani", 16.7300, 75.0600),
    ("Afzalpur", 17.2000, 76.3600),
    ("Lingsugur", 16.1600, 76.5200),
    ("Channapatna", 12.6500, 77.2000),
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MandiWise/1.0 (mandi price guidance demo app)"
CACHE_TTL_SECONDS = 300
OSM_MIN_INTERVAL = 1.1  # Nominatim policy: max 1 request/second

_cache: dict = {}
_last_osm_at = 0.0


class PlaceResult(BaseModel):
    name: str
    display: str
    lat: float
    lng: float
    source: str  # "mandi" | "town" | "osm"


class SearchResponse(BaseModel):
    query: str
    results: list


def _match_rank(query: str, candidate: str):
    """0 exact, 1 prefix, 2 substring; None = no match."""
    q = query.lower().strip()
    c = candidate.lower().strip()
    if not q or not c:
        return None
    if c == q:
        return 0
    if c.startswith(q):
        return 1
    if q in c:
        return 2
    return None


def _local_results(query: str, limit: int) -> list:
    scored = []
    db = SessionLocal()
    try:
        mandis = db.query(Mandi).filter(Mandi.lat.isnot(None), Mandi.lng.isnot(None)).all()
    finally:
        db.close()
    for mandi in mandis:
        display = f"{mandi.name}, {mandi.district}"
        for label in (mandi.name, mandi.district):
            rank = _match_rank(query, label)
            if rank is not None:
                scored.append((rank, 0, mandi.name, PlaceResult(
                    name=mandi.name, display=display,
                    lat=mandi.lat, lng=mandi.lng, source="mandi",
                )))
                break  # one entry per mandi
    for name, lat, lng in KARNATAKA_TOWNS:
        rank = _match_rank(query, name)
        if rank is not None:
            scored.append((rank, 1, name, PlaceResult(
                name=name, display=f"{name}, Karnataka",
                lat=lat, lng=lng, source="town",
            )))
    scored.sort(key=lambda item: item[:3])
    results, seen = [], set()
    for _, _, _, place in scored:
        key = place.name.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(place)
        if len(results) >= limit:
            break
    return results


def _fetch_osm(query: str, limit: int) -> list:
    """Query Nominatim; return [] on any failure (local results still work)."""
    global _last_osm_at
    if time.monotonic() - _last_osm_at < OSM_MIN_INTERVAL:
        return []
    _last_osm_at = time.monotonic()
    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "jsonv2",
                "countrycodes": "in",
                "limit": limit,
                "addressdetails": 0,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=6.0,
        )
        response.raise_for_status()
        places = []
        for row in response.json():
            try:
                places.append(PlaceResult(
                    name=str(row.get("name") or row.get("display_name", query)).split(",")[0],
                    display=str(row.get("display_name", "")),
                    lat=float(row["lat"]),
                    lng=float(row["lon"]),
                    source="osm",
                ))
            except (KeyError, ValueError, TypeError):
                continue
        return places
    except (httpx.HTTPError, ValueError, TypeError):
        return []


def _search(query: str, limit: int) -> SearchResponse:
    query = query.strip()
    key = (query.lower(), limit)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    results = _local_results(query, limit)
    if len(results) < limit and len(query) >= 3:
        known = {p.name.lower() for p in results}
        for place in _fetch_osm(query, limit - len(results)):
            if place.name.lower() not in known:
                results.append(place)
                known.add(place.name.lower())
    response = SearchResponse(query=query, results=results[:limit])

    if len(_cache) > 200:
        _cache.clear()
    _cache[key] = (time.monotonic(), response)
    return response


@router.get("/search", response_model=SearchResponse)
def search_locations(
    q: str = Query(..., min_length=2, max_length=80, description="Town, city or mandi name"),
    limit: int = Query(8, ge=1, le=15),
):
    """Search places by name (local mandis/towns first, then OpenStreetMap)."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="Search text is required")
    return _search(q, limit)
