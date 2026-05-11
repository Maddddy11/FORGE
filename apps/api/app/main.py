from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.analytics import router as analytics_router
from app.routers.assets import router as assets_router
from app.routers.incidents import router as incidents_router
from app.routers.ingestion import router as ingestion_router
from app.routers.recommendations import router as recommendations_router

app = FastAPI(title="IMAM Lite API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(ingestion_router)
app.include_router(assets_router)
app.include_router(incidents_router)
app.include_router(recommendations_router)
app.include_router(analytics_router)
