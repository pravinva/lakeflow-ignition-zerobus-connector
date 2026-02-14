import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import query as query_service

router = APIRouter(prefix="/api/compression")


def _wrap(data: object, start: float) -> dict:
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }


class SdtConfigUpdate(BaseModel):
    tag_pattern: str
    comp_dev: float | None = None
    comp_dev_percent: float | None = Field(default=None, ge=0.1, le=5.0)
    comp_max_seconds: int | None = Field(default=None, ge=60, le=3600)
    comp_min_seconds: int | None = None


@router.get("/comparison")
async def compression_comparison() -> dict:
    start = time.monotonic()
    data = await query_service.execute("compressionComparison")
    return _wrap(data, start)


@router.get("/sdt-config")
async def get_sdt_config() -> dict:
    start = time.monotonic()
    data = await query_service.execute("sdtConfig")
    return _wrap(data, start)


@router.put("/sdt-config")
async def update_sdt_config(body: SdtConfigUpdate) -> dict:
    start = time.monotonic()
    await query_service.execute(
        "sdtConfigUpdate",
        tag_pattern=body.tag_pattern,
        comp_dev=body.comp_dev,
        comp_dev_percent=body.comp_dev_percent,
        comp_max_seconds=body.comp_max_seconds or 600,
        comp_min_seconds=body.comp_min_seconds or 0,
    )
    data = await query_service.execute("sdtConfig")
    return _wrap(data, start)
