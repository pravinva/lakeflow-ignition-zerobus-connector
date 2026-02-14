# OTEvent protobuf ↔ Delta table schema alignment

The Zerobus connector sends `OTEvent` protobuf messages. The target Delta table (`zerobus_events`) **must** match the proto in column names, order, and types for Zerobus to accept the stream. Mismatch can cause INTERNAL/1521.

## Field-by-field alignment

| Proto (ot_event.proto) | Delta (zerobus_events) | Notes |
|------------------------|------------------------|-------|
| event_id string        | event_id STRING        | PK    |
| event_time int64       | event_time BIGINT      | **Microseconds** since Unix epoch (Java sends micros) |
| tag_path string        | tag_path STRING        |       |
| tag_provider string    | tag_provider STRING    |       |
| numeric_value double   | numeric_value DOUBLE   |       |
| string_value string    | string_value STRING    |       |
| boolean_value bool     | boolean_value BOOLEAN  |       |
| quality string         | quality STRING         |       |
| quality_code int32     | quality_code INT       |       |
| source_system string   | source_system STRING   |       |
| ingestion_timestamp int64 | ingestion_timestamp BIGINT | **Microseconds** since epoch |
| data_type string       | data_type STRING       |       |
| alarm_state string     | alarm_state STRING     |       |
| alarm_priority int32   | alarm_priority INT     |       |
| sdt_compressed bool    | sdt_compressed BOOLEAN |       |
| compression_ratio double | compression_ratio DOUBLE |     |
| sdt_enabled bool       | sdt_enabled BOOLEAN    |       |
| batch_bytes_sent int64 | batch_bytes_sent BIGINT |      |

## Timestamp units

- **Java (OtEventMapper):** `event_time` and `ingestion_timestamp` are set in **microseconds** (`System.currentTimeMillis() * 1000L`, `event.getTimestamp().getTime() * 1000L`).
- **Delta table:** `event_time` and `ingestion_timestamp` are **BIGINT** storing **microseconds** since epoch.
- Proto comments and this doc say "microseconds"; do not change to milliseconds without updating both Java and table.

## If you change the table

After changing `examples/agl_fleet/setup_databricks.sql` or the proto:

1. Ensure column **order** matches the proto field order above.
2. Ensure **names** match (snake_case).
3. Ensure **types**: int64→BIGINT, int32→INT, double→DOUBLE, bool→BOOLEAN, string→STRING.
4. Re-run `make db-setup-sql` (or apply DDL) and `make configure-83` so the gateway points at the table.

Zerobus docs recommend generating the proto **from** the table (`python -m zerobus.tools.generate_proto` or Java SDK tool). This repo uses a hand-written proto; keep it in sync with the table manually.

## Liquid clustering incompatibility (CLUSTER BY causes 1521)

**Zerobus Ingest does NOT support tables with liquid clustering (`CLUSTER BY`).** Stream creation fails with `INTERNAL: Error Code 1521` if the target table has any `CLUSTER BY` clause.

This was systematically isolated (2026-02-14) by testing 6 table variants:

| Constraint | Result |
|---|---|
| None (bare columns) | PASS |
| NOT NULL | PASS |
| PRIMARY KEY | PASS |
| **CLUSTER BY** | **FAIL (1521)** |
| CDF | PASS |
| All combined | **FAIL** (due to CLUSTER BY) |

**Workaround:** Do not use `CLUSTER BY` on tables that Zerobus writes to. If you need clustering for query performance, pause Zerobus ingest, add clustering (`ALTER TABLE ... CLUSTER BY (event_time, tag_path)`), OPTIMIZE, then remove it (`ALTER TABLE ... CLUSTER BY NONE`) before resuming Zerobus.
