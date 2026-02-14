import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from ..services import query as query_service

router = APIRouter(prefix="/api/assets")


def _wrap(data: object, start: float) -> dict:
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }


@router.get("")
async def list_assets() -> dict:
    start = time.monotonic()
    data = await query_service.execute("assets")
    return _wrap(data, start)


@router.get("/{asset_id}")
async def get_asset(asset_id: str) -> dict:
    start = time.monotonic()
    data = await query_service.execute("assetById", asset_id=asset_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")
    return _wrap(data[0], start)


@router.get("/{asset_id}/tags")
async def get_asset_tags(
    asset_id: str,
    tags: str | None = Query(default=None),
    range: int = Query(default=5, alias="range"),
) -> dict:
    start = time.monotonic()
    tag_list = tags.split(",") if tags else None
    data = await query_service.execute(
        "assetTags", asset_id=asset_id, tags=tag_list, range_minutes=range
    )
    return _wrap(data, start)
