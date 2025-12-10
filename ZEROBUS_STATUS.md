# Zerobus Connection Status

## Current Status

✅ **Event Streams → Module**: Working
- `zerobus_automation` Event Stream is enabled
- Events are being sent to module REST endpoint
- Module receives POST requests successfully

⚠️ **Module → Databricks**: Not Connected
- Error: `UNIMPLEMENTED` from Zerobus SDK
- Stream creation fails

## Configuration Applied

```json
{
  "enabled": true,
  "workspaceUrl": "https://e2-demo-field-eng.cloud.databricks.com",
  "zerobusEndpoint": "https://e2-demo-field-eng.cloud.databricks.com",
  "oauthClientId": "YOUR_SERVICE_PRINCIPAL_CLIENT_ID",
  "catalogName": "ignition_demo",
  "schemaName": "scada_data",
  "tableName": "tag_events",
  "targetTable": "ignition_demo.scada_data.tag_events"
}
```

## Possible Causes of UNIMPLEMENTED Error

### 1. Zerobus Not Enabled on Workspace
**Check:**
```sql
-- In Databricks SQL
SHOW TBLPROPERTIES ignition_demo.scada_data.tag_events;
```

Look for `delta.enableZerobus` = `true`

**Fix:**
```sql
ALTER TABLE ignition_demo.scada_data.tag_events 
SET TBLPROPERTIES ('delta.enableZerobus' = 'true');
```

### 2. Service Principal Permissions
**Verify the Service Principal has:**
- `USE CATALOG` on `ignition_demo`
- `USE SCHEMA` on `ignition_demo.scada_data`
- `MODIFY` on `ignition_demo.scada_data.tag_events`
- `SELECT` on `ignition_demo.scada_data.tag_events`

**Check:**
```sql
SHOW GRANTS ON TABLE ignition_demo.scada_data.tag_events;
```

### 3. Workspace Zerobus Feature Flag
Zerobus is a preview feature and might need to be enabled at the workspace level.

**Contact:** Databricks support or your account team to verify Zerobus is enabled.

### 4. OAuth Token Issues
**Test OAuth manually:**
```bash
curl -X POST https://e2-demo-field-eng.cloud.databricks.com/oidc/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=all-apis"
```

Should return an access token.

## What's Working

1. **Event Streams**: Fully functional
   - `ZerobusTagStream`: Sine + Realistic tags
   - `zerobus_automation`: Ramp tags
   
2. **Module REST API**: Receiving events
   - Endpoint: `http://localhost:8088/system/zerobus/ingest/batch`
   - Events are queued correctly

3. **Module Configuration**: Saved
   - Can be verified: `curl http://localhost:8088/system/zerobus/config`

## Next Steps

1. **Verify Zerobus is enabled** on the Databricks workspace
2. **Check table properties** for `delta.enableZerobus`
3. **Verify Service Principal permissions**
4. **Test OAuth token** acquisition manually
5. Once Zerobus connects, data will flow automatically

## Alternative: Use Standard Databricks API

If Zerobus isn't available, the module can be modified to use standard Databricks SQL API:

```
POST https://e2-demo-field-eng.cloud.databricks.com/api/2.0/sql/statements
```

This would require code changes but would work on any workspace.

## Testing Without Databricks

To test the full flow without Databricks:
1. Events are flowing from tags → Event Streams
2. Event Streams POST to module REST endpoint
3. Module queues events successfully
4. Only the Databricks send step is failing

The integration is 90% complete - just need Zerobus enablement!

