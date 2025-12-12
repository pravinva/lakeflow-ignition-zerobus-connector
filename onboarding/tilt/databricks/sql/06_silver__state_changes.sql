-- Tilt Renewables onboarding - Silver: state change events (derived events)
--
-- Output view:
--   {{catalog}}.{{schema}}.v_silver_state_changes
--
-- Use:
--   Useful for alarms, running/stopped, curtailment active, breaker status, etc.
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.v_silver_state_changes AS
WITH e AS (
  SELECT
    event_time,
    source_system,
    site,
    asset_type,
    asset_id,
    signal_name,
    signal_role,
    value_string
  FROM {{catalog}}.{{schema}}.v_silver_events
  WHERE signal_name IS NOT NULL
),
w AS (
  SELECT
    *,
    lag(value_string) OVER (
      PARTITION BY source_system, site, asset_type, asset_id, signal_name
      ORDER BY event_time
    ) AS prev_value
  FROM e
)
SELECT
  event_time,
  source_system,
  site,
  asset_type,
  asset_id,
  signal_name,
  signal_role,
  prev_value,
  value_string AS new_value
FROM w
WHERE prev_value IS NOT NULL AND prev_value <> value_string;


