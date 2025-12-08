# Quick Start Guide - Ignition Zerobus Connector Testing

## Your Environment

**Databricks Workspace:**
- URL: `https://e2-demo-field-eng.cloud.databricks.com`
- User: `pravin.varma@databricks.com`
- Credentials: `~/.databrickscfg`

**Ignition Gateway:**
- Version: 8.3.2 (macOS native install)
- URL: `http://localhost:8088`
- Location: `/usr/local/ignition/`

**Target Table:**
- Full name: `main.ignition_ot_test.bronze_events`
- Catalog: `main`
- Schema: `ignition_ot_test`

**Zerobus Endpoint:**
- `e2-demo-field-eng.zerobus.cloud.databricks.com`

---

## Step-by-Step Setup (15 minutes)

### Step 1: Set Up Databricks (5 min)

#### 1.1 Create Tables in Databricks

Open SQL Editor in your workspace:
```
https://e2-demo-field-eng.cloud.databricks.com/sql/editor
```

Copy and run the SQL from:
```bash
cat setup_databricks_testing.sql
```

This creates:
- ✅ Schema: `main.ignition_ot_test`
- ✅ Table: `bronze_events` (partitioned by date)
- ✅ View: `vw_recent_events` (last hour of data)

#### 1.2 Create OAuth Service Principal

**Option A: Using Databricks UI**

1. Go to: Account Console → User Management → Service Principals
2. Click "Add Service Principal"
3. Name: `ignition-zerobus-connector`
4. Click "Generate Secret"
5. **Save these:**
   - Client ID (UUID format)
   - Client Secret (starts with `dapi...`)

**Option B: Using CLI** (if you have account admin access)

```bash
# Create service principal
databricks service-principals create \
  --display-name "ignition-zerobus-connector"

# Generate OAuth secret
databricks service-principals create-secret \
  --service-principal-id <UUID-from-above>
```

#### 1.3 Grant Table Permissions

```sql
-- In Databricks SQL Editor
GRANT MODIFY, SELECT 
ON TABLE main.ignition_ot_test.bronze_events 
TO SERVICE_PRINCIPAL '<your-client-id>';
```

### Step 2: Set Up Ignition Gateway (5 min)

#### 2.1 Start Ignition

If not already running:
```bash
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist
```

Access Gateway:
```
http://localhost:8088
```

#### 2.2 Complete Initial Setup Wizard

1. Create admin account
2. Set Gateway name: `Ignition-Dev-Mac`
3. Skip database setup (optional)
4. Complete wizard

#### 2.3 Configure Generic Simulator

1. Go to: **Config → OPC UA → Device Connections**
2. Click "Create new Device"
3. Select **Simulators → Generic Simulator**
4. Name: `TestSimulator`
5. Click "Create New Device"

**Verify:** You should now see tags in Designer or Quick Client.

#### 2.4 Recommended Test Tags

| Tag | Type | Behavior | Good For Testing |
|-----|------|----------|------------------|
| `Sine0` | Double | -100 to 100, 60s period | Temperature sensor |
| `Sine1` | Double | -10 to 10, 10s period | Pressure variation |
| `Ramp1` | Integer | 0 to 100, 10s period | Tank level % |
| `Realistic0` | Double | Random walk, 5s updates | Flow rate |
| `RandomInteger1` | Integer | Random, 1s updates | Status codes |
| `WriteableBoolean1` | Boolean | Manual control | Start/Stop flags |

### Step 3: Build and Install Module (3 min)

#### 3.1 Build the Module

```bash
cd /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module

# Build the .modl file
./gradlew buildModule

# Output location
ls -lh build/modules/zerobus-connector-1.0.0.modl
```

#### 3.2 Install Module in Ignition

1. In Gateway Config: **System → Modules**
2. Click "Install or Upgrade a Module"
3. Upload: `build/modules/zerobus-connector-1.0.0.modl`
4. Click "Install"
5. **Restart Gateway** when prompted (takes ~30 seconds)

#### 3.3 Verify Module Loaded

1. Go to **System → Modules**
2. Look for "Zerobus Connector" in the list
3. Status should be "Running"
4. Check **Status → Logs → Wrapper Log** for startup messages

### Step 4: Configure Zerobus Connection (2 min)

#### 4.1 Open Module Configuration

Navigate to the Zerobus module config page (exact location depends on module implementation).

#### 4.2 Enter Configuration

| Setting | Value |
|---------|-------|
| Workspace URL | `https://e2-demo-field-eng.cloud.databricks.com` |
| Zerobus Endpoint | `e2-demo-field-eng.zerobus.cloud.databricks.com` |
| OAuth Client ID | `<from Step 1.2>` |
| OAuth Client Secret | `<from Step 1.2>` |
| Target Table | `main.ignition_ot_test.bronze_events` |
| Batch Size | `100` (start small) |
| Batch Interval | `5` seconds |
| Max Inflight Records | `50000` |
| Enable Recovery | ✅ Yes |

#### 4.3 Test Connection

1. Click "Test Connection" button
2. Should see: "✅ Connection successful"
3. If error: Check credentials, table name, network connectivity

#### 4.4 Subscribe to Tags

1. In tag subscription section:
   - Option A: Select folder: `TestSimulator/`
   - Option B: Explicit tags:
     ```
     [default]TestSimulator/Sine0
     [default]TestSimulator/Ramp1
     [default]TestSimulator/Realistic0
     ```

2. Click "Save" and "Apply"

#### 4.5 Enable Module

Toggle "Enabled" switch to ON.

---

## Step 5: Verify Data Flow (1 min)

### In Ignition

1. Check module diagnostics:
   - Events sent count (should increase)
   - Last successful send timestamp
   - Stream state: OPENED

2. Monitor Gateway logs:
   ```bash
   tail -f /usr/local/ignition/logs/wrapper.log
   ```

Look for:
- `ZerobusClientManager: Stream created successfully`
- `ZerobusClientManager: Records acknowledged up to offset: XXX`

### In Databricks

Open SQL Editor and run:

```sql
-- Check recent events
SELECT * 
FROM main.ignition_ot_test.vw_recent_events 
LIMIT 10;

-- Check ingestion rate
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as events,
  COUNT(DISTINCT tag_path) as unique_tags
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 30 MINUTE
GROUP BY 1
ORDER BY 1 DESC;

-- Check data quality
SELECT 
  quality,
  COUNT(*) as count
FROM main.ignition_ot_test.bronze_events
GROUP BY quality;
```

### Expected Results

Within 1-2 minutes of enabling the module:

✅ **Ignition:**
- Module shows "Connected" status
- Events sent counter incrementing
- No errors in logs

✅ **Databricks:**
- Rows appearing in `bronze_events` table
- `event_time` matches Ignition timestamps (within seconds)
- `quality` = "GOOD" for simulator tags
- `tag_path` matches subscribed tags

---

## Troubleshooting

### Module Won't Install

**Symptom:** Installation fails with error

**Solutions:**
- Check Ignition version ≥ 8.1.0
- Review Gateway logs for specific error
- Verify module signature is valid
- Check Gateway has write permissions

### Connection Test Fails

**Symptom:** "Test Connection" returns error

**Solutions:**

| Error | Solution |
|-------|----------|
| Auth failed | Verify OAuth client ID/secret are correct |
| Table not found | Check table exists: `SHOW TABLES IN main.ignition_ot_test` |
| Network error | Check firewall allows HTTPS to `*.databricks.com` |
| Permission denied | Grant MODIFY on table to service principal |

### No Data in Delta Table

**Symptom:** Query returns no rows after 5 minutes

**Solutions:**
1. Check module is enabled
2. Verify tags are subscribed
3. Confirm tags are actually changing values (check in Quick Client)
4. Review Gateway logs for ingestion errors
5. Check stream state in module diagnostics

### Ignition Trial Timeout

**Symptom:** Gateway shows "Trial has expired" after 2 hours

**Solution:**
- This is normal in trial mode
- Click "Restart Trial" button
- Or restart Gateway: `sudo launchctl unload/load ...`
- Module will auto-reconnect

---

## Quick Commands Reference

### Ignition Gateway

```bash
# Start
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# Stop
sudo launchctl unload /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# Restart
sudo launchctl unload /Library/LaunchDaemons/com.inductiveautomation.ignition.plist && \
sudo launchctl load /Library/LaunchDaemons/com.inductiveautomation.ignition.plist

# View logs
tail -f /usr/local/ignition/logs/wrapper.log

# Check if running
curl http://localhost:8088
```

### Build Module

```bash
cd /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module

# Clean build
./gradlew clean buildModule

# Just compile
./gradlew compileJava

# Run tests
./gradlew test

# Check dependencies
./gradlew dependencies
```

### Databricks Queries

```sql
-- Row count
SELECT COUNT(*) FROM main.ignition_ot_test.bronze_events;

-- Latest events
SELECT * FROM main.ignition_ot_test.vw_recent_events LIMIT 10;

-- Check latency
SELECT 
  AVG(latency_seconds) as avg_latency,
  MAX(latency_seconds) as max_latency
FROM main.ignition_ot_test.vw_recent_events;

-- Tag list
SELECT DISTINCT tag_path 
FROM main.ignition_ot_test.bronze_events;

-- Delete test data (if needed)
DELETE FROM main.ignition_ot_test.bronze_events;
```

---

## Next Steps: Run Test Cases

Once data is flowing, execute test cases from `tester.md`:

1. ✅ **Basic Connectivity** - Already verified!
2. ✅ **Simple Ingestion** - Let run for 5 minutes, verify row counts
3. **Configuration Changes** - Modify batch size, verify behavior
4. **Enable/Disable** - Toggle module, check data flow stops/resumes
5. **Network Loss** - Disconnect network, verify recovery
6. **Invalid Credentials** - Test error handling
7. **High-Frequency Load** - Subscribe to 20+ tags, monitor performance

---

## Success Criteria

Your setup is working correctly when:

- ✅ Module installs without errors
- ✅ Connection test passes
- ✅ Data appears in Delta table within 30 seconds
- ✅ Timestamps match (within 1-2 seconds)
- ✅ Quality flags are correct
- ✅ All subscribed tags appear
- ✅ No errors in Gateway logs
- ✅ Ingestion rate is stable

**You're ready to test!** 🚀

