#!/usr/bin/env python3
"""
Setup script for Databricks testing environment
Creates schema and tables for Ignition Zerobus Connector testing
"""

from databricks import sql
import os
from pathlib import Path

# Read credentials from ~/.databrickscfg
config_path = Path.home() / '.databrickscfg'
host = "https://e2-demo-field-eng.cloud.databricks.com"
token = None

# Parse config file
with open(config_path, 'r') as f:
    for line in f:
        if 'host' in line and 'e2-demo-field-eng' in line:
            host = line.split('=')[1].strip()
        if line.strip().startswith('token') and token is None:
            # Get the next token after finding the right host
            token = line.split('=')[1].strip()
            break

if not token:
    # Fallback to first token
    with open(config_path, 'r') as f:
        for line in f:
            if line.strip().startswith('token'):
                token = line.split('=')[1].strip()
                break

print(f"🔗 Connecting to: {host}")
print(f"👤 User: pravin.varma@databricks.com")
print()

# SQL statements to execute
sql_statements = [
    # Create schema
    """
    CREATE SCHEMA IF NOT EXISTS main.ignition_ot_test
    COMMENT 'Testing schema for Ignition → Zerobus → Databricks integration'
    """,
    
    # Create bronze events table
    """
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
    """,
    
    # Create view for easy querying
    """
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
    """
]

# Note: This requires databricks-sql-connector
# Install with: pip install databricks-sql-connector

try:
    # Try to use SQL warehouse (if available)
    print("⚠️  Note: This script requires a running SQL Warehouse.")
    print("📝 Alternative: Copy SQL from setup_databricks_testing.sql")
    print("   and run it in Databricks SQL Editor")
    print()
    print("✅ SQL file created: setup_databricks_testing.sql")
    print()
    print("🔗 Open in browser:")
    print(f"   {host}/sql/editor")
    print()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Alternative approaches:")
    print("1. Run SQL file in Databricks SQL Editor")
    print("2. Use Databricks notebook")
    print("3. Create tables manually in Catalog Explorer")

# Print summary
print("\n" + "="*60)
print("SETUP SUMMARY")
print("="*60)
print()
print("Target Configuration:")
print(f"  Catalog: main")
print(f"  Schema:  ignition_ot_test")
print(f"  Table:   bronze_events")
print()
print("Full table name for Ignition module:")
print("  👉 main.ignition_ot_test.bronze_events")
print()
print("Zerobus Endpoint (extract from workspace URL):")
workspace_id = host.split('//')[1].split('.')[0]
region = 'cloud'  # Adjust based on your workspace
print(f"  👉 {workspace_id}.zerobus.{region}.databricks.com")
print()
print("Next Steps:")
print("  1. Run setup_databricks_testing.sql in SQL Editor")
print("  2. Create OAuth service principal")
print("  3. Grant permissions to service principal")
print("  4. Configure Ignition module with credentials")
print()

