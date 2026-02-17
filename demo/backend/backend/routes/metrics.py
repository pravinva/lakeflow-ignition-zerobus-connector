import time

from fastapi import APIRouter

from ..services import query as query_service

router = APIRouter(prefix="/api/metrics")


def _wrap(data: object, start: float) -> dict:
    from datetime import datetime, timezone

    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }


@router.get("/throughput")
async def throughput() -> dict:
    start = time.monotonic()
    data = await query_service.execute("throughput", minutes=5)
    return _wrap(data, start)


@router.get("/latency")
async def latency() -> dict:
    start = time.monotonic()
    data = await query_service.execute("latency", minutes=5)
    return _wrap(data, start)


@router.get("/compression")
async def compression() -> dict:
    start = time.monotonic()
    data = await query_service.execute("compression")
    return _wrap(data, start)
