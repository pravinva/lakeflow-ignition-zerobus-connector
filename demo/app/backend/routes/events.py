import time
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..services import query as query_service
from ..services.query import QueryError

router = APIRouter(prefix="/api/events")


@router.get("/latest")
async def events_latest(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    start = time.monotonic()
    error: str | None = None
    try:
        data = await query_service.execute("eventsLatest", limit=limit)
    except QueryError as exc:
        data = []
        error = exc.message

    meta: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_time_ms": round((time.monotonic() - start) * 1000),
    }
    if error:
        meta["error"] = error
    return {"data": data, "meta": meta}
