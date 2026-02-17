import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/config")

VALID_SCENARIOS = ("wind", "battery", "mixed")
_current_scenario: str = "mixed"


def _wrap(data: object, start: float) -> dict:
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_time_ms": round((time.monotonic() - start) * 1000),
        },
    }


class ScenarioBody(BaseModel):
    scenario: str


@router.get("/scenario")
async def get_scenario() -> dict:
    start = time.monotonic()
    return _wrap({"scenario": _current_scenario}, start)


@router.post("/scenario")
async def set_scenario(body: ScenarioBody) -> dict:
    global _current_scenario  # noqa: PLW0603
    start = time.monotonic()
    if body.scenario not in VALID_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Must be one of: {', '.join(VALID_SCENARIOS)}",
        )
    _current_scenario = body.scenario
    return _wrap({"scenario": _current_scenario}, start)
