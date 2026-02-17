"""Tests for app/config.py - environment config loading and auth validation."""

import os

import pytest

from backend.config import load_config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure a clean environment for each test."""
    for key in (
        "DATABRICKS_HOST",
        "DATABRICKS_HTTP_PATH",
        "DATABRICKS_TOKEN",
        "DATABRICKS_CLIENT_ID",
        "DATABRICKS_CLIENT_SECRET",
        "DATABRICKS_WAREHOUSE_ID",
        "DATABRICKS_CATALOG",
        "DATABRICKS_SCHEMA",
    ):
        monkeypatch.delenv(key, raising=False)


def test_missing_host_raises(monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    with pytest.raises(ValueError, match="DATABRICKS_HOST"):
        load_config()


def test_defaults_for_catalog_and_schema(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    cfg = load_config()
    assert cfg.catalog == "agl_demo"
    assert cfg.schema == "ot"


def test_accepts_client_id_and_secret(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "cid")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "csec")
    cfg = load_config()
    assert cfg.client_id == "cid"
    assert cfg.client_secret == "csec"
    assert cfg.token == ""


def test_accepts_token_as_fallback(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    cfg = load_config()
    assert cfg.token == "tok"
    assert cfg.client_id == ""


def test_rejects_missing_auth(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    with pytest.raises(ValueError, match="authentication"):
        load_config()


def test_reads_warehouse_id(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/abc")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "wh-123")
    cfg = load_config()
    assert cfg.warehouse_id == "wh-123"
