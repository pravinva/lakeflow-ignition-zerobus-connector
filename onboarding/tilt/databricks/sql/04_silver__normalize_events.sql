-- Tilt Renewables onboarding - Silver: normalize Bronze events into fleet telemetry (long format)
--
-- Output view:
--   {{catalog}}.{{schema}}.v_silver_events
--
-- Strategy:
--   1) Keep Bronze schema fixed (protobuf contract)
--   2) Normalize using silver_signal_mapping (customer editable)
--   3) Fallback to heuristic parsing (best effort) when unmapped
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE OR REPLACE VIEW {{catalog}}.{{schema}}.v_silver_events AS
WITH b AS (
  SELECT
    event_id,
    event_time,
    tag_path,
    tag_provider,
    numeric_value,
    string_value,
    boolean_value,
    quality,
    quality_code,
    source_system,
    ingestion_timestamp,
    data_type,
    alarm_state,
    alarm_priority,
    regexp_extract(tag_path, '\\\\](.*)', 1) AS path_no_provider,
    COALESCE(
      CAST(numeric_value AS STRING),
      string_value,
      CAST(boolean_value AS STRING)
    ) AS value_string
  FROM {{catalog}}.{{schema}}.ot_events_bronze
),
heur AS (
  SELECT
    *,
    split(path_no_provider, '/') AS parts
  FROM b
),
mapped AS (
  SELECT
    h.*,
    m.site AS map_site,
    m.asset_type AS map_asset_type,
    m.asset_id AS map_asset_id,
    m.signal_name AS map_signal_name,
    m.unit AS map_unit,
    m.signal_role AS map_signal_role
  FROM heur h
  LEFT JOIN {{catalog}}.{{schema}}.silver_signal_mapping m
    ON m.enabled = true
   AND (m.source_system IS NULL OR m.source_system = h.source_system)
   AND (
        (m.match_type = 'exact'  AND h.tag_path = m.match_value)
     OR (m.match_type = 'prefix' AND h.tag_path LIKE concat(m.match_value, '%'))
     OR (m.match_type = 'regex'  AND regexp_like(h.tag_path, m.match_value))
   )
),
coalesced AS (
  SELECT
    event_time,
    event_id,
    source_system,
    tag_path,
    tag_provider,
    quality,
    quality_code,
    data_type,
    ingestion_timestamp,
    alarm_state,
    alarm_priority,

    -- Normalized dimensions: mapping wins, else best-effort heuristic
    COALESCE(map_site,       CASE WHEN size(parts) >= 1 THEN parts[0] ELSE NULL END) AS site,
    COALESCE(map_asset_type, CASE WHEN size(parts) >= 2 THEN upper(parts[1]) ELSE 'OTHER' END) AS asset_type,
    COALESCE(map_asset_id,   CASE WHEN size(parts) >= 3 THEN parts[2] ELSE NULL END) AS asset_id,
    COALESCE(map_signal_name,CASE WHEN size(parts) >= 4 THEN parts[3] ELSE NULL END) AS signal_name,
    COALESCE(map_unit, NULL) AS unit,
    COALESCE(map_signal_role, NULL) AS signal_role,

    numeric_value,
    string_value,
    boolean_value,
    value_string
  FROM mapped
)
SELECT
  c.*,
  r.asset_name,
  r.capacity_kw,
  r.manufacturer,
  r.model,
  r.timezone,
  r.latitude,
  r.longitude,
  r.metadata AS asset_metadata
FROM coalesced c
LEFT JOIN {{catalog}}.{{schema}}.silver_asset_registry r
  ON r.site = c.site AND r.asset_type = c.asset_type AND r.asset_id = c.asset_id;


