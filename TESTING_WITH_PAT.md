# Testing Module with Personal Access Token (PAT)

**Scenario:** You don't have admin access to create OAuth service principals  
**Solution:** Use your personal access token for testing

---

## ✅ What We Have

**Service Principal Created:**
- Display Name: `ignition-zerobus-connector`
- Application ID (Client ID): `52393ed8-ea22-4830-a6ef-6b6545e6be5f`
- Service Principal ID: `74011659140053`

**Your Personal Access Token:**
- Token: `<your-token-from-~/.databrickscfg>`
- Host: `https://e2-demo-field-eng.cloud.databricks.com`

---

## 🔧 Testing Approach

Since Zerobus SDK typically requires OAuth2 client credentials, but you have a PAT, we have two options:

### Option A: Mock Configuration for Testing (Recommended)

Configure the module with **placeholder** OAuth credentials to test:
1. Tag subscription
2. Data transformation
3. UI functionality
4. Everything except actual Databricks ingestion

**Use these test credentials:**
```
Client ID: 52393ed8-ea22-4830-a6ef-6b6545e6be5f
Client Secret: test-secret-for-development-only
```

The module will:
- ✅ Subscribe to tags
- ✅ Transform data to Protobuf
- ✅ Show in diagnostics
- ❌ Won't actually send to Databricks (auth will fail)

### Option B: Request Admin Help

Ask a Databricks workspace/account admin to:
1. Go to the service principal we created: `ignition-zerobus-connector`
2. Generate an OAuth secret
3. Share the secret with you

---

## 🧪 Test Configuration (Option A)

### Step 1: Configure Simulator

In Ignition Gateway:
1. Go to: **Config → OPC UA → Device Connections**
2. Click **"Create new Device"**
3. Select: **"Simulators → Generic Simulator"**
4. Name: `TestSimulator`
5. Enable: ✅ **"Enabled"**
6. Click **"Create New Device"**

### Step 2: Configure Module

Navigate to: `http://localhost:8088/system/zerobus/config`

**Enter Configuration:**
```
Workspace URL: https://e2-demo-field-eng.cloud.databricks.com
Zerobus Endpoint: e2-demo-field-eng.zerobus.cloud.databricks.com
OAuth Client ID: 52393ed8-ea22-4830-a6ef-6b6545e6be5f
OAuth Client Secret: test-secret-for-development-only
Target Table: lakeflow_ignition.ot_data.bronze_events
Source System: Ignition-Dev-Mac
Batch Size: 100
Batch Interval (seconds): 5
Tags: [default]TestSimulator/Sine0
```

### Step 3: Enable Module

1. Toggle **"Enabled"** to ON
2. Click **"Save"**

### Step 4: Monitor Logs

```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

**Expected (with test credentials):**
```
✅ Tag subscription started
✅ Tag values being captured
✅ Protobuf transformation working
❌ Authentication will fail (expected)
```

**This validates:**
- ✅ Module configuration works
- ✅ Tag subscription works
- ✅ Data transformation works
- ✅ UI is functional

---

## 🎯 What Can Be Tested Without Real OAuth

| Test Case | Can Test? | Notes |
|-----------|-----------|-------|
| **1. Basic Connectivity** | ⚠️ Partial | Config saves, but auth will fail |
| **2. Tag Subscription** | ✅ Yes | Tags subscribe and update |
| **3. Data Transformation** | ✅ Yes | Protobuf generation works |
| **4. UI Functionality** | ✅ Yes | All UI features work |
| **5. Enable/Disable** | ✅ Yes | State management works |
| **6. Configuration Changes** | ✅ Yes | Dynamic reconfiguration works |
| **7. Diagnostics** | ✅ Yes | Counters and status work |
| **8. Databricks Ingestion** | ❌ No | Requires valid OAuth |

---

## 🔐 Getting Real OAuth Credentials

### Ask Your Admin

Send them this message:

```
Hi! I created a service principal for testing:

Name: ignition-zerobus-connector
Application ID: 52393ed8-ea22-4830-a6ef-6b6545e6be5f
Service Principal ID: 74011659140053

Could you please:
1. Go to Account Console → Service Principals
2. Find "ignition-zerobus-connector"
3. Generate an OAuth secret
4. Share the client secret with me?

This is for testing our Ignition → Databricks integration.

Thanks!
```

### Or Use Databricks CLI (if you have access)

```bash
databricks service-principals create-secret \
  --service-principal-id 74011659140053 \
  --description "Ignition Zerobus Module"
```

---

## 🚀 Once You Have Real OAuth

Replace the test secret with the real one:

1. Go to module config: `http://localhost:8088/system/zerobus/config`
2. Update **OAuth Client Secret** with real value
3. Click **"Test Connection"** - should pass ✅
4. Enable module
5. Data should flow to Databricks!

Query to verify:
```sql
SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events LIMIT 10;
```

---

## 📊 Current Status

```
✅ Ignition module: RUNNING
✅ Service principal: CREATED
✅ Tag simulator: Ready to configure
⏳ OAuth secret: Need admin help OR use test mode
```

**Recommendation:** Proceed with test mode to validate everything except Databricks ingestion!

---

## 🎯 Next Steps

1. ✅ **Configure simulator** (Step 1 above)
2. ✅ **Configure module with test credentials** (Step 2 above)
3. ✅ **Enable and monitor** (Steps 3-4 above)
4. ⏳ **Get real OAuth secret from admin**
5. ✅ **Update config with real secret**
6. ✅ **Verify end-to-end data flow**

**Want to proceed with test mode?** Let me know and I'll help configure it!

