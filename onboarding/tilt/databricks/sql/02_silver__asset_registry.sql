-- Tilt Renewables onboarding - Silver: asset registry (dimension)
--
-- Purpose:
--   A small customer-managed table that defines assets (site/fleet metadata).
--   This keeps Silver stable even if tag naming differs across sites/OEMs.
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.silver_asset_registry (
  site STRING,
  asset_type STRING,            -- e.g. WIND_TURBINE, SOLAR_INVERTER, BESS_RACK
  asset_id STRING,              -- customer-defined stable asset identifier
  asset_name STRING,            -- optional human-friendly name
  capacity_kw DOUBLE,           -- optional nameplate
  manufacturer STRING,
  model STRING,
  timezone STRING,              -- IANA tz, e.g. Australia/Sydney
  commissioning_date DATE,
  latitude DOUBLE,
  longitude DOUBLE,
  metadata MAP<STRING, STRING>  -- free-form extensibility
)
USING DELTA;

-- Optional seed examples (safe to delete)
-- INSERT INTO {{catalog}}.{{schema}}.silver_asset_registry
-- SELECT * FROM VALUES
--   ('SiteA','WIND_TURBINE','T07','Turbine 07', 3500, 'OEM1', 'ModelX', 'Australia/Sydney', DATE'2022-01-01', -33.9, 151.2, map('note','example')),
--   ('SiteB','SOLAR_INVERTER','INV12','Inverter 12', 250, 'OEM2', 'InvY', 'Australia/Brisbane', DATE'2023-06-01', -27.4, 153.0, map('note','example'))
-- AS (site, asset_type, asset_id, asset_name, capacity_kw, manufacturer, model, timezone, commissioning_date, latitude, longitude, metadata);


