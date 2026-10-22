from fastapi import APIRouter
from app.api.endpoints import auth, crops, live_prices, mandis, ml_predict, prices, recommendations

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to MandiWise API"}

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(crops.router, prefix="/crops", tags=["crops"])
router.include_router(mandis.router, prefix="/mandis", tags=["mandis"])
router.include_router(ml_predict.router, prefix="/predict", tags=["predict"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(live_prices.router, prefix="/live-prices", tags=["live-prices"])
router.include_router(prices.router, prefix="/prices", tags=["prices"])
