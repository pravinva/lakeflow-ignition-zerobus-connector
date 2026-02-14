#!/usr/bin/env python3
"""
Isolate which table constraint causes Zerobus INTERNAL/1521.

Creates several variants of zerobus_events with constraints removed
one at a time, then tries to create a Zerobus JSON stream to each.

Variants tested (in order):
  1. v0_clean       -- no PK, no NOT NULL, no CDF, no CLUSTER BY
  2. v1_notnull     -- add NOT NULL on event_id/event_time/tag_path/tag_provider
  3. v2_pk          -- add PRIMARY KEY (event_id)
  4. v3_cluster     -- add CLUSTER BY (event_time, tag_path)
  5. v4_cdf         -- add CDF (delta.enableChangeDataFeed)
  6. v5_all         -- all constraints (same as production zerobus_events)

For each variant: CREATE TABLE, GRANT SP, try stream creation, report pass/fail.

Usage (from repo root):
  export $(grep -v '^#' .env | xargs)
  cd zerobus-test && uv run python isolate_constraints.py
"""

import os
import sys
import time
import uuid

# Databricks SDK for table creation
try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    sys.exit("Install databricks-sdk: uv add databricks-sdk (or run from repo root with uv run --with databricks-sdk)")

from zerobus.sdk.sync import ZerobusSdk
from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties

# --- Configuration -----------------------------------------------------------
SERVER_ENDPOINT = os.environ.get("ZEROBUS_ENDPOINT", "7405607216190670.zerobus.eastus2.azuredatabricks.net")
WORKSPACE_URL = os.environ.get("DATABRICKS_HOST", "https://adb-7405607216190670.10.azuredatabricks.net")
CLIENT_ID = os.environ.get("DATABRICKS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DATABRICKS_CLIENT_SECRET", "")
CATALOG = os.environ.get("CATALOG", "agl_demo")
SCHEMA = os.environ.get("SCHEMA", "ot")
SP_ID = os.environ.get("SP_APPLICATION_ID", "66c066ad-d5a9-496f-8da5-6d7bc2f5d954")
WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "e65d34bf5b095b0f")
DATABRICKS_PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE", "daveok")
# -----------------------------------------------------------------------------

# Base columns (no constraints)
BASE_COLUMNS = """
  event_id              STRING,
  event_time            BIGINT,
  tag_path              STRING,
  tag_provider          STRING,
  numeric_value         DOUBLE,
  string_value          STRING,
  boolean_value         BOOLEAN,
  quality               STRING,
  quality_code          INT,
  source_system         STRING,
  ingestion_timestamp   BIGINT,
  data_type             STRING,
  alarm_state           STRING,
  alarm_priority        INT,
  sdt_compressed        BOOLEAN,
  compression_ratio     DOUBLE,
  sdt_enabled           BOOLEAN,
  batch_bytes_sent      BIGINT
""".strip()

NOTNULL_COLUMNS = BASE_COLUMNS.replace(
    "event_id              STRING",
    "event_id              STRING      NOT NULL"
).replace(
    "event_time            BIGINT",
    "event_time            BIGINT      NOT NULL"
).replace(
    "tag_path              STRING,\n  tag_provider",
    "tag_path              STRING      NOT NULL,\n  tag_provider"
).replace(
    "tag_provider          STRING",
    "tag_provider          STRING      NOT NULL"
)

# Variant definitions: (suffix, columns, extra_clauses, tblproperties)
VARIANTS = [
    ("v0_clean",   BASE_COLUMNS,    "",                                   ""),
    ("v1_notnull", NOTNULL_COLUMNS, "",                                   ""),
    ("v2_pk",      BASE_COLUMNS + ",\n  CONSTRAINT pk PRIMARY KEY (event_id)", "", ""),
    ("v3_cluster", BASE_COLUMNS,    "CLUSTER BY (event_time, tag_path)",  ""),
    ("v4_cdf",     BASE_COLUMNS,    "",                                   "TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')"),
    ("v5_all",     NOTNULL_COLUMNS + ",\n  CONSTRAINT pk PRIMARY KEY (event_id)",
                                    "CLUSTER BY (event_time, tag_path)",  "TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')"),
]


def run_sql(w, stmt: str, desc: str) -> bool:
    try:
        resp = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=stmt.strip(),
            wait_timeout="30s",
        )
        state = getattr(getattr(resp, "status", None), "state", None)
        ok = state is not None and (str(state) == "SUCCEEDED" or str(state).endswith("SUCCEEDED"))
        if not ok:
            err = getattr(getattr(resp, "status", None), "error", None)
            print(f"    SQL FAILED ({desc}): state={state} error={err}")
        return ok
    except Exception as e:
        print(f"    SQL FAILED ({desc}): {e}")
        return False


def test_stream(table_name: str) -> tuple[bool, str]:
    """Try to create a JSON stream to the table. Returns (success, message)."""
    try:
        sdk = ZerobusSdk(SERVER_ENDPOINT, WORKSPACE_URL)
        table_properties = TableProperties(table_name)
        options = StreamConfigurationOptions(record_type=RecordType.JSON)
        stream = sdk.create_stream(CLIENT_ID, CLIENT_SECRET, table_properties, options)
        # Send one record to confirm it works end-to-end
        record = {
            "event_id": str(uuid.uuid4()),
            "event_time": int(time.time() * 1_000_000),
            "tag_path": "[test]constraint_test",
            "tag_provider": "test",
            "numeric_value": 42.0,
            "string_value": "",
            "boolean_value": False,
            "quality": "Good",
            "quality_code": 192,
            "source_system": "constraint-isolator",
            "ingestion_timestamp": int(time.time() * 1_000_000),
            "data_type": "DOUBLE",
            "alarm_state": "",
            "alarm_priority": 0,
            "sdt_compressed": False,
            "compression_ratio": 0.0,
            "sdt_enabled": False,
            "batch_bytes_sent": 0,
        }
        ack = stream.ingest_record(record)
        ack.wait_for_ack()
        stream.close()
        return True, "stream created + 1 record ingested"
    except Exception as e:
        msg = str(e)
        if "1521" in msg:
            return False, "FAILED: 1521 (stream creation rejected)"
        return False, f"FAILED: {msg[:120]}"


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit("Set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET in environment.")

    print(f"=== Zerobus 1521 Constraint Isolation ===")
    print(f"Catalog: {CATALOG}, Schema: {SCHEMA}, SP: {SP_ID}")
    print(f"Endpoint: {SERVER_ENDPOINT}")
    print(f"Workspace: {WORKSPACE_URL}")
    print()

    w = WorkspaceClient(profile=DATABRICKS_PROFILE)

    results = []
    for suffix, columns, extra, tblprops in VARIANTS:
        table_name = f"{CATALOG}.{SCHEMA}.zb_test_{suffix}"
        print(f"--- {suffix} ({table_name}) ---")

        # Drop if exists (clean slate)
        run_sql(w, f"DROP TABLE IF EXISTS {table_name}", "DROP")

        # Create
        ddl = f"CREATE TABLE {table_name} (\n{columns}\n)\n{extra}\n{tblprops}"
        if not run_sql(w, ddl, "CREATE"):
            results.append((suffix, "SKIP", "table creation failed"))
            continue

        # Grant SP
        if not run_sql(w, f"GRANT MODIFY, SELECT ON TABLE {table_name} TO `{SP_ID}`", "GRANT"):
            results.append((suffix, "SKIP", "grant failed"))
            continue

        # Test Zerobus stream
        print(f"    Testing Zerobus stream...")
        ok, msg = test_stream(table_name)
        status = "PASS" if ok else "FAIL"
        print(f"    {status}: {msg}")
        results.append((suffix, status, msg))

        # Cleanup
        run_sql(w, f"DROP TABLE IF EXISTS {table_name}", "DROP cleanup")
        print()

    # Summary
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for suffix, status, msg in results:
        constraints = {
            "v0_clean":   "none (bare columns)",
            "v1_notnull": "NOT NULL on 4 cols",
            "v2_pk":      "PRIMARY KEY (event_id)",
            "v3_cluster": "CLUSTER BY (event_time, tag_path)",
            "v4_cdf":     "CDF enabled",
            "v5_all":     "NOT NULL + PK + CLUSTER BY + CDF (production)",
        }
        print(f"  {status:4s}  {suffix:<14s}  {constraints.get(suffix, ''):<45s}  {msg}")

    any_fail = any(s == "FAIL" for _, s, _ in results)
    if any_fail:
        print("\n>>> One or more variants FAILED. The constraint(s) listed are likely causing 1521.")
    else:
        print("\n>>> All variants PASSED. The issue may be protobuf-specific, not table constraints.")

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
