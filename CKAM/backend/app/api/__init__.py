from fastapi import APIRouter
from app.api.endpoints import auth, crops, mandis, ml_predict, recommendations

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to MandiWise API"}

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(crops.router, prefix="/crops", tags=["crops"])
router.include_router(mandis.router, prefix="/mandis", tags=["mandis"])
router.include_router(ml_predict.router, prefix="/predict", tags=["predict"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
