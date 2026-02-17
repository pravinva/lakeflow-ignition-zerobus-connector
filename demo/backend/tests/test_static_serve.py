"""Tests for static file serving and SPA fallback in production mode."""

import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import create_app


@pytest.fixture
def static_dir():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "index.html").write_text("<!DOCTYPE html><html><body>SPA Root</body></html>")
        assets_dir = p / "assets"
        assets_dir.mkdir()
        (assets_dir / "main.js").write_text('console.log("hello");')
        (assets_dir / "style.css").write_text("body { color: white; }")
        yield str(p)


@pytest.fixture
async def prod_client(static_dir):
    app = create_app(static_dir=static_dir)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_root_returns_html(prod_client):
    resp = await prod_client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "SPA Root" in resp.text


@pytest.mark.anyio
async def test_api_health_still_json(prod_client):
    resp = await prod_client.get("/api/health")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_spa_fallback_returns_html(prod_client):
    resp = await prod_client.get("/some/client/route")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "SPA Root" in resp.text


@pytest.mark.anyio
async def test_api_routes_take_precedence(prod_client):
    resp = await prod_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
