"""Price-alert evaluation: notify farmers when their crop can be sold at the
best (usually nearest) mandi for a good profit.

An alert fires when all of these hold:
  1. the best mandi's estimated profit >= the farmer's min_profit (if set),
  2. something changed since the last notification (different best mandi, or
     profit improved) — so we never spam about a static situation,
  3. the per-alert cooldown has passed.

Each notification is stored in-app (bell icon) and, when SMTP is configured,
emailed to the farmer.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta

from app.database.session import SessionLocal
from app.models.models import Notification, PriceAlert, User
from app.services import notify
from app.services.ranking import rank_mandis

log = logging.getLogger("mandiwise.alerts")

CHECK_INTERVAL_SECONDS = int(os.getenv("ALERT_CHECK_INTERVAL_SECONDS", "120"))
COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "240"))
# Ignore sub-₹1 / sub-0.5% profit wobble when deciding "something changed".
CHANGE_FLOOR = 1.0


def _money(value: float) -> str:
    return f"{value:,.0f}"


def evaluate_alert(db, alert: PriceAlert) -> Notification | None:
    """Return a new Notification if the alert should fire, else None.
    Mutates and persists the alert's evaluation state."""
    if not alert.active:
        return None

    lat, lng = alert.lat, alert.lng
    if lat is None or lng is None:
        user = db.get(User, alert.user_id)
        if user is None or user.location_lat is None or user.location_lng is None:
            return None  # nowhere to measure distance from
        lat, lng = user.location_lat, user.location_lng

    ranking = rank_mandis(
        db,
        crop_id=alert.crop_id,
        quantity=alert.quantity,
        unit=alert.unit,
        lat=lat,
        lng=lng,
        transport_rate_per_km=alert.transport_rate_per_km,
    )
    if not ranking:
        return None

    best = ranking[0]
    nearest = min(ranking, key=lambda row: row["distance_km"])
    profit = float(best["estimated_profit"])

    meets_threshold = alert.min_profit is None or profit >= alert.min_profit
    improved = (
        alert.last_best_profit is None
        or best["mandi_id"] != alert.last_best_mandi_id
        or profit - alert.last_best_profit >= CHANGE_FLOOR
    )
    cooled = alert.last_notified_at is None or datetime.utcnow() - alert.last_notified_at >= timedelta(
        minutes=COOLDOWN_MINUTES
    )

    if not (meets_threshold and improved and cooled):
        # Remember the state so a later real change can be detected.
        if alert.last_best_profit is None:
            alert.last_best_mandi_id = best["mandi_id"]
            alert.last_best_profit = profit
            db.commit()
        return None

    crop_name = alert.crop.name if alert.crop else "Your crop"
    title = f"{crop_name}: ₹{_money(profit)} profit at {best['mandi_name']}"
    body = (
        f"{alert.quantity:g} {alert.unit} of {crop_name} at ₹{_money(best['current_price'])}/quintal "
        f"− ₹{_money(best['transport_cost'])} transport = about ₹{_money(profit)} profit "
        f"({best['distance_km']:.1f} km away)."
    )
    if nearest["mandi_id"] != best["mandi_id"]:
        body += f" Nearest mandi: {nearest['mandi_name']} ({nearest['distance_km']:.1f} km)."
    if alert.min_profit is not None:
        body += f" Your target was ₹{_money(alert.min_profit)}."

    notification = Notification(
        user_id=alert.user_id,
        kind="price_alert",
        title=title,
        body=body,
        link="/compare",
    )
    db.add(notification)
    alert.last_best_mandi_id = best["mandi_id"]
    alert.last_best_profit = profit
    alert.last_notified_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)

    user = db.get(User, alert.user_id)
    if user is not None and notify.smtp_configured():
        notify.send_email(user.email, f"MandiWise price alert — {title}", f"{title}\n\n{body}")
    return notification


def run_alert_check() -> int:
    """Evaluate every active alert once. Safe to call from a thread or endpoint."""
    db = SessionLocal()
    created = 0
    try:
        alerts = db.query(PriceAlert).filter(PriceAlert.active.is_(True)).all()
        for alert in alerts:
            try:
                if evaluate_alert(db, alert) is not None:
                    created += 1
            except Exception as exc:  # one bad alert must not block the rest
                log.warning("alert %s failed: %s", alert.id, exc)
        if created:
            log.info("[alerts] created %s notification(s)", created)
    finally:
        db.close()
    return created


async def alert_worker() -> None:
    """Background loop started with the app (see main.py lifespan)."""
    # First pass shortly after boot, then on the configured interval.
    await asyncio.sleep(15)
    while True:
        try:
            await asyncio.to_thread(run_alert_check)
        except Exception as exc:
            log.warning("[alerts] check failed: %s", exc)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
