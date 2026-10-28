from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
import os

from app.services.seed import ensure_seed

# Create tables and seed empty ones (crops, real Karnataka mandis, sample history)
ensure_seed()

from contextlib import asynccontextmanager  # noqa: E402
import asyncio  # noqa: E402

from app.services.alert_checker import alert_worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Run the price-alert checker alongside the API."""
    worker = asyncio.create_task(alert_worker())
    try:
        yield
    finally:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass


app = FastAPI(title="MandiWise API", lifespan=lifespan)

allowed_origins = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS",
    # localhost dev servers + the Capacitor app WebView (https://localhost)
    # + phone-on-LAN access to the dev server.
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,"
    "http://localhost:8000,http://127.0.0.1:8000,https://localhost,"
    "http://localhost,capacitor://localhost",
).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


# ---- Serve the built React app so one deployment = one URL ----
from pathlib import Path  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if DIST_DIR.is_dir():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="web_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        # API routes above are matched first; everything else falls back to the SPA.
        if full_path:
            candidate = DIST_DIR / full_path
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
