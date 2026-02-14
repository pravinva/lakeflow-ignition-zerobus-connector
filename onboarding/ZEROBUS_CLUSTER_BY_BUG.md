# Zerobus Ingest: Liquid Clustering causes INTERNAL/1521

**Date:** 2026-02-14
**Status:** Undocumented limitation (not in [Zerobus limitations page](https://docs.databricks.com/aws/en/ingestion/zerobus-limits))
**Affects:** All Zerobus Ingest SDKs (Python, Java, Go, Rust, TypeScript), all record types (JSON + Protobuf)
**Workspace:** Azure East US 2 (`adb-7405607216190670`), Python SDK 0.2.0, Java SDK 0.1.0

## Problem

Zerobus Ingest stream creation fails with `INTERNAL: Error Code 1521, Error State 0` when the target Delta table has **liquid clustering** (`CLUSTER BY`) enabled. The error is opaque -- neither the gRPC response nor Databricks docs explain what 1521 means.

```
Stream creation failed: com.databricks.zerobus.ZerobusException:
  Stream failed: INTERNAL: Internal error. Error Code: 1521, Error State: 0.
```

## Root cause

Delta tables created with `CLUSTER BY (col1, col2)` set the `liquid` clustering writer feature in the table's protocol. Zerobus Ingest does not support this Delta writer feature and rejects stream creation at the server side.

This is NOT caused by:
- Invalid credentials (SP OAuth works; `make db-check-sp` passes)
- Missing UC grants (SP has `MODIFY`, `SELECT`)
- Schema mismatch (proto and table columns match exactly)
- NOT NULL constraints, PRIMARY KEY constraints, or Change Data Feed

## Fix

Remove liquid clustering from the target table:

```sql
ALTER TABLE catalog.schema.zerobus_events CLUSTER BY NONE;
```

Stream creation succeeds immediately after this (no gateway restart needed; the retry loop picks it up).

## Isolation methodology

Systematically tested 6 table variants with the Python Zerobus SDK (`RecordType.JSON`), same SP, same endpoint. Each variant was created, granted, tested, then dropped:

| Variant | Table features | Stream creation |
|---------|---------------|----------------|
| v0_clean | Bare columns only | **PASS** |
| v1_notnull | `NOT NULL` on 4 columns | **PASS** |
| v2_pk | `PRIMARY KEY (event_id)` | **PASS** |
| v3_cluster | `CLUSTER BY (event_time, tag_path)` | **FAIL (1521)** |
| v4_cdf | `delta.enableChangeDataFeed = true` | **PASS** |
| v5_all | NOT NULL + PK + CLUSTER BY + CDF | **FAIL (1521)** |

Only the variants containing `CLUSTER BY` failed. The isolation script is at `zerobus-test/isolate_constraints.py`.

## Mini repro

Requires: Databricks workspace with Zerobus enabled, a service principal with UC grants, Python 3.12+, `uv`.

### 1. Install SDK

```bash
mkdir zerobus-repro && cd zerobus-repro
uv init && uv add databricks-zerobus-ingest-sdk
```

### 2. Create two tables (one with CLUSTER BY, one without)

Run in a Databricks SQL editor or notebook as a user with CREATE TABLE:

```sql
-- Table WITHOUT clustering (control)
CREATE TABLE IF NOT EXISTS my_catalog.my_schema.zb_no_cluster (
  id STRING, value DOUBLE
);
GRANT MODIFY, SELECT ON TABLE my_catalog.my_schema.zb_no_cluster
  TO `<your-sp-application-id>`;

-- Table WITH clustering (test)
CREATE TABLE IF NOT EXISTS my_catalog.my_schema.zb_with_cluster (
  id STRING, value DOUBLE
) CLUSTER BY (id);
GRANT MODIFY, SELECT ON TABLE my_catalog.my_schema.zb_with_cluster
  TO `<your-sp-application-id>`;
```

### 3. Run the repro script

```python
"""Minimal repro: Zerobus 1521 with CLUSTER BY."""
import uuid
from zerobus.sdk.sync import ZerobusSdk
from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties

ENDPOINT  = "<workspace-id>.zerobus.<region>.azuredatabricks.net"
WORKSPACE = "https://adb-<workspace-id>.<suffix>.azuredatabricks.net"
CLIENT_ID = "<sp-application-id>"
SECRET    = "<sp-client-secret>"

sdk = ZerobusSdk(ENDPOINT, WORKSPACE)
options = StreamConfigurationOptions(record_type=RecordType.JSON)

for table in ["my_catalog.my_schema.zb_no_cluster",
              "my_catalog.my_schema.zb_with_cluster"]:
    print(f"\nTesting: {table}")
    try:
        stream = sdk.create_stream(
            CLIENT_ID, SECRET,
            TableProperties(table), options
        )
        stream.ingest_record({"id": str(uuid.uuid4()), "value": 42.0}).wait_for_ack()
        stream.close()
        print(f"  PASS")
    except Exception as e:
        print(f"  FAIL: {e}")
```

### Expected output

```
Testing: my_catalog.my_schema.zb_no_cluster
  PASS

Testing: my_catalog.my_schema.zb_with_cluster
  FAIL: Failed to create a stream: ... INTERNAL: Internal error. Error Code: 1521 ...
```

### 4. Cleanup

```sql
DROP TABLE IF EXISTS my_catalog.my_schema.zb_no_cluster;
DROP TABLE IF EXISTS my_catalog.my_schema.zb_with_cluster;
```

## Workaround for production

If you need clustering for read performance but also need Zerobus writes:

1. Keep `CLUSTER BY NONE` on the table while Zerobus is actively writing.
2. Periodically (e.g. daily maintenance window):
   - Pause Zerobus ingest (disable module or stop sending events).
   - `ALTER TABLE ... CLUSTER BY (event_time, tag_path);`
   - `OPTIMIZE catalog.schema.zerobus_events;`
   - `ALTER TABLE ... CLUSTER BY NONE;`
   - Resume Zerobus ingest.

Or use a separate downstream table with clustering that reads from the Zerobus landing table via a streaming pipeline.

## References

- [Zerobus Ingest limitations](https://docs.databricks.com/aws/en/ingestion/zerobus-limits) -- does NOT mention CLUSTER BY
- [Zerobus Ingest usage](https://learn.microsoft.com/en-us/azure/databricks/ingestion/zerobus-ingest) -- table creation examples use no clustering
- [Liquid clustering docs](https://docs.databricks.com/aws/en/delta/clustering) -- no mention of Zerobus incompatibility
- This repo: `module/SCHEMA_ALIGNMENT.md`, `zerobus-test/isolate_constraints.py`
