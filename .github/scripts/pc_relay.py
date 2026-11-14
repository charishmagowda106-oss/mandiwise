"""Publish the mandi feed from this PC (residential Indian connection).

data.gov.in refuses datacenter addresses (GitHub Actions, Render and Apify
have all been firewalled off) but answers ordinary Indian home connections.
This runner fetches the Karnataka price feed with the local network and
force-pushes ``karnataka.json`` to the ``live-data`` branch — the same
single-file payload .github/workflows/mandi-relay.yml publishes — so
https://mandiwise.onrender.com keeps serving fresh rates through
raw.githubusercontent.com.

One-time setup (see APP.md):
  * ``%LOCALAPPDATA%\\mandiwise-relay\\apikey.txt`` — your data.gov.in key
    (falls back to the shared demo key when missing).
  * ``register_pc_relay.ps1`` — registers the every-4-hours task.

The GitHub Actions workflow stays enabled as a backup: whichever runner
reaches data.gov.in first publishes; both write the same single-file branch.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = Path(os.environ.get("LOCALAPPDATA") or str(Path.home())) / "mandiwise-relay"
KEY_FILE = BASE / "apikey.txt"
LOG_FILE = BASE / "relay.log"
GIT_DIR = BASE / "repo"
FETCH_DIR = BASE / "fetch"
REPO_URL = "https://github.com/charishmagowda106-oss/mandiwise.git"

# A console python child would flash a window under pythonw.exe (the task's
# entry point); CREATE_NO_WINDOW keeps every child invisible either way.
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# Prefer the console interpreter for children so their output reaches our log
# even when this runner itself is started by pythonw.exe (no std streams).
PYTHON = Path(sys.executable)
if PYTHON.name.lower() == "pythonw.exe":
    _console = PYTHON.with_name("python.exe")
    if _console.exists():
        PYTHON = _console


def log(message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
    try:
        BASE.mkdir(parents=True, exist_ok=True)
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 1_000_000:
            LOG_FILE.replace(LOG_FILE.with_name("relay.old.log"))
        with LOG_FILE.open("a", encoding="utf-8", buffering=1) as handle:
            handle.write(line + "\n")
    except OSError:
        pass
    print(line, flush=True)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", *args],
        cwd=str(GIT_DIR),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=FLAGS,
    )
    detail = ((result.stderr or "") + (result.stdout or "")).strip()
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def fetch(env: dict) -> Path | None:
    """Run fetch_mandi.py; return the payload path, or None on failure."""
    FETCH_DIR.mkdir(parents=True, exist_ok=True)
    payload = FETCH_DIR / "karnataka.json"
    try:
        payload.unlink()  # a stale file must never be mistaken for fresh data
    except FileNotFoundError:
        pass
    result = subprocess.run(
        [str(PYTHON), str(HERE / "fetch_mandi.py")],
        cwd=str(FETCH_DIR),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=FLAGS,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    tail = [line for line in output.splitlines() if line.strip()][-3:]
    if result.returncode != 0 or not payload.exists():
        log(f"fetch failed (exit {result.returncode}): {' | '.join(tail)}")
        return None
    log(f"fetch ok: {' | '.join(tail)}")
    return payload


def publish(payload: Path) -> None:
    """Force-push payload as live-data/karnataka.json (single-file branch)."""
    GIT_DIR.mkdir(parents=True, exist_ok=True)
    if not (GIT_DIR / ".git").exists():
        git("init")
        git("remote", "add", "origin", REPO_URL)
    else:
        git("remote", "set-url", "origin", REPO_URL)
    git("config", "user.name", "mandiwise-relay")
    git("config", "user.email", "mandiwise-relay@users.noreply.github.com")

    fetched = git("fetch", "--depth", "1", "origin", "live-data", check=False)
    if fetched.returncode == 0:
        git("checkout", "-f", "-B", "live-data", "FETCH_HEAD")
    else:
        # Branch missing (first ever run) or a transient fetch error — history
        # does not matter anyway: every publish force-replaces the whole file.
        git("checkout", "--orphan", "live-data", check=False)
        git("rm", "-rq", "--cached", ".", check=False)

    shutil.copyfile(payload, GIT_DIR / "karnataka.json")
    git("add", "-f", "karnataka.json")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    committed = git("commit", "-m", f"sync {stamp}", check=False)
    if committed.returncode != 0:
        output = (committed.stdout or "") + (committed.stderr or "")
        if "nothing to commit" not in output:
            raise RuntimeError(f"commit failed: {output.strip()}")
        log("karnataka.json unchanged — already published")
        return
    git("push", "--force", "origin", "HEAD:live-data")
    log("published live-data/karnataka.json")


def main() -> int:
    log("relay run started")
    BASE.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    if KEY_FILE.exists():
        env["DATA_GOV_API_KEY"] = KEY_FILE.read_text(encoding="utf-8").strip()
    else:
        log(f"warning: {KEY_FILE} missing — falling back to the shared demo key")

    payload = fetch(env)
    if payload is None:
        return 1
    publish(payload)
    log("relay run finished")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # a dead task must still leave a trace in the log
        log(f"ERROR: {exc.__class__.__name__}: {exc}")
        sys.exit(1)
