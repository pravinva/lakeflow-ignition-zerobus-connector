# Protobuf Types Being Used

**Question:** Are we using types that Zerobus doesn't support?

---

## Current Protobuf Schema Types

### Proto3 Scalar Types Used:

```protobuf
message OTEvent {
  string event_id = 1;              // STRING type
  int64 event_time = 2;             // INT64 type (for TIMESTAMP)
  string tag_path = 3;              // STRING type
  string tag_provider = 4;          // STRING type
  double numeric_value = 5;         // DOUBLE type
  string string_value = 6;          // STRING type
  bool boolean_value = 7;           // BOOL type
  string quality = 8;               // STRING type
  int32 quality_code = 9;           // INT32 type
  string source_system = 10;        // STRING type
  int64 ingestion_timestamp = 11;   // INT64 type (for TIMESTAMP)
  string data_type = 12;            // STRING type
  string alarm_state = 13;          // STRING type
  int32 alarm_priority = 14;        // INT32 type
}
```

### Types Summary:
- ✅ **string** (7 fields) - Basic Proto3 scalar type
- ⚠️ **int64** (2 fields) - Used for timestamps (epoch milliseconds)
- ✅ **double** (1 field) - Basic Proto3 scalar type
- ✅ **bool** (1 field) - Basic Proto3 scalar type
- ✅ **int32** (2 fields) - Basic Proto3 scalar type

---

## Mapping to Delta Table Types

| Delta Type | Protobuf Type | Field Example |
|------------|---------------|---------------|
| STRING | string | event_id, tag_path |
| TIMESTAMP | **int64** | event_time, ingestion_timestamp |
| DOUBLE | double | numeric_value |
| BOOLEAN | bool | boolean_value |
| INT | int32 | quality_code, alarm_priority |

---

## Potential Issues

### 1. Timestamp Representation ⚠️

**Current:** Using `int64` to represent timestamps as milliseconds since Unix epoch

**Question:** Does Zerobus require `google.protobuf.Timestamp` instead?

**Alternative approach:**
```protobuf
import "google/protobuf/timestamp.proto";

message OTEvent {
  google.protobuf.Timestamp event_time = 2;
  google.protobuf.Timestamp ingestion_timestamp = 11;
  // ...
}
```

---

### 2. Nullable Fields ⚠️

**Current:** Using Proto3 which doesn't have explicit null values

**Issue:** 
- In Proto3, unset fields have default values (0, "", false)
- Cannot distinguish between "not set" and "set to default value"

**Question:** Does Zerobus require `optional` keyword for nullable columns?

**Alternative approach (Proto3 with optional):**
```protobuf
syntax = "proto3";

message OTEvent {
  optional string event_id = 1;
  optional int64 event_time = 2;
  optional double numeric_value = 5;  // Can be null
  optional string string_value = 6;   // Can be null
  optional bool boolean_value = 7;    // Can be null
  // ...
}
```

---

### 3. Complex Types Not Used ✅

We are **NOT** using:
- ❌ Enums (removed from schema)
- ❌ Nested messages
- ❌ Maps
- ❌ oneof (removed from schema)
- ❌ repeated fields (except in batch wrapper)

All fields are basic scalar types.

---

## Questions for Databricks Team

### 1. Timestamp Type Requirements
**Q:** For Delta TIMESTAMP columns, must Protobuf use:
- **Option A:** `int64` (epoch milliseconds) ← Currently using
- **Option B:** `google.protobuf.Timestamp` (with seconds + nanos)
- **Option C:** Either works?

---

### 2. Nullable Column Handling
**Q:** For nullable Delta columns, must Protobuf use:
- **Option A:** Proto3 without `optional` (unset = default value) ← Currently using
- **Option B:** Proto3 with `optional` keyword
- **Option C:** Doesn't matter, Zerobus handles it?

**Example Delta columns that might be null:**
- `numeric_value` - Only set for numeric tags
- `string_value` - Only set for string tags
- `boolean_value` - Only set for boolean tags
- `alarm_state` - Only set if in alarm

---

### 3. Supported Scalar Types
**Q:** Are all these Proto3 scalar types supported by Zerobus?
- ✅ string
- ✅ int32
- ⚠️ int64 (specifically for timestamps)
- ✅ double
- ✅ bool

---

### 4. Type Validation
**Q:** Does Zerobus validate Protobuf types against Delta types at stream creation?
- If yes, does a type mismatch cause `UNIMPLEMENTED` error?
- Or would we get a more specific error like `INVALID_ARGUMENT`?

---

## Alternative Schema (Using google.protobuf.Timestamp)

If int64 is not supported for timestamps:

```protobuf
syntax = "proto3";

import "google/protobuf/timestamp.proto";

message OTEvent {
  string event_id = 1;
  google.protobuf.Timestamp event_time = 2;
  string tag_path = 3;
  string tag_provider = 4;
  optional double numeric_value = 5;
  optional string string_value = 6;
  optional bool boolean_value = 7;
  string quality = 8;
  int32 quality_code = 9;
  string source_system = 10;
  google.protobuf.Timestamp ingestion_timestamp = 11;
  string data_type = 12;
  optional string alarm_state = 13;
  optional int32 alarm_priority = 14;
}
```

---

## SDK Version

**Zerobus SDK:** `com.databricks:zerobus-ingest-sdk:0.1.0`  
**Protobuf Version:** `3.21.12`  
**Java Version:** 17

---

## Current Error

```
com.databricks.zerobus.ZerobusException: Stream failed: UNIMPLEMENTED
Caused by: io.grpc.StatusRuntimeException: UNIMPLEMENTED
```

**Could this be caused by:**
- ❌ Using `int64` instead of `google.protobuf.Timestamp` for timestamps?
- ❌ Not using `optional` for nullable fields?
- ❌ Some other type incompatibility?

---

## Request

Please confirm:
1. **Which Protobuf types are supported** for each Delta type
2. **How to handle timestamps** (int64 vs google.protobuf.Timestamp)
3. **How to handle nulls** (optional vs regular fields)
4. **If type mismatch causes UNIMPLEMENTED** or a different error

This will help us fix the schema to match Zerobus requirements exactly.

