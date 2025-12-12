-- Tilt Renewables onboarding - Bronze ingestion table (v1)
--
-- IMPORTANT:
-- This table schema is the ingestion contract. It must match:
--   module/src/main/proto/ot_event.proto
-- Column names, types, and order must match.
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name
--   {{sp}}       : service principal used by the Ignition module

CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.ot_events_bronze (
  event_id STRING,
  event_time TIMESTAMP,
  tag_path STRING,
  tag_provider STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  quality STRING,
  quality_code INT,
  source_system STRING,
  ingestion_timestamp BIGINT,
  data_type STRING,
  alarm_state STRING,
  alarm_priority INT
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

GRANT SELECT, MODIFY ON TABLE {{catalog}}.{{schema}}.ot_events_bronze TO `{{sp}}`;

-- Optional performance tuning (run periodically):
-- OPTIMIZE {{catalog}}.{{schema}}.ot_events_bronze ZORDER BY (source_system, tag_path);


