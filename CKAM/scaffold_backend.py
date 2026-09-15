import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

main_py = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.database.session import Base, engine
import app.models.models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MandiWise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
"""
write_file('backend/app/main.py', main_py)

api_router_py = """
from fastapi import APIRouter
from app.api.endpoints import auth, crops, mandis, ml_predict, recommendations

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(crops.router, prefix="/crops", tags=["crops"])
router.include_router(mandis.router, prefix="/mandis", tags=["mandis"])
router.include_router(ml_predict.router, prefix="/predict", tags=["predict"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
"""
write_file('backend/app/api/__init__.py', api_router_py)
