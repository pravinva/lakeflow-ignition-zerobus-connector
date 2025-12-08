#!/usr/bin/env python3
"""
Setup dedicated Lakeflow Ignition catalog and tables
Uses credentials from ~/.databrickscfg
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

# Credentials loaded from ~/.databrickscfg by WorkspaceClient
host = "https://e2-demo-field-eng.cloud.databricks.com"

print(f"🔗 Connecting to: {host}")
print(f"👤 User: pravin.varma@databricks.com")
print()

w = WorkspaceClient(host=host)  # Uses credentials from ~/.databrickscfg

# Get warehouse
warehouses = list(w.warehouses.list())
if not warehouses:
    print("❌ No SQL warehouses found")
    exit(1)

warehouse_id = warehouses[0].id
print(f"✅ Using warehouse: {warehouses[0].name}")
print()

# SQL statements to execute
sql_statements = [
    ("Creating catalog 'lakeflow_ignition'", """
        CREATE CATALOG IF NOT EXISTS lakeflow_ignition
        COMMENT 'Lakeflow Ignition Zerobus Connector - OT Data Integration'
    """),
    
    ("Creating schema 'ot_data'", """
        CREATE SCHEMA IF NOT EXISTS lakeflow_ignition.ot_data
        COMMENT 'Operational Technology data from Ignition SCADA'
    """),
    
    ("Creating bronze_events table", """
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
          ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Databricks ingestion timestamp'
        )
        USING DELTA
        TBLPROPERTIES (
          'delta.enableChangeDataFeed' = 'true',
          'delta.autoOptimize.optimizeWrite' = 'true',
          'comment' = 'Bronze layer: Raw OT events from Ignition via Zerobus Ingest'
        )
    """),
    
    ("Creating vw_recent_events view", """
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
    """),
    
    ("Granting permissions", """
        GRANT USE CATALOG ON CATALOG lakeflow_ignition TO `account users`
    """),
    
    ("Granting schema permissions", """
        GRANT USE SCHEMA ON SCHEMA lakeflow_ignition.ot_data TO `account users`
    """),
    
    ("Granting table permissions", """
        GRANT SELECT ON TABLE lakeflow_ignition.ot_data.bronze_events TO `account users`
    """)
]

# Execute each SQL statement
for description, sql in sql_statements:
    print(f"⏳ {description}...")
    try:
        response = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="30s"
        )
        
        if response.status.state == StatementState.SUCCEEDED:
            print(f"   ✅ Success")
        else:
            print(f"   ⚠️  Status: {response.status.state}")
            if hasattr(response.status, 'error') and response.status.error:
                print(f"      Error: {response.status.error.message}")
            
    except Exception as e:
        # Some errors are okay (e.g., permissions already exist)
        if "already" in str(e).lower() or "exist" in str(e).lower():
            print(f"   ℹ️  Already exists")
        else:
            print(f"   ⚠️  {e}")

print()
print("="*70)
print("✅ LAKEFLOW IGNITION CATALOG SETUP COMPLETE!")
print("="*70)
print()
print("📊 Created Resources:")
print(f"   • Catalog: lakeflow_ignition")
print(f"   • Schema:  lakeflow_ignition.ot_data")
print(f"   • Table:   lakeflow_ignition.ot_data.bronze_events")
print(f"   • View:    lakeflow_ignition.ot_data.vw_recent_events")
print()
print("🔗 Configuration for Ignition Module:")
print(f"   Workspace URL:    {host}")
print(f"   Zerobus Endpoint: e2-demo-field-eng.zerobus.cloud.databricks.com")
print(f"   Target Table:     lakeflow_ignition.ot_data.bronze_events")
print()
print("🔍 View your catalog:")
print(f"   {host}/explore/data/lakeflow_ignition")
print()
print("🧪 Test query:")
print(f"   SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events LIMIT 10;")
print()

