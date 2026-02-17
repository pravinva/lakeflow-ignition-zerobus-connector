import time
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..services import query as query_service

router = APIRouter(prefix="/api/events")


@router.get("/latest")
async def events_latest(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    start = time.monotonic()
    data = await query_service.execute("eventsLatest", limit=limit)
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }
