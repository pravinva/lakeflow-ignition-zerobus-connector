#!/usr/bin/env python3
"""Verify Databricks setup"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient(
    host="https://e2-demo-field-eng.cloud.databricks.com"
)  # Uses credentials from ~/.databrickscfg

# Get warehouse
warehouses = list(w.warehouses.list())
warehouse_id = warehouses[0].id

print("🔍 Checking existing resources...")
print()

# Check schema
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement="SHOW SCHEMAS IN main LIKE 'ignition_ot_test'",
        wait_timeout="30s"
    )
    print("✅ Schema 'main.ignition_ot_test' exists")
except Exception as e:
    print(f"❌ Schema check failed: {e}")

# Check table
try:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement="SHOW TABLES IN main.ignition_ot_test",
        wait_timeout="30s"
    )
    if result.result and result.result.data_array:
        print(f"✅ Found {len(result.result.data_array)} table(s)")
        for row in result.result.data_array:
            print(f"   • {row[1]}")  # table name
    else:
        print("⚠️  No tables found in schema")
except Exception as e:
    print(f"❌ Table check failed: {e}")

print()
print("📝 To create table manually, run:")
print()
print("""
CREATE TABLE IF NOT EXISTS main.ignition_ot_test.bronze_events (
  event_time TIMESTAMP,
  tag_path STRING,
  asset_id STRING,
  numeric_value DOUBLE,
  quality STRING,
  source_system STRING
) USING DELTA;
""")

