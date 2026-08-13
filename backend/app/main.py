import os
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.patient_routes import router as patient_router
from app.api.routes import router
from app.core.auth import ReverificationRequired
from app.core.config import Settings, get_settings
from app.mcp.insurance_registry import router as mcp_registry_router
from app.mcp.operations import router as mcp_operations_router

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


@app.exception_handler(ReverificationRequired)
def reverification_required_handler(
    _request: Request,
    exc: ReverificationRequired,
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "clerk_error": {
                "type": "forbidden",
                "reason": "reverification-error",
                "metadata": {"reverification": exc.configuration},
            }
        },
    )


@app.get("/healthz")
def healthcheck(current_settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    return {
        "status": "ok",
        "environment": current_settings.environment,
        "demo_mode": current_settings.demo_mode,
        "providers": {
            "database": (
                "supabase"
                if current_settings.use_supabase_persistence
                else ("unconfigured" if current_settings.persistence_mode == "supabase" else "synthetic")
            ),
            "authentication": (
                "demo"
                if current_settings.demo_mode
                else ("clerk" if current_settings.clerk_configured else "unconfigured")
            ),
            "openai": "configured" if current_settings.openai_configured else "unconfigured",
        },
        "provider_configuration": {
            "supabase": current_settings.supabase_configured,
            "clerk": current_settings.clerk_configured,
            "openai": current_settings.openai_configured,
            "persistence_mode": current_settings.persistence_mode,
        },
        "deployment": {
            "commit_sha": os.getenv("RAILWAY_GIT_COMMIT_SHA", "local"),
            "service": os.getenv("RAILWAY_SERVICE_NAME", "local"),
        },
    }


app.include_router(router, prefix=settings.api_prefix)
app.include_router(patient_router, prefix=settings.api_prefix)
app.include_router(mcp_operations_router)
app.include_router(mcp_registry_router)
