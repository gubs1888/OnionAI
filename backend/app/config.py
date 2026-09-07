"""
Central backend configuration (12-factor style).

All values can be overridden via environment variables or a `.env` file
(see `.env.example` at the repository root).

TEAM B owns this file. Other teams should NOT need to edit it.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Path anchors ----------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[1]   # .../onion-quality-ai/backend
REPO_ROOT = BACKEND_ROOT.parent                      # .../onion-quality-ai


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=(".env", str(BACKEND_ROOT / ".env"), str(REPO_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App identity ---
    app_name: str = "onion-quality-ai"
    version: str = "0.1.0"
    debug: bool = False

    # --- DEMO MODE ---------------------------------------------------------
    # True  -> /api/analyze returns deterministic synthetic detections that are
    #          ALWAYS flagged `is_demo=true`. Lets all 4 teams work before the
    #          real YOLO model exists.  False -> a real model file is REQUIRED.
    demo_mode: bool = True

    # --- HTTP ---
    api_prefix: str = "/api"
    cors_origins: str = "*"          # comma-separated list, or "*"

    # --- Auth ---
    jwt_secret: str = "change-me-dev-secret-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    seed_demo_user: bool = True      # creates demo/demo123 on first start

    # --- Database ---
    # Default = SQLite so `pip install && uvicorn ...` works with zero setup.
    # docker-compose / production override this with PostgreSQL.
    database_url: str = f"sqlite:///{BACKEND_ROOT / 'onion_quality_dev.db'}"

    # --- ML inference ---
    model_path: str = str(REPO_ROOT / "ml" / "models" / "onion_yolo.pt")

    # --- Filesystem locations ---
    upload_dir: Path = BACKEND_ROOT / "uploads"    # uploaded batch images
    report_dir: Path = BACKEND_ROOT / "reports"    # generated PDF reports
    grading_config_path: Path = BACKEND_ROOT / "config" / "grading_config.json"


settings = Settings()

# Ensure runtime directories exist (idempotent).
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.report_dir.mkdir(parents=True, exist_ok=True)
