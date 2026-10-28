"""Mandi ranking: distance-aware profit comparison, shared by the compare
endpoint, price alerts, and the alert checker so every surface agrees."""

from __future__ import annotations

import math

from sqlalchemy.orm import Session

from app.models.models import Crop, HistoricalPrice, Mandi


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (
        math.sin(dLat / 2) * math.sin(dLat / 2)
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def rank_mandis(
    db: Session,
    *,
    crop_id: int,
    quantity: float,
    unit: str,
    lat: float,
    lng: float,
    transport_rate_per_km: float,
) -> list[dict]:
    """Profit-ranked mandis for a crop shipped from (lat, lng).

    Returns dicts identical to the /recommendations/compare response rows.
    """
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        return []
    mandis = db.query(Mandi).all()

    quantity_quintals = quantity if unit == "quintal" else quantity / 100.0

    results = []
    for m in mandis:
        if m.lat is None or m.lng is None:
            continue
        latest_price = (
            db.query(HistoricalPrice)
            .filter(HistoricalPrice.crop_id == crop_id, HistoricalPrice.mandi_id == m.id)
            .order_by(HistoricalPrice.date.desc())
            .first()
        )
        if not latest_price:
            continue
        dist = haversine(lat, lng, m.lat, m.lng)
        price_per_quintal = latest_price.modal_price
        revenue = price_per_quintal * quantity_quintals
        transport = dist * transport_rate_per_km
        profit = revenue - transport
        results.append(
            {
                "mandi_id": m.id,
                "mandi_name": m.name,
                "distance_km": round(dist, 2),
                "current_price": round(price_per_quintal, 2),
                "transport_cost": round(transport, 2),
                "expected_revenue": round(revenue, 2),
                "estimated_profit": round(profit, 2),
            }
        )

    results.sort(key=lambda x: x["estimated_profit"], reverse=True)
    for idx, r in enumerate(results):
        r["rank"] = idx + 1
        r["recommendation"] = "BEST MANDI" if idx == 0 else "ALTERNATIVE"
    return results
