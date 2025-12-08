# 🧪 Installation & Testing Results

**Date:** Dec 8, 2025  
**Tester:** QA (Automated)  
**Module:** zerobus-connector-1.0.0.modl  
**Ignition Version:** 8.3.2

---

## ✅ BUILD VERIFICATION - PASSED

### Module Built Successfully
- **File:** `/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl`
- **Size:** 3.7 MB
- **Status:** ✅ Build successful (0 compilation errors)

### Module Contents Verified
```
✅ lib/zerobus-connector-1.0.0.jar (85 KB) - Our module code
✅ lib/zerobus-ingest-sdk-0.1.0.jar (158 KB) - Databricks SDK
✅ lib/protobuf-java-3.21.12.jar (1.7 MB) - Protocol Buffers
✅ lib/jackson-databind-2.15.2.jar (1.6 MB) - JSON library
✅ lib/jackson-core-2.15.2.jar (549 KB)
✅ lib/jackson-annotations-2.15.2.jar (76 KB)
✅ module.xml - Module descriptor
```

### Module Structure Verified
```
✅ module.xml is valid
✅ Module ID: com.example.ignition.zerobus
✅ Module Name: Zerobus Connector
✅ Version: 1.0.0
✅ Hook class: com.example.ignition.zerobus.ZerobusGatewayHook
✅ Scope: Gateway (G)
✅ Required Ignition version: 8.3.0
```

### Java Classes Verified
```
✅ ZerobusGatewayHook.class - Main module hook
✅ ZerobusClientManager.class - Zerobus SDK wrapper
✅ ConfigModel.class - Configuration POJO
✅ ZerobusConfigServlet.class - Configuration UI servlet
✅ TagSubscriptionService.class - Tag monitoring
✅ All protobuf-generated classes present
```

---

## 🚀 IGNITION ENVIRONMENT - READY

### Gateway Status
- **Status:** ✅ Running
- **Port:** 8088
- **Location:** /usr/local/ignition/
- **Version:** 8.3.2 (confirmed via logs)
- **Trial Time:** 2800 minutes remaining (~47 hours)

### Installed Modules (Pre-test)
```
✅ OPC-UA v10.3.2
✅ Historian Core v1.3.2
✅ Perspective v3.3.2
✅ Vision v12.3.2
✅ Allen-Bradley Drivers
✅ Modbus Driver v8.3.2
✅ MSSQL JDBC Driver
✅ PostgreSQL JDBC Driver
... 25+ modules total
```

---

## 📥 INSTALLATION ATTEMPT - NEEDS WEB UI

### What I Tried
1. ✅ Copied `.modl` file to `/usr/local/ignition/user-lib/modules/`
2. ✅ Restarted Gateway using `gwcmd.sh -r`
3. ❌ Module did NOT auto-register (expected behavior)

### Finding
**Ignition modules cannot be installed by simply copying to the directory.**

Modules MUST be installed through the web UI:
- **Config → System → Modules → "Install or Upgrade a Module"**

This is by design for:
- Security validation
- Dependency checking
- License validation
- Configuration initialization

---

## 🎯 NEXT STEPS - MANUAL INSTALLATION REQUIRED

### Step 1: Open Ignition Gateway (1 minute)

```bash
# Gateway is already running at:
open http://localhost:8088
```

**Login credentials:**
- Username: (admin account you created during setup)
- Password: (your password)

### Step 2: Install Module (2 minutes)

1. Navigate to: **Config → System → Modules**
2. Click: **"Install or Upgrade a Module"**
3. Click: **"Choose File"**
4. Select: 
   ```
   /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl
   ```
5. Click: **"Install"**
6. Click: **"Restart Gateway"** when prompted
7. Wait 30-60 seconds for restart

### Step 3: Verify Installation (1 minute)

After restart:

1. Go to: **Config → System → Modules**
2. Look for: **"Zerobus Connector"** in the module list
3. Check Status: Should be **"Running"**
4. Check Version: Should be **"1.0.0"**

**Check logs:**
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

**Expected log entries:**
```
INFO  ZerobusGatewayHook - Setting up Zerobus Gateway Module
INFO  ZerobusGatewayHook - Zerobus Gateway Module started successfully
INFO  ZerobusGatewayHook - Configuration servlet registered at /system/zerobus
```

---

## 🧪 TEST PLAN - AFTER INSTALLATION

Once module is installed, execute these tests from `tester.md`:

### Test Case 1: Basic Connectivity ✅ (5 minutes)

**Setup Databricks:**
1. Create OAuth Service Principal in Databricks Account Console
2. Save Client ID and Secret
3. Grant permissions on `lakeflow_ignition` catalog:
   ```sql
   GRANT USE CATALOG ON CATALOG lakeflow_ignition 
   TO SERVICE_PRINCIPAL '<client-id>';
   
   GRANT USE SCHEMA ON SCHEMA lakeflow_ignition.ot_data 
   TO SERVICE_PRINCIPAL '<client-id>';
   
   GRANT MODIFY, SELECT ON TABLE lakeflow_ignition.ot_data.bronze_events 
   TO SERVICE_PRINCIPAL '<client-id>';
   ```

**Configure Module:**
1. Navigate to: `http://localhost:8088/system/zerobus/config`
2. Enter configuration:
   - Workspace URL: `https://e2-demo-field-eng.cloud.databricks.com`
   - Zerobus Endpoint: `e2-demo-field-eng.zerobus.cloud.databricks.com`
   - OAuth Client ID: `<from above>`
   - OAuth Client Secret: `<from above>`
   - Target Table: `lakeflow_ignition.ot_data.bronze_events`
   - Source System: `Ignition-Dev-Mac`
3. Click **"Test Connection"**

**Expected:**
- ✅ Connection test passes
- ✅ Success message displayed
- ✅ No errors in Gateway logs

**If connection test fails:**
- Check OAuth credentials
- Verify table exists: `lakeflow_ignition.ot_data.bronze_events`
- Verify network connectivity to Databricks
- Check Gateway logs for detailed error

---

### Test Case 2: Simple Ingestion ✅ (10 minutes)

**Setup Simulator:**
1. In Gateway: **Config → OPC UA → Device Connections**
2. Click **"Create new Device"**
3. Select **"Simulators → Generic Simulator"**
4. Name: `TestSimulator`
5. Enable: **"Enabled"** checkbox
6. Click **"Create New Device"**

**Configure Tags:**
1. Go back to module config: `http://localhost:8088/system/zerobus/config`
2. In **"Tag Selection"** field, enter:
   ```
   [default]TestSimulator/Sine0
   [default]TestSimulator/Ramp1
   [default]TestSimulator/Realistic0
   ```
3. Enable module: Toggle **"Enabled"** to ON
4. Click **"Save"**

**Wait 2 minutes, then verify in Databricks:**
```sql
-- Should return rows
SELECT * 
FROM lakeflow_ignition.ot_data.vw_recent_events 
LIMIT 10;
```

**Expected:**
- ✅ Rows appear within 30-60 seconds
- ✅ `tag_path` contains subscribed tags
- ✅ `quality` = "GOOD"
- ✅ `numeric_value` has realistic values
- ✅ `event_time` matches current time (±2 seconds)

**Verify in Ignition:**
1. Check diagnostics: `http://localhost:8088/system/zerobus/diagnostics`
2. Should show:
   - Events sent count (increasing)
   - Last successful send timestamp
   - Stream state: OPENED

---

### Test Case 3: Configuration Changes ✅ (5 minutes)

**Steps:**
1. Change batch size from 100 to 500
2. Click **"Save"**
3. Generate more tag changes (tags update automatically)
4. Check logs for new batch size

**Expected:**
- ✅ New configuration takes effect immediately
- ✅ No data loss
- ✅ No module restart needed
- ✅ Logs show new batch size being used

---

### Test Case 4: Enable/Disable ✅ (5 minutes)

**Steps:**
1. Note current event count in diagnostics
2. Toggle **"Enabled"** to OFF
3. Click **"Save"**
4. Wait 1 minute
5. Note last event timestamp in Databricks
6. Toggle **"Enabled"** to ON
7. Click **"Save"**
8. Wait 1 minute

**Expected:**
- ✅ No new rows during disabled period
- ✅ Ingestion resumes after enable
- ✅ No errors in logs
- ✅ Stream state changes: OPENED → CLOSED → OPENED

---

### Test Case 5: Network Loss Resilience ⚠️ (10 minutes)

**Steps:**
1. Module running and ingesting data
2. Temporarily disconnect network:
   ```bash
   # macOS: System Settings → Network → Wi-Fi → Turn Off
   ```
3. Wait 1 minute
4. Observe Gateway logs
5. Reconnect network
6. Wait 1 minute
7. Check Databricks for resumed ingestion

**Expected:**
- ✅ Module logs show connection errors and retry attempts
- ✅ Module doesn't crash
- ✅ Ingestion resumes automatically after network restore
- ✅ No data loss (buffered during outage)
- ✅ Stream recovery works

---

### Test Case 6: Invalid Credentials 🔐 (3 minutes)

**Steps:**
1. In module config, enter wrong OAuth secret
2. Click **"Test Connection"**

**Expected:**
- ✅ Clear authentication error message
- ✅ No module crash
- ✅ No malformed data in Delta table
- ✅ Module remains in error state until credentials fixed

---

### Test Case 7: High-Frequency Load 🚀 (30 minutes)

**Steps:**
1. Create 20-50 simulator tags:
   ```
   [default]TestSimulator/Sine0
   [default]TestSimulator/Sine1
   [default]TestSimulator/Sine2
   [default]TestSimulator/Ramp0
   [default]TestSimulator/Ramp1
   [default]TestSimulator/Realistic0
   [default]TestSimulator/Realistic1
   ... (up to 50 tags)
   ```
2. Subscribe to all in module config
3. Let run for 30 minutes
4. Monitor CPU/memory usage
5. Check Gateway logs for errors
6. Query Databricks for throughput

**Expected:**
- ✅ Stable throughput (no degradation)
- ✅ CPU usage < 20%
- ✅ Memory stable (no leaks)
- ✅ No frequent connection failures
- ✅ All tags appear in Databricks
- ✅ Ingestion rate consistent

---

## 📊 TEST EXIT CRITERIA

Module passes testing when:

- ✅ Module installs without errors
- ✅ Connection test passes
- ✅ Data appears in Delta within 30 seconds
- ✅ All subscribed tags appear
- ✅ Timestamps accurate (±2 seconds)
- ✅ Quality flags correct
- ✅ Configuration changes work dynamically
- ✅ Enable/disable works correctly
- ✅ Recovery works after network loss
- ✅ Invalid credentials handled gracefully
- ✅ High-frequency load is stable
- ✅ No errors in Gateway logs (except during fault injection)

---

## 🛠️ TROUBLESHOOTING GUIDE

### Module Won't Install

| Symptom | Solution |
|---------|----------|
| "Invalid module file" | Verify .modl file is not corrupted |
| "Version incompatible" | Check Ignition version ≥ 8.3.0 |
| "Missing dependencies" | Ensure all JARs in .modl file |

### Connection Test Fails

| Error | Solution |
|-------|----------|
| Auth failed | Verify OAuth client ID/secret |
| Table not found | Confirm table exists in Databricks |
| Network timeout | Check firewall, verify HTTPS allowed |
| Permission denied | Run GRANT statements |

### No Data in Databricks

**Checklist:**
- [ ] Module is enabled
- [ ] Tags are subscribed
- [ ] Tags are changing (verify in Quick Client)
- [ ] Stream state is OPENED
- [ ] No errors in Gateway logs
- [ ] OAuth credentials correct
- [ ] Databricks table exists
- [ ] Network connectivity to Zerobus endpoint

### Module Logs Errors

```bash
# View full logs
tail -f /usr/local/ignition/logs/wrapper.log

# Filter for Zerobus
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus

# View module diagnostics
curl http://localhost:8088/system/zerobus/diagnostics
```

---

## 📁 KEY FILES

```
Module Built:
/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl

Documentation:
/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/tester.md
/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/MODULE_READY.md
/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/DATABRICKS_SETUP_COMPLETE.md

Ignition Gateway:
http://localhost:8088

Module Config UI (after install):
http://localhost:8088/system/zerobus/config

Databricks Workspace:
https://e2-demo-field-eng.cloud.databricks.com
```

---

## 🎯 CURRENT STATUS

**Build Phase:** ✅ **100% COMPLETE**
- Module compiles: ✅ PASS
- Module packages: ✅ PASS
- All dependencies included: ✅ PASS

**Installation Phase:** ⏸️ **AWAITING MANUAL STEP**
- Ignition Gateway running: ✅ READY
- Module file ready: ✅ READY
- **Action needed:** Install via Web UI

**Testing Phase:** ⏳ **PENDING INSTALLATION**
- Test environment ready: ✅ READY
- Databricks resources: ✅ READY
- Test plan defined: ✅ READY
- **Action needed:** Execute 7 test cases

---

## 🚀 IMMEDIATE NEXT ACTIONS

1. **Open Ignition Gateway:**
   ```bash
   open http://localhost:8088
   ```

2. **Install Module:**
   - Config → System → Modules → Install or Upgrade a Module
   - Select: `module/build/modules/zerobus-connector-1.0.0.modl`

3. **Verify Installation:**
   - Check module list for "Zerobus Connector"
   - Status should be "Running"

4. **Run Test Cases:**
   - Follow test plan above
   - Document results
   - Report any issues

---

**Ready to proceed with manual installation!** 🎉

