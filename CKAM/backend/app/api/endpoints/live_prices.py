from fastapi import APIRouter, HTTPException, Query

from app.services.agmarknet import LiveMarketDataError, get_karnataka_prices

router = APIRouter()


@router.get("/karnataka")
def get_live_karnataka_prices(
    commodity: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=100, ge=1, le=100),
):
    """Latest official Karnataka wholesale rates, fetched when requested."""
    try:
        return get_karnataka_prices(commodity=commodity, limit=limit)
    except LiveMarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
