# 🎉 MODULE BUILT SUCCESSFULLY!

**Module:** `zerobus-connector-1.0.0.modl`  
**Size:** 3.7 MB  
**Status:** ✅ **READY FOR INSTALLATION AND TESTING**

---

## 📦 Built Module

**Location:**
```
/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl
```

**Contents:**
- ✅ `zerobus-connector-1.0.0.jar` - Your module code
- ✅ `zerobus-ingest-sdk-0.1.0.jar` - Databricks Zerobus SDK
- ✅ `protobuf-java-3.21.12.jar` - Protocol Buffers
- ✅ `jackson-databind-2.15.2.jar` - JSON serialization
- ✅ `module.xml` - Module descriptor

---

## 🚀 INSTALLATION STEPS

### Step 1: Start Ignition Gateway

```bash
# Start Ignition
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# Wait 30 seconds for startup

# Access Gateway
open http://localhost:8088
```

**Initial Setup (if first time):**
1. Create admin account
2. Set Gateway name: `Ignition-Dev-Mac`
3. Complete wizard

### Step 2: Install the Module

1. Go to: **Config → System → Modules**
2. Click **"Install or Upgrade a Module"**
3. Click **"Choose File"**
4. Select: `module/build/modules/zerobus-connector-1.0.0.modl`
5. Click **"Install"**
6. Click **"Restart Gateway"** when prompted
7. Wait 30-60 seconds for restart

### Step 3: Verify Installation

After restart:
1. Go to **Config → System → Modules**
2. Look for **"Zerobus Connector"** in the list
3. Status should be: **"Running"**
4. Version: **1.0.0**

Check logs:
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

Look for:
```
INFO  ZerobusGatewayHook - Setting up Zerobus Gateway Module
INFO  ZerobusGatewayHook - Zerobus Gateway Module started successfully
INFO  ZerobusGatewayHook - Configuration servlet registered at /system/zerobus
```

---

## 🔧 CONFIGURE THE MODULE

### Step 1: Create OAuth Service Principal in Databricks

1. Go to Account Console → **Service Principals**
2. Click **"Add Service Principal"**
3. Name: `ignition-zerobus-connector`
4. Click **"Generate Secret"**
5. **SAVE THESE:**
   - Client ID: `<UUID>`
   - Client Secret: `dapi...`

### Step 2: Grant Permissions

In Databricks SQL Editor:

```sql
-- Grant catalog access
GRANT USE CATALOG ON CATALOG lakeflow_ignition 
TO SERVICE_PRINCIPAL '<your-client-id>';

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA lakeflow_ignition.ot_data 
TO SERVICE_PRINCIPAL '<your-client-id>';

-- Grant table access
GRANT MODIFY, SELECT ON TABLE lakeflow_ignition.ot_data.bronze_events 
TO SERVICE_PRINCIPAL '<your-client-id>';
```

### Step 3: Configure Generic Simulator

1. In Ignition Gateway: **Config → OPC UA → Device Connections**
2. Click **"Create new Device"**
3. Select **"Simulators → Generic Simulator"**
4. Name: `TestSimulator`
5. Click **"Create New Device"**

**Available test tags:**
- `Sine0` - Temperature (-100 to 100°C, 60s cycle)
- `Sine1` - Pressure (-10 to 10 PSI, 10s cycle)
- `Ramp1` - Tank level (0-100%, 10s cycle)
- `Realistic0` - Flow rate with drift (5s updates)
- `RandomInteger1` - Status codes (1s updates)

### Step 4: Configure Zerobus Module

Navigate to the module configuration:
```
http://localhost:8088/system/zerobus/config
```

Or find it in Gateway Config menu.

**Enter Configuration:**

| Setting | Value |
|---------|-------|
| Workspace URL | `https://e2-demo-field-eng.cloud.databricks.com` |
| Zerobus Endpoint | `e2-demo-field-eng.zerobus.cloud.databricks.com` |
| OAuth Client ID | `<from Step 1>` |
| OAuth Client Secret | `<from Step 1>` |
| Target Table | `lakeflow_ignition.ot_data.bronze_events` |
| Source System | `Ignition-Dev-Mac` |
| Batch Size | `100` |
| Batch Interval (seconds) | `5` |
| Enable Stream Recovery | ✅ Yes |
| Max Inflight Records | `50000` |

**Tag Selection:**
```
[default]TestSimulator/Sine0
[default]TestSimulator/Ramp1
[default]TestSimulator/Realistic0
```

### Step 5: Test Connection

1. Click **"Test Connection"** button
2. Should see: **✅ "Connection successful!"**
3. If error: Check credentials, table name, network

### Step 6: Enable Module

1. Toggle **"Enabled"** switch to ON
2. Click **"Save"**
3. Module should start streaming data

---

## ✅ VERIFY DATA FLOW

### In Ignition (1 minute)

Check module diagnostics:
```
http://localhost:8088/system/zerobus/diagnostics
```

Should show:
- Events sent count (increasing)
- Last successful send timestamp
- Stream state: OPENED

Check Gateway logs:
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

Look for:
```
INFO  ZerobusClientManager - Stream created successfully
INFO  ZerobusClientManager - Records acknowledged up to offset: XXX
```

### In Databricks (30 seconds)

Open SQL Editor:
```
https://e2-demo-field-eng.cloud.databricks.com/sql/editor
```

**Query 1: Check recent events**
```sql
SELECT * 
FROM lakeflow_ignition.ot_data.vw_recent_events 
LIMIT 10;
```

**Expected:**
- ✅ Rows appear within 30-60 seconds
- ✅ `event_time` matches current time (within seconds)
- ✅ `tag_path` shows your subscribed tags
- ✅ `quality` = "GOOD"
- ✅ `numeric_value` has simulator values

**Query 2: Check ingestion rate**
```sql
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as events,
  COUNT(DISTINCT tag_path) as unique_tags
FROM lakeflow_ignition.ot_data.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 30 MINUTE
GROUP BY 1
ORDER BY 1 DESC;
```

**Expected:**
- ✅ Rows every minute
- ✅ Event counts consistent with batch interval
- ✅ All subscribed tags present

---

## 🧪 RUN TEST CASES (from tester.md)

Now execute all 7 test cases!

### Test Case 1: Basic Connectivity ✅

**Already done!** Connection test passed.

### Test Case 2: Simple Ingestion

**Steps:**
1. Module configured with 3 simulator tags
2. Let run for 5 minutes
3. Query Delta table

**Expected:**
- Rows exist for Sine0, Ramp1, Realistic0
- Timestamps match
- Values match simulator output

**Verify:**
```sql
SELECT 
  tag_path,
  COUNT(*) as events,
  MIN(event_time) as first_event,
  MAX(event_time) as last_event
FROM lakeflow_ignition.ot_data.bronze_events
GROUP BY tag_path;
```

### Test Case 3: Configuration Changes

**Steps:**
1. Change batch size from 100 to 500
2. Save configuration
3. Generate more tag changes
4. Observe logs

**Expected:**
- New batch size takes effect
- No data loss
- No module restart needed

### Test Case 4: Enable/Disable

**Steps:**
1. Disable module
2. Wait 1 minute (note last event time)
3. Enable module
4. Generate tag changes

**Expected:**
- No new rows during disabled period
- Ingestion resumes after enable

### Test Case 5: Network Loss

**Steps:**
1. Disconnect network temporarily
2. Wait 1 minute
3. Reconnect network

**Expected:**
- Module logs show connection errors and retries
- Module doesn't crash
- Ingestion resumes on restore

### Test Case 6: Invalid Credentials

**Steps:**
1. Enter wrong OAuth secret in config
2. Click "Test Connection"

**Expected:**
- Clear auth error message
- No malformed data in Delta
- Module remains running but in error state

### Test Case 7: High-Frequency Load

**Steps:**
1. Subscribe to 20-50 tags (multiple Sine, Ramp, Realistic)
2. Run for 30 minutes
3. Monitor CPU/memory

**Expected:**
- Stable throughput
- No runaway resource usage
- No frequent failures

---

## 📊 SUCCESS CRITERIA

Module is working correctly when:

- ✅ Module installs without errors
- ✅ Connection test passes
- ✅ Data appears in Delta within 30 seconds
- ✅ Timestamps accurate (±2 seconds)
- ✅ Quality flags correct (GOOD for simulators)
- ✅ All subscribed tags appear
- ✅ No errors in Gateway logs
- ✅ Ingestion rate stable
- ✅ Recovery works after network loss
- ✅ All 7 test cases pass

---

## 🛠️ TROUBLESHOOTING

### Module Won't Install

**Solution:**
- Check Ignition version ≥ 8.1.0
- Review Gateway logs: Status → Logs → Wrapper Log
- Verify .modl file is not corrupted

### Connection Test Fails

| Error | Solution |
|-------|----------|
| Auth failed | Verify OAuth client ID/secret |
| Table not found | Verify: `lakeflow_ignition.ot_data.bronze_events` exists |
| Network error | Check firewall, verify outbound HTTPS allowed |
| Permission denied | Run GRANT statements from Step 2 |

### No Data in Delta

**Checklist:**
- [ ] Module is enabled
- [ ] Tags are subscribed
- [ ] Tags are actually changing (check in Quick Client)
- [ ] Stream state is OPENED (check diagnostics)
- [ ] No errors in Gateway logs
- [ ] OAuth credentials correct

### Ignition Trial Timeout

**After 2 hours:**
- Gateway shows "Trial has expired"
- Click **"Restart Trial"** button
- Or restart Gateway:
  ```bash
  sudo launchctl unload /Library/LaunchDaemons/com.inductiveautomation.ignition.plist
  sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist
  ```

---

## 📁 KEY FILES

```
module/build/modules/zerobus-connector-1.0.0.modl  ← Install this!
tester.md                                          ← Your test plan
DATABRICKS_SETUP_COMPLETE.md                      ← Databricks info
MODULE_READY.md                                    ← This file
```

---

## 🎯 QUICK START COMMANDS

```bash
# 1. Build module (already done!)
cd module
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew buildModule

# 2. Start Ignition
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# 3. Access Gateway
open http://localhost:8088

# 4. View Ignition logs
tail -f /usr/local/ignition/logs/wrapper.log

# 5. Query Databricks
open https://e2-demo-field-eng.cloud.databricks.com/sql/editor
# Run: SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events LIMIT 10;
```

---

## 🏆 ACHIEVEMENT UNLOCKED!

✅ Complete documentation  
✅ Build system configured  
✅ All dependencies resolved  
✅ Module compiles 100%  
✅ Module built successfully  
✅ Databricks catalog & tables created  
✅ Testing environment ready  
✅ Test plan complete  

**YOU ARE READY TO TEST!** 🚀🚀🚀

---

**Next:** Install the module in Ignition and run through all 7 test cases from `tester.md`!

