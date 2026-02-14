import time
from typing import Literal

from fastapi import APIRouter, Query

from ..services import query as query_service

router = APIRouter(prefix="/api/metrics")

MetricsSource = Literal["raw_tags", "raw_throughput"]


def _wrap(data: object, start: float, source: str | None = None) -> dict:
    from datetime import datetime, timezone

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_time_ms": round((time.monotonic() - start) * 1000),
    }
    if source:
        meta["source"] = source
    return {"data": data, "meta": meta}


@router.get("/throughput")
async def throughput(
    source: MetricsSource = Query("raw_tags", description="raw_tags (landing) or raw_throughput (deduped)"),
) -> dict:
    start = time.monotonic()
    data = await query_service.execute("throughput", minutes=5, source=source)
    return _wrap(data, start, source)


@router.get("/latency")
async def latency(
    source: MetricsSource = Query("raw_tags", description="raw_tags (landing) or raw_throughput (deduped)"),
) -> dict:
    start = time.monotonic()
    connector = await query_service.execute("latency", minutes=5, source=source)
    # Merge E2E latency from raw_throughput (CDF _commit_timestamp) when available
    try:
        e2e = await query_service.execute("latencyE2e", minutes=5)
        by_window = {r["window_start"]: r for r in connector}
        for r in e2e:
            key = r["window_start"]
            if key in by_window:
                by_window[key]["avg_e2e_latency_ms"] = r.get("avg_e2e_latency_ms")
                by_window[key]["p99_e2e_latency_ms"] = r.get("p99_e2e_latency_ms")
        data = list(by_window.values())
        data.sort(key=lambda x: x["window_start"])
    except Exception:
        data = connector
    return _wrap(data, start, source)


@router.get("/compression")
async def compression() -> dict:
    start = time.monotonic()
    data = await query_service.execute("compression")
    return _wrap(data, start)
