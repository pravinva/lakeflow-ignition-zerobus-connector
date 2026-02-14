"""Tests for the query builder - validates SQL generation without Databricks."""

import pytest

from backend.services.query import build_query


def test_throughput_query():
    sql, params = build_query("throughput", minutes=10)
    assert "ingest_metrics" in sql
    assert params == [10]


def test_latency_query():
    sql, params = build_query("latency", minutes=5)
    assert "avg_latency_ms" in sql
    assert params == [5]


def test_events_latest_query():
    sql, params = build_query("eventsLatest", limit=20)
    assert "raw_tags" in sql
    assert "LIMIT" in sql
    assert params == [20]


def test_assets_query():
    sql, params = build_query("assets")
    assert "assets" in sql
    assert "raw_tags" in sql


def test_asset_by_id_query():
    sql, params = build_query("assetById", asset_id="wind_01")
    assert params == ["wind_01"]


def test_asset_tags_with_filter():
    sql, params = build_query(
        "assetTags", asset_id="wind_01", tags=["temp", "speed"], range_minutes=15
    )
    assert "tag_name IN" in sql
    assert params == ["wind_01", 15, "temp", "speed"]


def test_compression_comparison_query():
    sql, params = build_query("compressionComparison")
    assert "SUM(records_raw)" in sql


def test_sdt_config_query():
    sql, _params = build_query("sdtConfig")
    assert "sdt_config" in sql


def test_sdt_config_update_query():
    sql, params = build_query(
        "sdtConfigUpdate", tag_pattern="*", comp_dev_percent=1.5, comp_max_seconds=600
    )
    assert "MERGE INTO" in sql and "sdt_config" in sql
    assert params[0] == "*"


def test_unknown_query_raises():
    with pytest.raises(ValueError, match="Unknown query"):
        build_query("nonexistent")
