import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR.parent / "storage"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )

    PROJECT_NAME: str = "AI-Generated & Manipulated Media Detection System"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR}/forensics.db"
    )
    
    # Storage paths
    STORAGE_PATH: str = str(STORAGE_DIR)
    UPLOADS_PATH: str = str(STORAGE_DIR / "uploads")
    FRAMES_PATH: str = str(STORAGE_DIR / "frames")
    HEATMAPS_PATH: str = str(STORAGE_DIR / "heatmaps")
    REPORTS_PATH: str = str(STORAGE_DIR / "reports")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production-64bytes-min"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # Detection Thresholds
    THRESHOLD_LOW_EVIDENCE: float = 0.30
    THRESHOLD_INCONCLUSIVE: float = 0.60
    THRESHOLD_SUSPICIOUS: float = 0.80

settings = Settings()
