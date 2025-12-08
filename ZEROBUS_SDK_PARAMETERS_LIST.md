# Zerobus SDK Parameters - Complete List

**Error:** `io.grpc.StatusRuntimeException: UNIMPLEMENTED`  
**Workspace:** `e2-demo-field-eng.cloud.databricks.com`

---

## 1. ZerobusSdk Constructor Parameters

```java
ZerobusSdk sdk = new ZerobusSdk(
    endpoint,
    workspaceUrl
);
```

**Parameter 1: endpoint**
- Value: `"e2-demo-field-eng.cloud.databricks.com"`
- Type: String
- Format: Hostname only (no protocol)

**Parameter 2: workspaceUrl**
- Value: `"https://e2-demo-field-eng.cloud.databricks.com"`
- Type: String
- Format: Full URL with https://

---

## 2. TableProperties Parameters

```java
TableProperties<OTEvent> tableProperties = new TableProperties<>(
    targetTable,
    protoInstance
);
```

**Parameter 1: targetTable**
- Value: `"ignition_demo.scada_data.tag_events"`
- Type: String
- Format: `catalog.schema.table`
- Verified: Table exists and is MANAGED Delta table

**Parameter 2: protoInstance**
- Value: `OTEvent.getDefaultInstance()`
- Type: Message (Protobuf)
- Class: `com.example.ignition.zerobus.proto.OTEvent`

---

## 3. createStream Parameters

```java
CompletableFuture<ZerobusStream<OTEvent>> streamFuture = sdk.createStream(
    tableProperties,
    oauthClientId,
    oauthClientSecret,
    streamOptions
);
```

**Parameter 1: tableProperties**
- Type: TableProperties<OTEvent>
- See section 2 above

**Parameter 2: oauthClientId**
- Value: `"15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d"`
- Type: String
- Description: Service principal client ID
- Verified: Service principal exists and has permissions

**Parameter 3: oauthClientSecret**
- Value: `"dose****"` (redacted)
- Type: String
- Description: Service principal client secret
- Verified: OAuth authentication succeeds (no 401 errors)

**Parameter 4: streamOptions**
- Type: StreamConfigurationOptions
- See section 4 below

---

## 4. StreamConfigurationOptions Parameters

```java
StreamConfigurationOptions options = StreamConfigurationOptions.builder()
    .setMaxInflightRecords(maxInflightRecords)
    .setRecovery(recovery)
    .setRecoveryTimeoutMs(recoveryTimeoutMs)
    .setRecoveryBackoffMs(recoveryBackoffMs)
    .setRecoveryRetries(recoveryRetries)
    .setFlushTimeoutMs(flushTimeoutMs)
    .setServerLackOfAckTimeoutMs(serverLackOfAckTimeoutMs)
    .setAckCallback(ackCallback)
    .build();
```

**All StreamConfigurationOptions values:**
- `maxInflightRecords`: `10000` (int)
- `recovery`: `true` (boolean)
- `recoveryTimeoutMs`: `30000` (int) - 30 seconds
- `recoveryBackoffMs`: `1000` (int) - 1 second
- `recoveryRetries`: `3` (int)
- `flushTimeoutMs`: `60000` (int) - 60 seconds
- `serverLackOfAckTimeoutMs`: `60000` (int) - 60 seconds
- `ackCallback`: Custom callback function

---

## 5. Target Table Details

**Full table name:** `ignition_demo.scada_data.tag_events`

**Breakdown:**
- Catalog: `ignition_demo`
- Schema: `scada_data`
- Table: `tag_events`

**Table properties:**
- Type: MANAGED (not EXTERNAL)
- Format: DELTA
- CDC enabled: Yes
- Auto-optimize: Yes

**Table schema (14 columns):**
```sql
event_id STRING
event_time TIMESTAMP
tag_path STRING
tag_provider STRING
numeric_value DOUBLE
string_value STRING
boolean_value BOOLEAN
quality STRING
quality_code INT
source_system STRING
ingestion_timestamp TIMESTAMP
data_type STRING
alarm_state STRING
alarm_priority INT
```

---

## 6. Service Principal Permissions

**Service Principal:** `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`

**Granted permissions:**
- `USE CATALOG` on `ignition_demo`
- `USE SCHEMA` on `ignition_demo.scada_data`
- `SELECT` on `ignition_demo.scada_data.tag_events`
- `MODIFY` on `ignition_demo.scada_data.tag_events`

---

## 7. Protobuf Message Type

**Class:** `com.example.ignition.zerobus.proto.OTEvent`

**Package:** `com.example.ignition.zerobus.proto`

**Fields (14 total):**
```protobuf
message OTEvent {
  string event_id = 1;
  int64 event_time = 2;
  string tag_path = 3;
  string tag_provider = 4;
  double numeric_value = 5;
  string string_value = 6;
  bool boolean_value = 7;
  string quality = 8;
  int32 quality_code = 9;
  string source_system = 10;
  int64 ingestion_timestamp = 11;
  string data_type = 12;
  string alarm_state = 13;
  int32 alarm_priority = 14;
}
```

---

## 8. SDK Version & Dependencies

**Zerobus SDK:**
- GroupId: `com.databricks`
- ArtifactId: `zerobus-ingest-sdk`
- Version: `0.1.0`

**Protobuf:**
- Version: `3.21.12`
- Syntax: proto3

**Java:**
- Version: 17

---

## 9. Potential Parameter Issues

### Issue 1: Endpoint Format ⚠️
**Current:** `"e2-demo-field-eng.cloud.databricks.com"` (no protocol)

**Questions:**
- Should it include port? `"e2-demo-field-eng.cloud.databricks.com:443"`
- Should it include protocol? `"https://e2-demo-field-eng.cloud.databricks.com"`
- Should it be different from workspaceUrl?

---

### Issue 2: Table Name Format ⚠️
**Current:** `"ignition_demo.scada_data.tag_events"` (3-part name)

**Questions:**
- Is 3-part name correct? (catalog.schema.table)
- Should it be 2-part? (schema.table)
- Should catalog be specified separately?

---

### Issue 3: OAuth Token Endpoint ⚠️
**Current:** Not specified (SDK derives it?)

**Questions:**
- Does Zerobus need explicit OAuth token endpoint?
- Is it derived from workspace URL automatically?
- Should we pass it explicitly?

---

### Issue 4: StreamConfigurationOptions ⚠️
**Current values:**
- `maxInflightRecords`: `10000`
- `recoveryTimeoutMs`: `30000`
- `flushTimeoutMs`: `60000`

**Questions:**
- Are these values within acceptable ranges?
- Are there minimum/maximum limits?
- Could any of these cause UNIMPLEMENTED?

---

## 10. Complete SDK Call

**Actual code:**
```java
// Step 1: Create SDK instance
ZerobusSdk sdk = new ZerobusSdk(
    "e2-demo-field-eng.cloud.databricks.com",
    "https://e2-demo-field-eng.cloud.databricks.com"
);

// Step 2: Configure table
TableProperties<OTEvent> tableProperties = new TableProperties<>(
    "ignition_demo.scada_data.tag_events",
    OTEvent.getDefaultInstance()
);

// Step 3: Configure stream options
StreamConfigurationOptions options = StreamConfigurationOptions.builder()
    .setMaxInflightRecords(10000)
    .setRecovery(true)
    .setRecoveryTimeoutMs(30000)
    .setRecoveryBackoffMs(1000)
    .setRecoveryRetries(3)
    .setFlushTimeoutMs(60000)
    .setServerLackOfAckTimeoutMs(60000)
    .setAckCallback(this::handleAcknowledgment)
    .build();

// Step 4: Create stream
CompletableFuture<ZerobusStream<OTEvent>> streamFuture = sdk.createStream(
    tableProperties,
    "15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d",
    "<CLIENT_SECRET_REDACTED>",
    options
);

// Step 5: Wait for stream
ZerobusStream<OTEvent> stream = streamFuture.get(30000, TimeUnit.MILLISECONDS);
```

---

## 11. Error Details

**Error message:**
```
com.databricks.zerobus.ZerobusException: Stream creation failed: 
com.databricks.zerobus.ZerobusException: Stream failed: UNIMPLEMENTED

Caused by: io.grpc.StatusRuntimeException: UNIMPLEMENTED
```

**When error occurs:**
- During `createStream()` call
- After OAuth authentication succeeds
- Before any data is sent

**What works:**
- ✅ Network connectivity
- ✅ OAuth authentication (no 401 errors)
- ✅ Service principal has permissions
- ✅ Table exists and is accessible

---

## Questions

1. **Endpoint parameter:** Is the format correct? Should it include port or protocol?

2. **Table name:** Is 3-part name (catalog.schema.table) correct?

3. **StreamConfigurationOptions:** Are the values acceptable? Any invalid settings?

4. **Protobuf matching:** Does the Protobuf need to match Delta schema exactly (column names, types, order)?

5. **Any missing parameters?** Are we missing any required configuration?

---

**Please review these parameters and let us know which one(s) are incorrect.**

