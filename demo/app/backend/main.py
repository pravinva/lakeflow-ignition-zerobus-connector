from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import AppConfig
from .routes import admin, analytics, asset_framework, assets, compression, config, events, health, metrics
from .services import query as query_service
from .services.query import QueryError

_logger = logging.getLogger(__name__)


def create_app(static_dir: str | None = None) -> FastAPI:
    app = FastAPI(title="AGL OT Lakehouse Demo")

    @app.on_event("startup")
    async def _log_startup() -> None:
        _logger.warning("AGL OT Lakehouse Demo app startup complete; serving requests.")

    # Initialise query service with configured catalog/schema so all SQL
    # uses fully-qualified table names from one source of truth.
    cfg = AppConfig()
    _logger.warning(
        "Query init: catalog=%s schema=%s (env DATABRICKS_CATALOG=%s DATABRICKS_SCHEMA=%s)",
        cfg.catalog,
        cfg.schema,
        os.environ.get("DATABRICKS_CATALOG", "<unset>"),
        os.environ.get("DATABRICKS_SCHEMA", "<unset>"),
    )
    query_service.init(cfg.catalog, cfg.schema)

    @app.exception_handler(QueryError)
    async def _handle_query_error(_request: Request, exc: QueryError) -> JSONResponse:
        """Return a structured JSON error when a SQL query fails, rather than 500."""
        _logger.warning("QueryError on %s: %s", exc.query_name, exc.message)
        return JSONResponse(
            status_code=502,
            content={
                "data": [],
                "meta": {"error": exc.message, "query": exc.query_name},
            },
        )

    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(events.router)
    app.include_router(assets.router)
    app.include_router(compression.router)
    app.include_router(config.router)
    app.include_router(admin.router)
    app.include_router(analytics.router)
    app.include_router(asset_framework.router)

    # In production, serve frontend static assets with SPA fallback
    resolved_static = static_dir or os.environ.get("STATIC_DIR")
    if resolved_static:
        static_path = Path(resolved_static).resolve()
        if static_path.is_dir():
            app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="static-assets")

            @app.get("/{full_path:path}")
            async def spa_fallback(request: Request, full_path: str) -> FileResponse:
                """SPA fallback: return index.html for non-API, non-asset routes."""
                file_path = static_path / full_path
                if file_path.is_file():
                    return FileResponse(file_path)
                return FileResponse(static_path / "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
