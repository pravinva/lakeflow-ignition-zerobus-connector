-- Tilt Renewables onboarding - Silver: 1-minute aggregates (fleet rollups)
--
-- Output view:
--   {{catalog}}.{{schema}}.v_silver_signal_1min
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.v_silver_signal_1min AS
SELECT
  window.start AS window_start,
  window.end AS window_end,
  source_system,
  site,
  asset_type,
  asset_id,
  signal_name,
  signal_role,

  COUNT(*) AS event_count,
  SUM(CASE WHEN quality_code = 192 THEN 1 ELSE 0 END) AS good_count,
  (SUM(CASE WHEN quality_code = 192 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) AS good_ratio,

  AVG(numeric_value) AS avg_numeric,
  MIN(numeric_value) AS min_numeric,
  MAX(numeric_value) AS max_numeric,

  max_by(value_string, event_time) AS last_value_string,
  max(event_time) AS last_event_time
FROM {{catalog}}.{{schema}}.v_silver_events
GROUP BY
  window(event_time, '1 minute'),
  source_system, site, asset_type, asset_id, signal_name, signal_role;


