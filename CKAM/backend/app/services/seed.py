"""Start-up seeding: crops, real Karnataka mandis, and sample price history.

Safe to call on every boot — each step only runs when its table is empty, so a
fresh database (local SQLite or Render's Postgres) fills itself in.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text

from app.database.session import Base, SessionLocal, engine
import app.models.models  # noqa: F401  (register mappings before create_all)
from app.models.models import Crop, Mandi, HistoricalPrice
from app.services.karnataka_mandis import REAL_MANDIS

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HISTORY_CSV = PROJECT_ROOT / "data" / "sample" / "historical_prices.csv"

# Columns added after the first release. create_all() never alters existing
# tables, so these get appended here (SQLite and Postgres both accept ADD COLUMN).
USER_COLUMNS = {
    "phone": "VARCHAR",
    "phone_verified": "BOOLEAN DEFAULT FALSE",
}


def _ensure_user_columns() -> None:
    try:
        existing = {column["name"] for column in inspect(engine).get_columns("users")}
        with engine.begin() as conn:
            for name, ddl_type in USER_COLUMNS.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl_type}"))
                    print(f"[migrate] added users.{name}")
    except Exception as exc:  # never block start-up on migration
        print(f"[migrate] skipped ({exc})")


def _seed_mandis(db) -> None:
    db.add_all([Mandi(**row) for row in REAL_MANDIS])
    db.commit()


def _load_history(db) -> None:
    """Bulk-load the sample history CSV with pandas (fast, low memory)."""
    if not HISTORY_CSV.is_file():
        print(f"[seed] no history CSV at {HISTORY_CSV}; run scripts/rebuild_market_data.py")
        return

    frame = pd.read_csv(HISTORY_CSV)
    crop_ids = {name: cid for cid, name in db.query(Crop.id, Crop.name).all()}
    mandi_ids = {name: mid for mid, name in db.query(Mandi.id, Mandi.name).all()}

    frame["crop_id"] = frame["crop"].map(crop_ids)
    frame["mandi_id"] = frame["mandi"].map(mandi_ids)
    unknown_crops = sorted(set(frame.loc[frame["crop_id"].isna(), "crop"]))
    unknown_mandis = sorted(set(frame.loc[frame["mandi_id"].isna(), "mandi"]))
    frame = frame.dropna(subset=["crop_id", "mandi_id"])
    if frame.empty:
        print("[seed] history CSV matched no DB rows; skipped")
        return

    out = pd.DataFrame({
        "crop_id": frame["crop_id"].astype(int),
        "mandi_id": frame["mandi_id"].astype(int),
        "date": frame["date"].astype(str).str[:10],
        "min_price": (frame["modal_price"] * 0.92).round(2),
        "max_price": (frame["modal_price"] * 1.08).round(2),
        "modal_price": frame["modal_price"].astype(float),
        "unit": "quintal",
    })
    out.to_sql(HistoricalPrice.__tablename__, engine, if_exists="append", index=False)
    print(f"[seed] loaded {len(out)} sample price rows")
    if unknown_crops:
        print(f"[seed] CSV crops missing from DB (ignored): {unknown_crops}")
    if unknown_mandis:
        print(f"[seed] CSV mandis missing from DB (ignored): {unknown_mandis}")


def ensure_seed() -> None:
    """Create tables and fill empty ones. Idempotent."""
    Base.metadata.create_all(bind=engine)
    _ensure_user_columns()  # create_all never adds columns to existing tables
    db = SessionLocal()
    try:
        if db.query(Crop).count() == 0:
            from app.api.endpoints.crops import ensure_karnataka_crops
            ensure_karnataka_crops(db)
            print(f"[seed] seeded {db.query(Crop).count()} crops")
        if db.query(Mandi).count() == 0:
            _seed_mandis(db)
            print(f"[seed] seeded {db.query(Mandi).count()} real Karnataka mandis")
        if db.query(HistoricalPrice).count() == 0:
            _load_history(db)
    except Exception as exc:  # never block API start-up on seeding
        print(f"[seed] skipped ({exc})")
    finally:
        db.close()
