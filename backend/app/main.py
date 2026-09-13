"""
Onion Quality AI — FastAPI application entrypoint.

Run (from backend/):
    uvicorn app.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs        (Swagger UI)
    http://localhost:8000/redoc
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import analysis, auth, batches, health, reports
from app.config import settings
from app.db.database import SessionLocal, init_db
from app.services.auth import ensure_demo_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (safe on an empty DB) + seed the DEMO login.
    init_db()
    if settings.seed_demo_user:
        db = SessionLocal()
        try:
            ensure_demo_user(db)
        except Exception as exc:  # noqa: BLE001 — never block startup on seeding
            print(f"[startup] WARN: could not seed demo user: {exc}")
        finally:
            db.close()
    yield
    # Shutdown: nothing to clean up yet.


app = FastAPI(
    title="Onion Quality AI — Backend",
    version=settings.version,
    description=(
        "AI-based Onion Quality Assessment and Grading System "
        f"(Smart India Hackathon 2026 — PS {26031}).\n\n"
        "**DEMO MODE is ON by default**: `/api/analyze` returns deterministic "
        "synthetic results flagged `is_demo: true`. They are NOT real AI output."
    ),
    lifespan=lifespan,
)

# --- CORS (mobile dev on device/simulator + web) ----------------------------
_origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ----------------------------------------------------------------
prefix = settings.api_prefix
app.include_router(health.router, prefix=prefix)
app.include_router(auth.router, prefix=prefix)
app.include_router(batches.router, prefix=prefix)
app.include_router(analysis.router, prefix=prefix)
app.include_router(reports.router, prefix=prefix)

# Uploaded images are servable for previews (read-only).
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


# --- Uniform error envelope: {"error": {code, message, details}} -------------
@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        code, message = detail.get("code", "ERROR"), detail.get("message", "Request failed.")
        details = detail.get("details")
    else:
        code, message, details = "ERROR", str(detail or "Request failed."), None
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={"error": {"code": code, "message": message, "details": details}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload failed validation.",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Never leak internals to clients; log server-side instead.
    print(f"[error] Unhandled exception on {request.method} {request.url.path}: {exc!r}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Unexpected server error. The incident was logged.",
                "details": None,
            }
        },
    )


# --- Serve Web Frontend (Expo Web Export) -----------------------------------
from pathlib import Path
from fastapi.responses import FileResponse

dist_dir = Path(__file__).resolve().parents[2] / "mobile" / "dist"
if dist_dir.exists():
    if (dist_dir / "_expo").exists():
        app.mount("/_expo", StaticFiles(directory=str(dist_dir / "_expo")), name="expo")
    if (dist_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

    NO_CACHE_HEADERS = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(dist_dir / "index.html", headers=NO_CACHE_HEADERS)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        if (
            full_path.startswith("api")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi.json")
            or full_path.startswith("uploads")
        ):
            raise StarletteHTTPException(status_code=404, detail="Not Found")
        target_file = dist_dir / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_dir / "index.html", headers=NO_CACHE_HEADERS)
else:
    @app.get("/", tags=["meta"], summary="Service banner")
    def root() -> dict:
        return {
            "service": settings.app_name,
            "version": settings.version,
            "demo_mode": settings.demo_mode,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
            "notice": "DEMO MODE returns synthetic data flagged is_demo=true." if settings.demo_mode else None,
        }

