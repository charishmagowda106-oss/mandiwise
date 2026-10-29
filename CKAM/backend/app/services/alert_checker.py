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
from datetime import date, datetime, timedelta

from app.database.session import SessionLocal
from app.models.models import Notification, PriceAlert, User, UserCrop
from app.services import notify
from app.services.ranking import rank_mandis

log = logging.getLogger("mandiwise.alerts")

CHECK_INTERVAL_SECONDS = int(os.getenv("ALERT_CHECK_INTERVAL_SECONDS", "120"))
COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "240"))
# Ignore sub-₹1 / sub-0.5% profit wobble when deciding "something changed".
CHANGE_FLOOR = 1.0
# A watched crop notifies once when its harvest date is this close or past.
HARVEST_WINDOW_DAYS = 7


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


def evaluate_harvest_windows(db) -> int:
    """Notify each farmer once when a watched crop's harvest date is due
    (or within HARVEST_WINDOW_DAYS), with the best mandi to sell at today."""
    today = date.today()
    due = (
        db.query(UserCrop)
        .filter(
            UserCrop.expected_harvest_date.isnot(None),
            UserCrop.harvest_notified_at.is_(None),
            UserCrop.expected_harvest_date <= today + timedelta(days=HARVEST_WINDOW_DAYS),
        )
        .all()
    )
    created = 0
    for uc in due:
        try:
            crop_name = uc.crop.name if uc.crop else "Your crop"
            days = (uc.expected_harvest_date - today).days
            if days < 0:
                when = f"was due {-days} day(s) ago"
            elif days == 0:
                when = "is due today"
            else:
                when = f"is due in {days} day(s)"
            title = f"{crop_name}: harvest {when}"

            lat = uc.lat if uc.lat is not None else None
            lng = uc.lng if uc.lng is not None else None
            if lat is None or lng is None:
                user = db.get(User, uc.user_id)
                if user is not None:
                    lat, lng = user.location_lat, user.location_lng
            body = f"You marked {uc.quantity:g} quintals of {crop_name} for this harvest."
            if lat is not None and lng is not None:
                ranking = rank_mandis(
                    db, crop_id=uc.crop_id, quantity=uc.quantity, unit="quintal",
                    lat=lat, lng=lng, transport_rate_per_km=10.0,
                )
                if ranking:
                    best = ranking[0]
                    body += (
                        f" Today's best: {best['mandi_name']} at ₹{_money(best['current_price'])}/quintal"
                        f" — about ₹{_money(best['expected_revenue'])} for your quantity"
                        f" ({best['distance_km']:.1f} km away)."
                    )
            body += " Open the app to compare all nearby mandis."

            notification = Notification(
                user_id=uc.user_id,
                kind="harvest_window",
                title=title,
                body=body,
                link="/",
            )
            db.add(notification)
            uc.harvest_notified_at = datetime.utcnow()
            db.commit()
            created += 1

            farmer = db.get(User, uc.user_id)
            if farmer is not None and notify.smtp_configured():
                notify.send_email(farmer.email, f"MandiWise harvest reminder — {title}", f"{title}\n\n{body}")
        except Exception as exc:  # one bad crop must not block the rest
            log.warning("harvest check for crop %s failed: %s", uc.id, exc)
            db.rollback()
    return created


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
        created += evaluate_harvest_windows(db)
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
