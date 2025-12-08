#!/usr/bin/env python3
"""
Setup Databricks tables for Ignition Zerobus Connector testing
Uses credentials from ~/.databrickscfg
"""

import os
import sys
from pathlib import Path

# Credentials loaded from ~/.databrickscfg by WorkspaceClient
host = "https://e2-demo-field-eng.cloud.databricks.com"

print(f"🔗 Connecting to: {host}")
print(f"👤 User: pravin.varma@databricks.com")
print()

# SQL statements to execute
sql_statements = [
    ("Creating schema", """
        CREATE SCHEMA IF NOT EXISTS main.ignition_ot_test
        COMMENT 'Testing schema for Ignition → Zerobus → Databricks integration'
    """),
    
    ("Creating bronze_events table", """
        CREATE TABLE IF NOT EXISTS main.ignition_ot_test.bronze_events (
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
        CREATE OR REPLACE VIEW main.ignition_ot_test.vw_recent_events AS
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
        FROM main.ignition_ot_test.bronze_events
        WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
        ORDER BY event_time DESC
    """)
]

try:
    # Try using databricks-sdk
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.sql import StatementState
        
        w = WorkspaceClient(host=host)  # Uses credentials from ~/.databrickscfg
        
        # Get a warehouse to run SQL on
        warehouses = w.warehouses.list()
        warehouse_list = list(warehouses)
        
        if not warehouse_list:
            print("❌ No SQL warehouses found")
            print("⚠️  Please create a SQL warehouse in Databricks first")
            print(f"   URL: {host}/sql/warehouses")
            sys.exit(1)
        
        warehouse_id = warehouse_list[0].id
        print(f"✅ Using warehouse: {warehouse_list[0].name}")
        print()
        
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
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print()
        print("="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print()
        print("📊 Created Resources:")
        print(f"   • Schema: main.ignition_ot_test")
        print(f"   • Table:  main.ignition_ot_test.bronze_events")
        print(f"   • View:   main.ignition_ot_test.vw_recent_events")
        print()
        print("🔗 Configuration for Ignition Module:")
        print(f"   Workspace URL:    {host}")
        print(f"   Zerobus Endpoint: e2-demo-field-eng.zerobus.cloud.databricks.com")
        print(f"   Target Table:     main.ignition_ot_test.bronze_events")
        print()
        print("🔍 View your table:")
        print(f"   {host}/explore/data/main/ignition_ot_test/bronze_events")
        print()
        
    except ImportError:
        print("❌ databricks-sdk not installed")
        print()
        print("📝 To install:")
        print("   pip install databricks-sdk")
        print()
        print("📝 Or run SQL manually in SQL Editor:")
        print(f"   {host}/sql/editor")
        print()
        print("   Copy SQL from: setup_databricks_testing.sql")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Alternative: Run SQL manually")
    print(f"1. Open: {host}/sql/editor")
    print(f"2. Copy SQL from: setup_databricks_testing.sql")
    sys.exit(1)

