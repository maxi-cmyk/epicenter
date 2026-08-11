from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Synthetic P0 API for Epicenter administrative readiness.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "demo_mode": settings.demo_mode,
        "providers": {
            "database": "supabase" if settings.supabase_configured else "synthetic",
            "authentication": "clerk" if settings.clerk_configured else "demo",
        },
    }


app.include_router(router, prefix=settings.api_prefix)
