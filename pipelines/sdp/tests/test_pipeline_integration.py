"""Pipeline integration tests - verify contact points work together.

Tests the data flow: Zerobus → Bronze → Silver → Analytics → App queries
"""

from pathlib import Path

import pytest


def _read_file(relative_path: str) -> str:
    """Read a file relative to repo root."""
    repo_root = Path(__file__).parent.parent.parent.parent
    return (repo_root / relative_path).read_text()


class TestBronzeSilverTransform:
    """Test bronze_silver.py transformation."""

    def test_uses_correct_column_names(self):
        """Verify bronze_silver reads correct PRD column names."""
        source = _read_file("pipelines/sdp/transformations/bronze_silver.py")

        # Should use PRD schema column names
        assert "event_timestamp" in source, "Should read event_timestamp (not source_timestamp)"
        assert "tag_value" in source, "Should read tag_value (not value)"
        assert "sdt_compressed" in source, "Should read sdt_compressed (not is_compressed)"

        # Should NOT use old column names
        assert "source_timestamp" not in source, "Should not use source_timestamp"

    def test_outputs_correct_columns(self):
        """Verify bronze_silver outputs aggregated_tags schema (streaming table columns)."""
        source = _read_file("pipelines/sdp/transformations/bronze_silver.py")

        # aggregated_tags streaming table outputs (asset_id comes from enriched_tags via mapping)
        required_outputs = [
            "window_start",
            "window_end",
            "tag_name",
            "source_system",
            "tag_provider",
            "avg_value",
            "min_value",
            "max_value",
            "stddev_value",
            "sample_count",
        ]
        for col in required_outputs:
            assert col in source, f"Should output {col}"


class TestHealthScoring:
    """Test health scoring module."""

    def test_battery_key_tags_match_agl_signals(self):
        """Verify BATTERY_KEY_TAGS match AGL signal mapping."""
        from agl_analytics.health import BATTERY_KEY_TAGS

        # These should match signal_name in silver_signal_mapping
        assert "soc_pct" in BATTERY_KEY_TAGS, "Should include soc_pct"
        assert "max_rack_temp_c" in BATTERY_KEY_TAGS, "Should include max_rack_temp_c"

    def test_compute_zscore_handles_zero_stddev(self):
        """Verify z-score computation handles edge cases."""
        from agl_analytics.health import compute_zscore

        # Zero stddev should return 0, not divide by zero
        result = compute_zscore(value=100.0, mean=50.0, stddev=0.0)
        assert result == 0.0

    def test_health_score_range(self):
        """Verify health score stays in [0, 1] range."""
        from agl_analytics.health import compute_health_score

        # All anomalous → 0.0
        assert compute_health_score(anomalous_count=4, total_tag_count=4) == 0.0

        # None anomalous → 1.0
        assert compute_health_score(anomalous_count=0, total_tag_count=4) == 1.0

        # Half anomalous → 0.5
        assert compute_health_score(anomalous_count=2, total_tag_count=4) == 0.5

        # Empty tags → 1.0 (healthy by default)
        assert compute_health_score(anomalous_count=0, total_tag_count=0) == 1.0


class TestMarketData:
    """Test market data module."""

    def test_price_generator_outputs_correct_schema(self):
        """Verify price generator outputs expected fields."""
        from agl_analytics.market import generate_historical_prices

        prices = generate_historical_prices(days=1, region="NSW1")

        assert len(prices) > 0, "Should generate prices"
        record = prices[0]
        assert "interval_start" in record
        assert "interval_end" in record
        assert "region" in record
        assert "price_aud_mwh" in record
        assert "demand_mw" in record

    def test_forecast_generator_includes_spikes(self):
        """Verify forecast includes high-price events for demo urgency."""
        from agl_analytics.market import generate_price_forecast

        forecast = generate_price_forecast(hours=48, region="NSW1")

        # Should have at least one spike > $300/MWh for demo
        prices = [r["forecast_price_aud_mwh"] for r in forecast]
        has_spike = any(p > 300 for p in prices)
        assert has_spike, "Forecast should include at least one price spike for demo urgency"


class TestAppQueries:
    """Test app backend queries match table schemas."""

    def test_analytics_queries_exist(self):
        """Verify analytics queries are registered in query.py."""
        source = _read_file("demo/app/backend/services/query.py")

        required_queries = [
            "healthScores",
            "revenueRisk",
            "nemPrices",
            "priceForecast",
            "revenueSummary",
        ]
        for q in required_queries:
            assert f'"{q}"' in source, f"Missing query builder: {q}"

    def test_health_scores_query_schema(self):
        """Verify healthScores query matches table schema."""
        source = _read_file("demo/app/backend/services/query.py")

        # Should query required columns from APP-PRD
        required_cols = ["scored_at", "asset_id", "health_score", "primary_risk_tag"]
        for col in required_cols:
            assert col in source, f"Missing column {col} in healthScores query"

    def test_revenue_risk_query_schema(self):
        """Verify revenueRisk query matches table schema."""
        source = _read_file("demo/app/backend/services/query.py")

        # Should query required columns from APP-PRD
        required_cols = [
            "revenue_at_risk_aud",
            "trip_probability",
            "recommended_action",
        ]
        for col in required_cols:
            assert col in source, f"Missing column {col} in revenueRisk query"


class TestAnalyticsRoutes:
    """Test analytics API routes exist."""

    def test_analytics_router_exists(self):
        """Verify analytics.py route file exists."""
        source = _read_file("demo/app/backend/routes/analytics.py")
        assert "APIRouter" in source
        assert "/api/analytics" in source

    def test_analytics_router_registered(self):
        """Verify analytics router is registered in main.py."""
        source = _read_file("demo/app/backend/main.py")
        assert "analytics" in source
        assert "app.include_router(analytics.router)" in source


class TestEndToEndPipeline:
    """Integration tests for complete pipeline flow."""

    def test_schema_alignment_bronze_to_analytics(self):
        """Verify column names align across pipeline stages."""
        source = _read_file("pipelines/sdp/transformations/bronze_silver.py")

        # Check bronze_silver reads valid bronze columns (PRD schema)
        for col in ["event_timestamp", "asset_id", "tag_name", "tag_value", "sdt_compressed"]:
            assert col in source, f"bronze_silver should read {col}"

    def test_key_tags_align_with_signal_mapping(self):
        """Verify key tags match signal mapping definitions."""
        from agl_analytics.health import BATTERY_KEY_TAGS

        # Signal mappings from 11_seed_tomago_site01_mapping.sql
        agl_signal_names = {
            "soc_pct",
            "soh_pct",
            "energy_available_mwh",
            "bess_active_power_mw",
            "derate_active",
            "ambient_temp_c",
            "max_rack_temp_c",
            "alarm_count",
        }

        # At least some key tags should match signal names
        matched = set(BATTERY_KEY_TAGS) & agl_signal_names
        assert len(matched) >= 2, f"Key tags should match signal mapping. Matched: {matched}"

    def test_silver_analytics_reads_from_enriched_tags(self):
        """Verify silver_analytics reads from enriched_tags (MV built from aggregated_tags)."""
        source = _read_file("pipelines/sdp/transformations/silver_analytics.py")
        assert "enriched_tags" in source, "silver_analytics should read from enriched_tags"

    def test_enriched_tags_derives_sim_tag_path(self):
        """With empty silver_signal_mapping, enriched_tags derives asset_id/signal_name from [sim] tag_path."""
        source = _read_file("pipelines/sdp/transformations/bronze_silver.py")
        assert "[sim]" in source or '"[sim]"' in source or "'[sim]'" in source, (
            "enriched_tags should parse simulator tag_path [sim]asset_id/rest"
        )
        assert "derived_asset_id" in source or "_derived_asset_id" in source, (
            "enriched_tags should derive asset_id when mapping is missing"
        )
        assert "derived_signal_name" in source or "_derived_signal_name" in source, (
            "enriched_tags should derive signal_name when mapping is missing"
        )

    def test_health_scores_left_join_and_infers_asset_type(self):
        """health_scores uses left join to silver_asset_registry and infers asset_type when registry is empty."""
        source = _read_file("pipelines/sdp/transformations/silver_analytics.py")
        assert "left" in source and "how=" in source, (
            "health_scores should left join to silver_asset_registry"
        )
        assert "coalesce" in source.lower(), (
            "health_scores should coalesce asset_type (infer when null)"
        )
        assert "wind_" in source or "wind_turbine" in source, (
            "health_scores should infer asset_type from asset_id (e.g. wind_ -> wind_turbine)"
        )

    def test_battery_key_tags_include_simulator_path_names(self):
        """BATTERY_KEY_TAGS include simulator path-style names so derived signal_name matches."""
        from agl_analytics.health import BATTERY_KEY_TAGS

        assert "battery/soc_pct" in BATTERY_KEY_TAGS, (
            "BATTERY_KEY_TAGS should include simulator path-style battery/soc_pct"
        )
        assert "battery/temperature_c" in BATTERY_KEY_TAGS, (
            "BATTERY_KEY_TAGS should include simulator path-style battery/temperature_c"
        )

    def test_revenue_risk_joins_health_and_forecast(self):
        """Verify revenue_risk joins health_scores with price_forecast."""
        source = _read_file("pipelines/sdp/transformations/revenue_risk.py")
        assert "health_scores" in source, "revenue_risk should read health_scores"
        assert "price_forecast" in source, "revenue_risk should read price_forecast"
