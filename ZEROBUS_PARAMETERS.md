# Zerobus SDK Parameters Being Used

**Date:** December 9, 2025  
**Issue:** Getting `UNIMPLEMENTED` error when calling Zerobus API

---

## SDK Initialization Parameters

### 1. ZerobusSdk Constructor
```java
new ZerobusSdk(
    endpoint,      // "e2-demo-field-eng.cloud.databricks.com"
    workspaceUrl   // "https://e2-demo-field-eng.cloud.databricks.com"
)
```

**Values:**
- **Endpoint:** `e2-demo-field-eng.cloud.databricks.com` (no https://)
- **Workspace URL:** `https://e2-demo-field-eng.cloud.databricks.com` (with https://)

---

### 2. TableProperties Configuration
```java
new TableProperties<>(
    targetTable,              // "ignition_demo.scada_data.tag_events"
    OTEvent.getDefaultInstance()  // Protobuf message instance
)
```

**Values:**
- **Target Table:** `ignition_demo.scada_data.tag_events`
- **Catalog:** `ignition_demo`
- **Schema:** `scada_data`
- **Table:** `tag_events`
- **Table Type:** MANAGED Delta table
- **Message Type:** `com.example.ignition.zerobus.proto.OTEvent` (Protobuf)

---

### 3. OAuth Authentication
```java
zerobusSdk.createStream(
    tableProperties,
    oauthClientId,      // Service principal client ID
    oauthClientSecret,  // Service principal client secret
    streamOptions
)
```

**Values:**
- **OAuth Client ID:** `<your-client-id>`
- **OAuth Client Secret:** `<your-client-secret>`
- **Auth Method:** OAuth2 Client Credentials Flow

---

### 4. StreamConfigurationOptions
```java
StreamConfigurationOptions.builder()
    .setMaxInflightRecords(10000)
    .setRecovery(true)
    .setRecoveryTimeoutMs(30000)
    .setRecoveryBackoffMs(1000)
    .setRecoveryRetries(3)
    .setFlushTimeoutMs(60000)
    .setServerLackOfAckTimeoutMs(60000)
    .setAckCallback(this::handleAcknowledgment)
    .build()
```

**Values:**
- **Max Inflight Records:** `10000`
- **Recovery Enabled:** `true`
- **Recovery Timeout:** `30000` ms (30 seconds)
- **Recovery Backoff:** `1000` ms (1 second)
- **Recovery Retries:** `3`
- **Flush Timeout:** `60000` ms (60 seconds)
- **Server Lack of Ack Timeout:** `60000` ms (60 seconds)
- **Ack Callback:** Custom acknowledgment handler

---

## Permissions Granted

**Service Principal:** `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`

**Catalog Level:**
- ✅ USE CATALOG on `ignition_demo`

**Schema Level:**
- ✅ USE SCHEMA on `ignition_demo.scada_data`

**Table Level:**
- ✅ SELECT on `ignition_demo.scada_data.tag_events`
- ✅ MODIFY on `ignition_demo.scada_data.tag_events`

---

## Delta Table Schema

```sql
CREATE TABLE ignition_demo.scada_data.tag_events (
    event_id STRING,
    event_time TIMESTAMP,
    tag_path STRING,
    tag_provider STRING,
    numeric_value DOUBLE,
    string_value STRING,
    boolean_value BOOLEAN,
    quality STRING,
    quality_code INT,
    source_system STRING,
    ingestion_timestamp TIMESTAMP,
    data_type STRING,
    alarm_state STRING,
    alarm_priority INT
)
USING DELTA
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
```

**Table Properties:**
- ✅ Format: DELTA
- ✅ Type: MANAGED (not EXTERNAL)
- ✅ Name format: Valid (ASCII, digits, underscores)
- ✅ CDC enabled
- ✅ Auto-optimize enabled

---

## Protobuf Schema (Current)

```protobuf
message OTEvent {
  int64 event_time = 1;
  string tag_path = 2;
  string asset_id = 3;                    // ⚠️ NOT in Delta table
  string asset_path = 4;                  // ⚠️ NOT in Delta table
  oneof value {
    double numeric_value = 5;
    string string_value = 6;
    bool boolean_value = 7;
    int64 integer_value = 8;
  }
  string value_string = 9;                // ⚠️ NOT in Delta table
  Quality quality = 10;                   // ⚠️ Enum, not string+int
  string source_system = 11;
  // ... more fields ...
}
```

**⚠️ SCHEMA MISMATCH ISSUE:**
- ❌ Missing: `event_id` (required by Delta table)
- ❌ Missing: `tag_provider` (required by Delta table)
- ❌ Missing: `quality_code` (required by Delta table)
- ❌ Missing: `ingestion_timestamp` (required by Delta table)
- ❌ Missing: `data_type` (required by Delta table)
- ❌ Missing: `alarm_state` (required by Delta table)
- ❌ Missing: `alarm_priority` (required by Delta table)
- ❌ Extra: `asset_id`, `asset_path`, `value_string` (not in Delta table)
- ❌ Type mismatch: `quality` is enum in Proto, needs to be `string` + `int`

---

## SDK Version & Dependencies

**Maven Coordinates:**
```xml
<dependency>
    <groupId>com.databricks</groupId>
    <artifactId>zerobus-ingest-sdk</artifactId>
    <version>0.1.0</version>
</dependency>
```

**Java Version:** Java 17  
**Protocol:** gRPC over HTTPS  
**Protobuf Version:** 3.21.12

---

## Error Being Encountered

```
com.databricks.zerobus.ZerobusException: 
Stream creation failed: com.databricks.zerobus.ZerobusException: 
Stream failed: UNIMPLEMENTED

Caused by: io.grpc.StatusRuntimeException: UNIMPLEMENTED
```

**gRPC Method Called:** `ZerobusGrpc.ephemeralStream()`

---

## What We've Verified

✅ Zerobus is enabled in workspace (confirmed by Databricks team)  
✅ Service principal has correct permissions (SELECT, MODIFY)  
✅ OAuth authentication works (no 401 errors)  
✅ Network connectivity works (gRPC connection established)  
✅ Table is MANAGED Delta table (not EXTERNAL)  
✅ Table name format is valid  
❌ **Protobuf schema does NOT match Delta table schema** ← LIKELY CAUSE

---

## Likely Root Cause

**Schema Mismatch:** Zerobus requires the Protobuf schema to match the Delta table schema EXACTLY:
- Same number of columns
- Same column names (case-sensitive)
- Same data types
- Same nullability

Our current Protobuf has 16 fields with different names than the Delta table's 14 columns.

**Zerobus validation:** When `createStream()` is called, Zerobus likely validates the Protobuf schema against the Delta table schema. If they don't match exactly, it may return `UNIMPLEMENTED` as a generic error.

---

## Questions for Databricks Team

1. **Does Zerobus validate Protobuf schema against Delta table schema before creating the stream?**
   - If yes, does a schema mismatch cause `UNIMPLEMENTED` error?
   - Or should we get a more specific error like `INVALID_ARGUMENT`?

2. **What are the exact schema matching requirements?**
   - Must column names match exactly?
   - Must column order match?
   - Are nullable columns allowed?
   - Can Protobuf have optional fields?

3. **How should timestamps be represented?**
   - Delta table has `TIMESTAMP` type
   - Should Protobuf use `int64` (epoch millis) or `google.protobuf.Timestamp`?

4. **Are there any workspace-level configurations needed for Zerobus?**
   - IP allowlisting?
   - Service principal additional permissions?
   - Unity Catalog specific settings?

---

## Next Steps

1. **Fix Protobuf schema** to exactly match Delta table
2. **Regenerate Java classes** from updated .proto file
3. **Rebuild module** with corrected schema
4. **Retry connection** with matching schema
5. **Verify data flow** if connection succeeds

---

## Contact Information

**Workspace:** `e2-demo-field-eng.cloud.databricks.com`  
**Service Principal:** `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`  
**Target Table:** `ignition_demo.scada_data.tag_events`  
**SDK Version:** `com.databricks:zerobus-ingest-sdk:0.1.0`

