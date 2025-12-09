#!/usr/bin/env python3
"""Fix table creation without DEFAULT constraints"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

w = WorkspaceClient(
    host="https://e2-demo-field-eng.cloud.databricks.com"
)  # Uses credentials from ~/.databrickscfg

warehouse_id = list(w.warehouses.list())[0].id

print("🔧 Creating bronze_events table (without DEFAULT constraints)...")
print()

sql = """
CREATE TABLE IF NOT EXISTS lakeflow_ignition.ot_data.bronze_events (
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition tag',
  tag_path STRING COMMENT 'Full Ignition tag path',
  asset_id STRING COMMENT 'Asset identifier extracted from tag path',
  asset_path STRING COMMENT 'Asset hierarchy path',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  integer_value BIGINT COMMENT 'Integer tag value',
  value_string STRING COMMENT 'Value as string for all types',
  quality STRING COMMENT 'Data quality: GOOD, BAD, UNCERTAIN, UNKNOWN',
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  site STRING COMMENT 'Site/location identifier',
  line STRING COMMENT 'Production line identifier',
  unit STRING COMMENT 'Equipment unit identifier',
  tag_description STRING COMMENT 'Tag description/metadata',
  engineering_units STRING COMMENT 'Engineering units (PSI, RPM, °C, etc.)',
  ingestion_timestamp TIMESTAMP COMMENT 'Databricks ingestion timestamp'
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'comment' = 'Bronze layer: Raw OT events from Ignition via Zerobus Ingest'
)
"""

try:
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="30s"
    )
    
    if response.status.state == StatementState.SUCCEEDED:
        print("✅ Table created successfully!")
    else:
        print(f"⚠️  Status: {response.status.state}")
        if hasattr(response.status, 'error') and response.status.error:
            print(f"   Error: {response.status.error.message}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("Creating view...")

view_sql = """
CREATE OR REPLACE VIEW lakeflow_ignition.ot_data.vw_recent_events AS
SELECT 
  event_time,
  tag_path,
  asset_id,
  COALESCE(
    CAST(numeric_value AS STRING),
    string_value,
    CAST(boolean_value AS STRING),
    CAST(integer_value AS STRING)
  ) as value,
  quality,
  source_system,
  ingestion_timestamp,
  ROUND((UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)), 2) as latency_seconds
FROM lakeflow_ignition.ot_data.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
ORDER BY event_time DESC
"""

try:
    response = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=view_sql,
        wait_timeout="30s"
    )
    
    if response.status.state == StatementState.SUCCEEDED:
        print("✅ View created successfully!")
    else:
        print(f"⚠️  Status: {response.status.state}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print("✅ ALL DONE!")
print("="*70)
print()
print("📊 Your Resources:")
print("   • Catalog: lakeflow_ignition")
print("   • Schema:  lakeflow_ignition.ot_data")  
print("   • Table:   lakeflow_ignition.ot_data.bronze_events")
print("   • View:    lakeflow_ignition.ot_data.vw_recent_events")
print()
print("🔗 For Ignition Module Configuration:")
print("   Target Table: lakeflow_ignition.ot_data.bronze_events")
print()
print("🔍 View in Databricks:")
print("   https://e2-demo-field-eng.cloud.databricks.com/explore/data/lakeflow_ignition/ot_data/bronze_events")
print()

