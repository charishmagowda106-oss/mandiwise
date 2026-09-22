"""Regenerate the demo market dataset end-to-end:

    real mandis -> sample price history CSV -> trained model

Run from the CKAM folder:
    set PYTHONPATH=backend
    .venv\\Scripts\\python.exe backend\\scripts\\rebuild_market_data.py

Afterwards, restart the backend so it picks up the new model (history reloads
automatically on next boot when the table is empty).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from app.database.session import SessionLocal, engine, Base
import app.models.models  # noqa: F401
from app.models.models import Crop, Mandi, HistoricalPrice
from app.services.karnataka_mandis import REAL_MANDIS


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Crop).count() == 0:
            from app.api.endpoints.crops import ensure_karnataka_crops
            ensure_karnataka_crops(db)
            print(f"Seeded {db.query(Crop).count()} crops")

        # 1) Replace whatever mandis exist (incl. "Mandi A..D") with real ones
        deleted_history = db.query(HistoricalPrice).delete()
        deleted_mandis = db.query(Mandi).delete()
        db.commit()
        db.add_all([Mandi(**row) for row in REAL_MANDIS])
        db.commit()
        print(f"Removed {deleted_mandis} dummy mandis + {deleted_history} old price rows; "
              f"seeded {db.query(Mandi).count()} real Karnataka mandis")
    finally:
        db.close()

    # 2) Regenerate the sample history CSV for every crop x real mandi, then train
    import train_ml
    train_ml.generate_sample_data()
    train_ml.train_model()

    # 3) Load the fresh CSV into the database
    from app.services.seed import _load_history
    from app.database.session import SessionLocal as SL
    db = SL()
    try:
        _load_history(db)
    finally:
        db.close()

    print("Rebuild complete. Restart the backend to serve the new data.")


if __name__ == "__main__":
    main()
