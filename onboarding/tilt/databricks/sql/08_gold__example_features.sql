-- Tilt Renewables onboarding - Gold: example feature scaffolding for ML
--
-- Output view:
--   {{catalog}}.{{schema}}.v_gold_features_1min
--
-- Notes:
-- - This is intentionally generic. It becomes powerful once you populate
--   silver_signal_mapping.signal_role for key signals.
-- - Typical roles you can standardize:
--     ACTIVE_POWER, WIND_SPEED, ROTOR_SPEED, VIBRATION, AMBIENT_TEMP,
--     SOC, CHARGE_POWER, DISCHARGE_POWER, CURTAILMENT_ACTIVE, AVAILABILITY
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.v_gold_features_1min AS
WITH a AS (
  SELECT * FROM {{catalog}}.{{schema}}.v_silver_signal_1min
),
wide AS (
  SELECT
    window_start,
    window_end,
    site,
    asset_type,
    asset_id,

    -- Common "wide" features (extend as you learn the customer's signals)
    MAX(CASE WHEN signal_role = 'ACTIVE_POWER' THEN avg_numeric END) AS active_power_kw_avg,
    MAX(CASE WHEN signal_role = 'WIND_SPEED' THEN avg_numeric END) AS wind_speed_ms_avg,
    MAX(CASE WHEN signal_role = 'SOC' THEN avg_numeric END) AS soc_pct_avg,

    -- Data quality / coverage
    SUM(event_count) AS events_1min,
    AVG(good_ratio) AS avg_good_ratio
  FROM a
  GROUP BY window_start, window_end, site, asset_type, asset_id
)
SELECT
  *,
  -- Simple lag features (example)
  lag(active_power_kw_avg, 1) OVER (PARTITION BY site, asset_type, asset_id ORDER BY window_start) AS active_power_kw_avg_lag_1,
  lag(active_power_kw_avg, 5) OVER (PARTITION BY site, asset_type, asset_id ORDER BY window_start) AS active_power_kw_avg_lag_5
FROM wide;


