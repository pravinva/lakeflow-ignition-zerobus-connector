"""Tests for API routes - metrics, events, assets, compression, config, admin."""

import os
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.anyio
async def test_metrics_throughput(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[{"x": 1}]):
        resp = await client.get("/api/metrics/throughput")
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    assert "query_time_ms" in body["meta"]


@pytest.mark.anyio
async def test_metrics_latency(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/metrics/latency")
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.anyio
async def test_metrics_compression(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/metrics/compression")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_events_latest(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[{"ev": 1}]):
        resp = await client.get("/api/events/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == [{"ev": 1}]


@pytest.mark.anyio
async def test_events_limit_capped(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]) as mock_exec:
        resp = await client.get("/api/events/latest?limit=300")
    # FastAPI Query(le=200) should reject > 200
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_assets_list(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[{"id": "a1"}]):
        resp = await client.get("/api/assets")
    assert resp.status_code == 200
    assert resp.json()["data"] == [{"id": "a1"}]


@pytest.mark.anyio
async def test_asset_by_id(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[{"id": "wind_01"}]):
        resp = await client.get("/api/assets/wind_01")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "wind_01"


@pytest.mark.anyio
async def test_asset_not_found(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/assets/no_such")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_asset_tags(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[{"t": 1}]):
        resp = await client.get("/api/assets/wind_01/tags?range=15")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_compression_comparison(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/compression/comparison")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_sdt_config_get(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.get("/api/compression/sdt-config")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_sdt_config_update(client):
    with patch("backend.services.query.execute", new_callable=AsyncMock, return_value=[]):
        resp = await client.put(
            "/api/compression/sdt-config",
            json={"tag_pattern": "*", "comp_dev_percent": 2.0, "comp_max_seconds": 300},
        )
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_sdt_config_validation_rejects_bad_comp_dev(client):
    resp = await client.put(
        "/api/compression/sdt-config",
        json={"tag_pattern": "*", "comp_dev_percent": 10.0},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_scenario_get(client):
    resp = await client.get("/api/config/scenario")
    assert resp.status_code == 200
    assert resp.json()["data"]["scenario"] == "mixed"


@pytest.mark.anyio
async def test_scenario_switch(client):
    resp = await client.post("/api/config/scenario", json={"scenario": "wind"})
    assert resp.status_code == 200
    assert resp.json()["data"]["scenario"] == "wind"


@pytest.mark.anyio
async def test_scenario_invalid(client):
    resp = await client.post("/api/config/scenario", json={"scenario": "bad"})
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_admin_reset_requires_api_key(client):
    resp = await client.post("/api/admin/reset")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_admin_reset_with_valid_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    resp = await client.post("/api/admin/reset", headers={"x-api-key": "secret123"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "reset_complete"
