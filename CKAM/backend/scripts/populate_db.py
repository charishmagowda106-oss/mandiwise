"""Populate an empty database (crops, real mandis, sample history).

On a normal boot the API seeds itself via app.services.seed.ensure_seed();
this script is the manual equivalent (used by start_mandiwise.bat).
"""

from app.services.seed import ensure_seed

if __name__ == "__main__":
    ensure_seed()
    print("Database populated.")
