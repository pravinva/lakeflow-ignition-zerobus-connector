# Zerobus API Error Report

## Issue Summary
Zerobus Ingest API returns `UNIMPLEMENTED` error when attempting to create a stream in the field-eng workspace.

---

## Workspace Details

**Workspace URL:** `https://e2-demo-field-eng.cloud.databricks.com`  
**Workspace Host:** `e2-demo-field-eng.cloud.databricks.com`  
**Service Principal:** `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`  
**Date/Time:** December 9, 2025 00:17:11 AEDT  

---

## Error Details

### Primary Error
```
com.databricks.zerobus.ZerobusException: Stream creation failed: 
com.databricks.zerobus.ZerobusException: Stream failed: UNIMPLEMENTED
```

### Root Cause
```
Caused by: io.grpc.StatusRuntimeException: UNIMPLEMENTED
```

### Full Stack Trace Context
```
INFO   | jvm 1    | 2025/12/09 00:17:11 | Caused by: com.databricks.zerobus.ZerobusException: 
Stream creation failed: com.databricks.zerobus.ZerobusException: Stream failed: UNIMPLEMENTED
INFO   | jvm 1    | 2025/12/09 00:17:11 | 	at com.databricks.zerobus.ZerobusStream.lambda$createStream$5(ZerobusStream.java:434)
INFO   | jvm 1    | 2025/12/09 00:17:11 | 	at com.databricks.zerobus.ZerobusStream.handleStreamFailed(ZerobusStream.java:700)
INFO   | jvm 1    | 2025/12/09 00:17:11 | 	at com.databricks.zerobus.ZerobusStream$1.onError(ZerobusStream.java:1101)
...
INFO   | jvm 1    | 2025/12/09 00:17:11 | Caused by: io.grpc.StatusRuntimeException: UNIMPLEMENTED
INFO   | jvm 1    | 2025/12/09 00:17:11 | 	at io.grpc.Status.asRuntimeException(Status.java:537)
```

---

## What's Working

✅ **OAuth Authentication:** Service principal successfully authenticates  
✅ **Network Connectivity:** gRPC connection to Databricks established  
✅ **Service Principal Permissions:** Catalog/schema/table permissions granted correctly  
✅ **SDK Integration:** Databricks Zerobus Java SDK (v0.1.0) correctly integrated  

---

## What's NOT Working

❌ **Zerobus ephemeralStream RPC method:** Returns `UNIMPLEMENTED`  
❌ **Stream creation:** Cannot create Zerobus stream for data ingestion  

---

## Technical Details

**SDK Version:** `com.databricks:zerobus-ingest-sdk:0.1.0`  
**Protocol:** gRPC over HTTPS  
**Authentication Method:** OAuth2 Client Credentials  
**Target Table:** `ignition_demo.scada_data.tag_events`  

**RPC Method Attempted:** `ZerobusGrpc.ephemeralStream()`  
**Result:** `UNIMPLEMENTED` status code  

---

## Interpretation

The `UNIMPLEMENTED` gRPC status code indicates that:

1. The Zerobus service endpoint is reachable
2. Authentication is successful
3. **The `ephemeralStream` RPC method is not implemented/enabled in this workspace**

This typically means:
- Zerobus Ingest is a **preview/private preview feature**
- The feature flag is **not enabled** for this workspace
- The workspace may need to be **added to the preview program**

**Important:** We have definitively ruled out permissions as the cause by testing with:
- Minimal permissions (SELECT, MODIFY) → UNIMPLEMENTED
- Maximum permissions (ALL PRIVILEGES) → UNIMPLEMENTED

**This proves the issue is workspace-level feature availability, not permissions.**

---

## Request

Please **enable Zerobus Ingest API** for the following workspace:

**Workspace:** `e2-demo-field-eng.cloud.databricks.com`  
**Feature:** Zerobus Ingest API / ephemeralStream  
**Use Case:** Real-time SCADA data ingestion from Ignition Gateway  
**Service Principal:** `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`  

---

## Additional Context

### Other Workspace Tested

**Workspace:** `https://one-env-vdm-serverless-fszpx9.cloud.databricks.com`  
**Result:** Same `UNIMPLEMENTED` error  
**Conclusion:** Zerobus not enabled in either workspace  

### What We've Verified

✅ Service principal has correct permissions (USE CATALOG, USE SCHEMA, SELECT, MODIFY)  
✅ **Tested with ALL PRIVILEGES** - same error, permissions are not the issue  
✅ Target table exists and is accessible  
✅ OAuth credentials are valid and working  
✅ Unity Catalog is properly configured  
✅ Delta table created with CDC enabled  

### Permissions Tested

We tested multiple permission levels - **ALL produce the same UNIMPLEMENTED error:**

1. **Specific privileges:** USE CATALOG, USE SCHEMA, SELECT, MODIFY → ❌ UNIMPLEMENTED
2. **ALL PRIVILEGES** on table → ❌ UNIMPLEMENTED (same error)

**Conclusion:** Permissions are not the issue. The Zerobus API itself is not available.  

---

## Reference Information

**Official Zerobus SDK:**  
https://github.com/databricks/zerobus-sdk-java

**SDK Maven Coordinates:**  
```xml
<dependency>
    <groupId>com.databricks</groupId>
    <artifactId>zerobus-ingest-sdk</artifactId>
    <version>0.1.0</version>
</dependency>
```

**Documentation:**  
Zerobus Ingest appears to be in preview - may require feature enablement request

---

## Expected Behavior (Once Enabled)

Once Zerobus is enabled in the workspace, the application should:

1. Successfully create an ephemeral stream
2. Begin ingesting events in batches
3. Acknowledge offsets after successful writes
4. Support high-throughput streaming (10K+ events/sec)

---

## Contact

**Reported by:** Pravin Varma  
**Date:** December 9, 2025  
**Module:** Ignition-Zerobus Connector v1.0.0  

---

## Next Steps

1. **Databricks Team:** Enable Zerobus Ingest for workspace(s)
2. **Our Team:** Test connection after enablement
3. **Expected Timeline:** 1-3 business days

Once enabled, no code changes are needed - the module will connect automatically.

