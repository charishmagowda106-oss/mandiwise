"""Fetch the official AGMARKNET daily price feed for Karnataka.

Runs on GitHub Actions: their runners reach api.data.gov.in, while Render's
US IPs are firewalled off ([Errno 113] No route to host). Writes
``karnataka.json`` at the repo root, which the workflow publishes to the
``live-data`` branch for MandiWise to read via raw.githubusercontent.com.

Set the ``DATA_GOV_API_KEY`` repository secret to use your own (free)
data.gov.in key and get a dedicated rate quota instead of the shared demo key.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
DEFAULT_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
PAGE_SIZE = 1000
MAX_PAGES = 10
RETRY_ATTEMPTS = 20      # patient retries ride out shared-key 429 windows
RETRY_SLEEP_SECONDS = 60
HTTP_TIMEOUT = 30.0      # keep worst-case retries inside the job's 25 minutes


def fetch_page(api_key: str, offset: int) -> dict:
    params = urllib.parse.urlencode(
        {
            "api-key": api_key,
            "format": "json",
            "limit": PAGE_SIZE,
            "offset": offset,
            "filters[state]": "Karnataka",
        }
    )
    request = urllib.request.Request(
        f"{URL}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    # CI captures stdout in blocks — stream lines so retry progress is visible
    # live in the Actions log instead of arriving all at once at exit.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    api_key = (os.environ.get("DATA_GOV_API_KEY") or "").strip() or DEFAULT_KEY
    records: list[dict] = []
    attempts = 0

    while len(records) < PAGE_SIZE * MAX_PAGES:
        attempts += 1
        if attempts > RETRY_ATTEMPTS + MAX_PAGES:
            break
        try:
            data = fetch_page(api_key, len(records))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"fetch error: {exc!r}")
            data = {}

        rows = data.get("records") or []
        if not rows:
            if data.get("error"):
                print(f"upstream said: {data['error']}")
            if attempts <= RETRY_ATTEMPTS:
                print(f"no data yet (attempt {attempts}), sleeping {RETRY_SLEEP_SECONDS}s")
                time.sleep(RETRY_SLEEP_SECONDS)
                continue
            break

        # Guard against a backend that ignores `offset` and repeats page one.
        if records and rows[0] == records[0]:
            print("pagination ignored offset — stopping at first page")
            break

        records.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        time.sleep(2)

    if not records:
        print("::error::No records fetched from data.gov.in")
        return 1

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(records),
        "records": records,
    }
    with open("karnataka.json", "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
    print(f"fetched {len(records)} Karnataka records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
