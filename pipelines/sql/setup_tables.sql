-- AGL OT Lakehouse Demo - Table Setup
-- Usage: Run against your Databricks SQL Warehouse.
-- Replace ${catalog} and ${schema} with your target catalog/schema,
-- or set them as query parameters (e.g., agl_demo.ot).

-- 1. Bronze: raw tag events from Ignition via Zerobus
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.raw_tags (
  event_timestamp   TIMESTAMP   NOT NULL COMMENT 'Source timestamp from Ignition',
  ingest_timestamp  TIMESTAMP   NOT NULL COMMENT 'Time Zerobus persists to Delta',
  asset_id          STRING      NOT NULL COMMENT 'Unique asset identifier (e.g. wind_hexham_t01)',
  asset_type        STRING      NOT NULL COMMENT 'wind_turbine | battery_bess | solar | gas',
  tag_name          STRING      NOT NULL COMMENT 'Full tag path (e.g. generator/speed_rpm)',
  tag_value         DOUBLE      NOT NULL COMMENT 'Numeric value',
  quality           INT         NOT NULL COMMENT 'OPC quality code (192 = good)',
  source_system     STRING      NOT NULL COMMENT 'ignition_sim for demo',
  sdt_compressed    BOOLEAN     NOT NULL COMMENT 'True if this record survived SDT compression',
  compression_ratio DOUBLE               COMMENT 'Running ratio of raw-to-compressed events per tag'
)
COMMENT 'Bronze layer: raw OT tag change events from Ignition via Zerobus';

-- 2. Silver: windowed aggregations
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.aggregated_tags (
  window_start      TIMESTAMP   NOT NULL COMMENT 'Aggregation window start',
  window_end        TIMESTAMP   NOT NULL COMMENT 'Aggregation window end',
  asset_id          STRING      NOT NULL COMMENT 'Asset identifier',
  tag_name          STRING      NOT NULL COMMENT 'Tag path',
  avg_value         DOUBLE               COMMENT 'Mean value in window',
  min_value         DOUBLE               COMMENT 'Min value in window',
  max_value         DOUBLE               COMMENT 'Max value in window',
  stddev_value      DOUBLE               COMMENT 'Std deviation in window',
  sample_count      INT                  COMMENT 'Raw samples in window',
  compressed_count  INT                  COMMENT 'Post-SDT samples in window'
)
COMMENT 'Silver layer: windowed tag aggregations';

-- 3. Ingest metrics (5-second windows)
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.ingest_metrics (
  window_start          TIMESTAMP   NOT NULL COMMENT '5-second window start',
  window_end            TIMESTAMP   NOT NULL COMMENT '5-second window end',
  records_raw           LONG                 COMMENT 'Records generated before SDT',
  records_after_sdt     LONG                 COMMENT 'Records that survived SDT compression',
  bytes_estimate        LONG                 COMMENT 'Approximate bytes written to Delta',
  avg_latency_ms        DOUBLE               COMMENT 'Avg ingest_timestamp - event_timestamp in ms',
  p99_latency_ms        DOUBLE               COMMENT 'P99 latency in ms',
  tags_active           LONG                 COMMENT 'Distinct tags seen in window',
  sdt_compression_ratio DOUBLE               COMMENT 'records_raw / records_after_sdt'
)
COMMENT 'Ingest throughput and latency metrics per 5-second window';

-- 4. SDT configuration per tag pattern
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.sdt_config (
  tag_pattern       STRING      NOT NULL COMMENT 'Glob pattern matching tag names (e.g. */temperature_c)',
  comp_dev          DOUBLE               COMMENT 'Compression deviation (engineering units)',
  comp_dev_percent  DOUBLE               COMMENT 'CompDev as % of tag span',
  comp_max_seconds  INT                  COMMENT 'Max time before forcing an archive event',
  comp_min_seconds  INT                  COMMENT 'Min time between archived events'
)
COMMENT 'Swinging Door Trending compression configuration per tag pattern';

-- Pre-populate SDT defaults
MERGE INTO ${catalog}.${schema}.sdt_config AS target
USING (
  SELECT * FROM VALUES
    ('*/temperature_c',  0.5,  NULL, 600, 0),
    ('*/power_kw',       NULL, 1.0,  600, 0),
    ('*/soc_pct',        0.5,  NULL, 600, 0)
  AS defaults(tag_pattern, comp_dev, comp_dev_percent, comp_max_seconds, comp_min_seconds)
) AS source
ON target.tag_pattern = source.tag_pattern
WHEN NOT MATCHED THEN INSERT *;

-- 5. Asset metadata
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.assets (
  asset_id          STRING      NOT NULL COMMENT 'Primary key',
  asset_name        STRING      NOT NULL COMMENT 'Display name',
  asset_type        STRING      NOT NULL COMMENT 'wind_turbine / battery_bess',
  site_name         STRING      NOT NULL COMMENT 'e.g. Hexham, Liddell, Tomago',
  capacity_mw       DOUBLE               COMMENT 'Rated capacity in MW',
  latitude          DOUBLE               COMMENT 'For map display',
  longitude         DOUBLE               COMMENT 'For map display',
  commissioned_date DATE                 COMMENT 'Nullable',
  tag_count         INT                  COMMENT 'Number of tags per asset'
)
COMMENT 'Asset metadata for wind turbines and battery BESS units';
