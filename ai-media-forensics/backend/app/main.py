import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import engine, Base, check_db_connection
from app.models.schemas import HealthCheckResponse
from app.api.routes_detection import router as detection_router
from app.api.routes_provenance import router as provenance_router
from app.api.routes_media import router as media_router
from app.api.routes_reports import router as reports_router
from app.api.routes_auth import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("ai_forensics")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI-Generated & Manipulated Media Detection System...")
    # Create DB tables if they do not exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas verified/created.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    yield
    logger.info("Shutting down AI Forensics Engine.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Multi-pipeline AI forensics platform for detecting AI-generated and manipulated media.",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(detection_router, prefix=settings.API_V1_STR)
app.include_router(provenance_router, prefix=settings.API_V1_STR)
app.include_router(media_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/health", response_model=HealthCheckResponse, tags=["Health"])
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """System and database connectivity health check."""
    db_status = check_db_connection()
    return HealthCheckResponse(
        status="ok",
        version=settings.PROJECT_VERSION,
        database=db_status
    )

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
