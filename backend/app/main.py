from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.patient_routes import router as patient_router
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
    allow_origins=settings.frontend_origin_list,
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
            "database": (
                "synthetic" if settings.demo_mode else ("supabase" if settings.supabase_configured else "unconfigured")
            ),
            "authentication": (
                "demo" if settings.demo_mode else ("clerk" if settings.clerk_configured else "unconfigured")
            ),
        },
        "provider_configuration": {
            "supabase": settings.supabase_configured,
            "clerk": settings.clerk_configured,
        },
    }


app.include_router(router, prefix=settings.api_prefix)
app.include_router(patient_router, prefix=settings.api_prefix)
