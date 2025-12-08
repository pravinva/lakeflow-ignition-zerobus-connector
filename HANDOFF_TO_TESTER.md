# Handoff to Tester - Ignition Zerobus Connector

## Current Status

**Date:** December 8, 2025  
**Environment:** macOS (e2-demo-field-eng workspace)  
**Status:** ⚠️ **Module build pending - dependencies not yet available**

---

## What's Ready ✅

### 1. Documentation (Complete)
- ✅ `README.md` - Project overview and quick start
- ✅ `architect.md` - Architecture and design
- ✅ `developer.md` - Implementation guide with official SDK references
- ✅ `tester.md` - Your comprehensive test plan
- ✅ `TESTING_SETUP.md` - Docker and simulator setup
- ✅ `QUICKSTART.md` - 15-minute setup guide
- ✅ `setup_databricks_testing.sql` - Delta table creation SQL

### 2. Local Environment (Ready)
- ✅ **Ignition Gateway 8.3.2** installed natively on macOS
  - Location: `/usr/local/ignition/`
  - Access: `http://localhost:8088`
  - Status: Installed, needs initial setup
  
- ✅ **Databricks Workspace** configured
  - Workspace: `e2-demo-field-eng.cloud.databricks.com`
  - User: `pravin.varma@databricks.com`
  - Credentials: `~/.databrickscfg`
  - Target: `main.ignition_ot_test.bronze_events`
  
- ✅ **Build Tools** installed
  - Gradle 9.2.1
  - OpenJDK 17
  - Databricks CLI 0.228.0

### 3. Module Structure (Complete)
- ✅ `build.gradle` - Using official Nexus + Maven Central
- ✅ `src/main/proto/ot_event.proto` - Protobuf schema defined
- ✅ `src/main/resources/module.xml` - Module descriptor
- ✅ Java source files (developer working on implementation)

---

## What's Pending ⏳

### 1. Module Build (Blocked)

**Issue:** Dependencies not available

```
❌ com.databricks:zerobus-sdk-java:0.1.0 - Not found in Maven Central
❌ com.inductiveautomation.ignitionsdk:tag-api:8.3.0 - Not found in Nexus
```

**Root Cause:**
- **Zerobus SDK**: Public Preview - may not be published to Maven Central yet
- **Ignition SDK**: May need different version or Nexus authentication

**Next Actions:**
1. **Contact Databricks Team** for Zerobus SDK access:
   - Verify if SDK is published to Maven Central
   - If not, get artifact directly or private Maven coordinates
   - Alternative: Use snapshot version from Databricks internal repo

2. **Verify Ignition SDK Version**:
   - Check available versions at: https://nexus.inductiveautomation.com
   - May need to use 8.1.x instead of 8.3.0
   - Or configure Nexus authentication if required

### 2. Developer Code (In Progress)

Files being worked on:
- `ConfigPanel.java` - Gateway web UI
- `TagSubscriptionService.java` - Tag monitoring
- `ZerobusClientManager.java` - SDK integration
- `TagEvent.java` - Event data structure
- Unit tests

---

## Testing Setup Instructions

### Step 1: Start Ignition Gateway

```bash
# Start Ignition
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# Access Gateway
open http://localhost:8088
```

**Initial Setup:**
1. Create admin account (username/password)
2. Set Gateway name: `Ignition-Dev-Mac`
3. Skip database setup
4. Complete wizard

### Step 2: Configure Generic Simulator

1. Go to: **Config → OPC UA → Device Connections**
2. Click "Create new Device"
3. Select **Simulators → Generic Simulator**
4. Name: `TestSimulator`
5. Save

**Available Test Tags:**
- `Sine0` - Oscillates -100 to 100 over 60s (temperature sensor)
- `Ramp1` - Counts 0 to 100 over 10s (tank level)
- `Realistic0` - Random walk every 5s (flow rate)
- `RandomInteger1` - Random values every 1s (status codes)
- `WriteableBoolean1` - Manual control flag

### Step 3: Setup Databricks Tables

```bash
# Open SQL Editor
open https://e2-demo-field-eng.cloud.databricks.com/sql/editor

# Run the SQL from:
cat setup_databricks_testing.sql
```

This creates:
- Schema: `main.ignition_ot_test`
- Table: `bronze_events`
- View: `vw_recent_events`

### Step 4: Create OAuth Service Principal

**Option A: UI (Recommended)**
1. Go to Account Console → Service Principals
2. Click "Add Service Principal"
3. Name: `ignition-zerobus-connector`
4. Click "Generate Secret"
5. **Save:**
   - Client ID: `<UUID>`
   - Client Secret: `dapi...`

**Grant Permissions:**
```sql
GRANT MODIFY, SELECT 
ON TABLE main.ignition_ot_test.bronze_events 
TO SERVICE_PRINCIPAL '<client-id>';
```

### Step 5: Build Module (Once Dependencies Available)

```bash
cd /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module

# Build with JDK 17
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home \
./gradlew clean buildModule

# Output location
ls -lh build/modules/zerobus-connector-1.0.0.modl
```

### Step 6: Install Module

1. In Gateway: **Config → System → Modules**
2. Click "Install or Upgrade a Module"
3. Upload: `build/modules/zerobus-connector-1.0.0.modl`
4. Restart Gateway

### Step 7: Configure Module

Navigate to module config page and enter:

| Setting | Value |
|---------|-------|
| Workspace URL | `https://e2-demo-field-eng.cloud.databricks.com` |
| Zerobus Endpoint | `e2-demo-field-eng.zerobus.cloud.databricks.com` |
| OAuth Client ID | `<from Step 4>` |
| OAuth Client Secret | `<from Step 4>` |
| Target Table | `main.ignition_ot_test.bronze_events` |
| Tag Selection | `TestSimulator/Sine0`, `TestSimulator/Ramp1` |
| Batch Size | `100` |
| Batch Interval | `5` seconds |

Click "Test Connection", then "Enable"

### Step 8: Verify Data Flow

**In Databricks:**
```sql
-- Check recent data
SELECT * FROM main.ignition_ot_test.vw_recent_events LIMIT 10;

-- Check ingestion rate
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as events
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 30 MINUTE
GROUP BY 1 ORDER BY 1 DESC;
```

**Expected:** Rows appear within 30 seconds with matching timestamps

---

## Test Plan Execution

### Priority 1: Functional Tests (from tester.md)

**Test Case 1: Basic Connectivity**
- Install module
- Configure credentials
- Click "Test Connection"
- **Expected:** Success message

**Test Case 2: Simple Ingestion**
- Subscribe to 2-3 simulator tags
- Let run 5 minutes
- Query Delta table
- **Expected:** Rows exist, timestamps match

**Test Case 3: Configuration Changes**
- Change batch size from 100 to 500
- Save and apply
- **Expected:** New batch size takes effect without restart

**Test Case 4: Enable/Disable**
- Disable module
- Wait 1 minute (no new data)
- Enable module
- **Expected:** Data flow resumes

### Priority 2: Resilience Tests

**Test Case 5: Network Loss**
- Disconnect network
- Wait 1 minute
- Reconnect
- **Expected:** Module recovers, ingestion resumes

**Test Case 6: Invalid Credentials**
- Enter wrong OAuth secret
- Click "Test Connection"
- **Expected:** Clear error message

**Test Case 7: High-Frequency Load**
- Subscribe to 20-50 tags
- Run for 30 minutes
- Monitor CPU/memory
- **Expected:** Stable performance, no crashes

### Acceptance Criteria

✅ Module installs without errors  
✅ Connection test passes  
✅ Data appears in Delta within 30s  
✅ Timestamps accurate (±2s)  
✅ Quality flags correct  
✅ No errors in Gateway logs  
✅ Ingestion rate stable  
✅ Recovery works after network loss

---

## Troubleshooting

### Ignition Issues

| Issue | Solution |
|-------|----------|
| Gateway won't start | `sudo launchctl load /Library/LaunchDaemons/...` |
| Trial timeout (2hrs) | Click "Restart Trial" or restart Gateway |
| Module won't install | Check Ignition version ≥ 8.1, review logs |
| No simulator tags | Verify Generic Simulator device is enabled |

### Databricks Issues

| Issue | Solution |
|-------|----------|
| Table not found | Run `setup_databricks_testing.sql` |
| Permission denied | Grant MODIFY to service principal |
| Auth failed | Verify client ID/secret are correct |
| No data in table | Check module is enabled, tags subscribed |

### Build Issues

| Issue | Solution |
|-------|----------|
| Dependencies not found | Contact Databricks for Zerobus SDK access |
| Java version error | Use JDK 17: `JAVA_HOME=/opt/homebrew/opt/openjdk@17/...` |
| Compile errors | Developer still working on implementation |

---

## Quick Commands

```bash
# Ignition
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist  # start
sudo launchctl unload /Library/LaunchDaemons/com.inductiveautomation.ignition.plist  # stop
tail -f /usr/local/ignition/logs/wrapper.log  # view logs

# Build
cd /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew buildModule

# Databricks CLI
databricks catalogs list
databricks current-user me
```

---

## Contact Points

### For Zerobus SDK Access
- Contact: Databricks Lakeflow Connect team
- Verify: SDK published to Maven Central?
- Alternative: Internal Maven repo coordinates

### For Ignition SDK Issues
- Check: https://nexus.inductiveautomation.com
- Forum: https://forum.inductiveautomation.com
- Version: Try 8.1.x if 8.3.0 not available

### For Module Implementation
- Developer completing Java source files
- Review: `module/src/main/java/` directory
- Status: Core files drafted, testing/integration pending

---

## Next Steps (Priority Order)

1. ⏳ **Resolve Dependencies** (blocking)
   - Get Zerobus SDK artifact
   - Verify Ignition SDK version
   
2. ⏳ **Complete Implementation** (developer)
   - Finish Java source files
   - Run unit tests
   
3. ✅ **Start Ignition Gateway** (ready now)
   - Complete initial setup
   - Configure simulators
   
4. ✅ **Setup Databricks** (ready now)
   - Create tables
   - Create service principal
   
5. 🎯 **Test Module** (once built)
   - Install `.modl` file
   - Run test cases from `tester.md`
   - Verify end-to-end data flow

---

## Success Indicators

When everything is working:
- ✅ Module builds successfully
- ✅ Module installs in Ignition
- ✅ Connection test passes
- ✅ Data flows from Ignition → Databricks
- ✅ Timestamps match
- ✅ All test cases pass
- ✅ No errors in logs

**You're ready to start testing as soon as the module builds!** 🚀

---

## Files Reference

```
lakeflow-ignition-zerobus-connector/
├── README.md                    - Project overview
├── QUICKSTART.md                - 15-min setup guide
├── HANDOFF_TO_TESTER.md        - This file
├── architect.md                 - Architecture
├── developer.md                 - Implementation guide
├── tester.md                    - YOUR test plan
├── TESTING_SETUP.md            - Docker/simulator guide
├── setup_databricks_testing.sql - Table creation SQL
├── setup_databricks.py          - Helper script
└── module/
    ├── build.gradle             - Build configuration
    ├── src/main/proto/          - Protobuf schemas
    ├── src/main/java/           - Java source (in progress)
    └── src/main/resources/      - Module descriptor
```
