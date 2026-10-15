import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from app.db.database import create_db_and_tables
from app.api.v1.tickets_api import router as tickets_router
from app.api.v1.foods_api import router as foods_router
from app.api.v1.refrigerators_api import router as refrigerators_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Backend de refrigerador inteligente con procesamiento de tickets en MinIO y lectura OCR modular",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(tickets_router, prefix="/api/v1")
app.include_router(foods_router, prefix="/api/v1")
app.include_router(refrigerators_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.app_name,
        "environment": settings.environment,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
