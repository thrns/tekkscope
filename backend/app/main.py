import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import search, lens, deeplens, reportlens, api_keys, tek, nlts
from app.config.settings import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO if settings.deployment_mode == "production" else logging.DEBUG)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to every response for support and log correlation."""

    async def dispatch(self, request: Request, call_next):
        import uuid

        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(
    title="Tekkscope API",
    version="0.1.0",
    description="Source-backed AI research, search, streaming, and report generation.",
)
app.add_middleware(RequestIdMiddleware)

# Add CORS middleware - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "x-api-key", "x-request-id"],
    expose_headers=["X-Request-ID"],
)

app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(lens.router, prefix="/lens", tags=["Lens"])
app.include_router(deeplens.router, prefix="/deeplens", tags=["DeepLens"])
app.include_router(reportlens.router, prefix="/reportlens", tags=["ReportLens"])
app.include_router(nlts.router, prefix="/nlts", tags=["NLTS"])

app.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])

app.include_router(tek.router, tags=["Tek"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Tekkscope API"}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Return service readiness without making health checks expensive."""

    checks = {"configuration": "ok"}
    if settings.tekk_redis_readiness_required:
        from app.streaming import manager

        if await manager.redis_available():
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable"
            return JSONResponse(status_code=503, content={"ready": False, "checks": checks})
    else:
        checks["redis"] = "optional"

    return {"ready": True, "checks": checks}
