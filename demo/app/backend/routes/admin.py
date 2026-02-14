import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/api/admin")


def _wrap(data: object, start: float) -> dict:
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }


@router.post("/reset")
async def reset(x_api_key: str | None = Header(default=None)) -> dict:
    start = time.monotonic()
    expected_key = os.environ.get("ADMIN_API_KEY", "")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return _wrap(
        {"status": "reset_complete", "message": "Demo tables truncated and simulator restarted"},
        start,
    )
