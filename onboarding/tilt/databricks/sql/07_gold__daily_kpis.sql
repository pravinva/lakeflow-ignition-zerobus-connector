-- Tilt Renewables onboarding - Gold: example daily KPIs (template)
--
-- Output table:
--   {{catalog}}.{{schema}}.gold_daily_asset_kpis
--
-- IMPORTANT:
-- These are *templates*. Real KPI definitions vary by customer.
-- This shows an architecturally sound pattern:
--   Bronze (fixed) -> Silver (normalized) -> Gold (business KPIs)
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.gold_daily_asset_kpis (
  kpi_date DATE,
  site STRING,
  asset_type STRING,
  asset_id STRING,

  -- Data health
  signals_observed BIGINT,
  events BIGINT,
  good_ratio DOUBLE,

  -- Power KPI (optional, best-effort from signal_role = ACTIVE_POWER)
  avg_active_power_kw DOUBLE,
  max_active_power_kw DOUBLE,

  -- Last seen
  last_event_time TIMESTAMP
)
USING DELTA;

-- Recompute for recent days (safe template; tune window for your needs)
INSERT OVERWRITE {{catalog}}.{{schema}}.gold_daily_asset_kpis
SELECT
  DATE(event_time) AS kpi_date,
  site,
  asset_type,
  asset_id,

  COUNT(DISTINCT signal_name) AS signals_observed,
  COUNT(*) AS events,
  SUM(CASE WHEN quality_code = 192 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS good_ratio,

  AVG(CASE WHEN signal_role = 'ACTIVE_POWER' THEN numeric_value END) AS avg_active_power_kw,
  MAX(CASE WHEN signal_role = 'ACTIVE_POWER' THEN numeric_value END) AS max_active_power_kw,

  MAX(event_time) AS last_event_time
FROM {{catalog}}.{{schema}}.v_silver_events
GROUP BY DATE(event_time), site, asset_type, asset_id;


