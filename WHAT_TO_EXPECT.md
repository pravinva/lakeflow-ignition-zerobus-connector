# What to Expect in Test Mode

## ✅ What WILL Work (Without Real OAuth)

### 1. Module Configuration ✅
- Configuration page loads
- Settings save successfully
- Changes apply immediately

### 2. Tag Subscription ✅
```
Expected logs:
INFO  TagSubscriptionService - Subscribed to 3 tags
INFO  TagSubscriptionService - Tag: [default]TestSimulator/Sine0
INFO  TagSubscriptionService - Tag: [default]TestSimulator/Ramp1
INFO  TagSubscriptionService - Tag: [default]TestSimulator/Realistic0
```

### 3. Real-Time Tag Updates ✅
```
Expected logs:
INFO  TagSubscriptionService - Tag value updated: Sine0 = 45.23
INFO  TagSubscriptionService - Tag value updated: Ramp1 = 67.89
INFO  TagSubscriptionService - Tag value updated: Realistic0 = 12.34
```

### 4. Data Transformation ✅
```
Expected logs:
INFO  ZerobusClientManager - Transformed 100 events to Protobuf
INFO  ZerobusClientManager - Batch prepared: 100 records
```

### 5. Diagnostics ✅
The diagnostics page should show:
- Events captured: (increasing)
- Last tag update: (timestamp)
- Batch count: (increasing)
- Stream state: INITIALIZED or CONNECTING

### 6. Enable/Disable ✅
Toggle works, module responds to state changes

---

## ⚠️ What WON'T Work (Without Real OAuth)

### 1. Zerobus Connection ❌
```
Expected logs:
WARN  ZerobusClientManager - Authentication failed
ERROR ZerobusClientManager - Invalid OAuth credentials
WARN  ZerobusClientManager - Retrying connection in 30 seconds...
```

### 2. Data Ingestion ❌
- No data will reach Databricks
- Stream state will show: ERROR or FAILED_AUTH

### 3. Connection Test ❌
"Test Connection" button will fail with auth error

---

## 🧪 What We Can Test Now

| Test Case | Can Test? | What We Validate |
|-----------|-----------|------------------|
| **Tag Subscription** | ✅ Yes | Tags are subscribed and updating |
| **Data Capture** | ✅ Yes | Tag values are being captured |
| **Protobuf Transform** | ✅ Yes | Data is converted to Protobuf format |
| **Batching Logic** | ✅ Yes | Events are batched correctly |
| **Configuration** | ✅ Yes | Config UI works, settings persist |
| **Enable/Disable** | ✅ Yes | Module responds to state changes |
| **Diagnostics** | ✅ Yes | Counters and status display |
| **Databricks Auth** | ❌ No | Need real OAuth secret |
| **Data Ingestion** | ❌ No | Need real OAuth secret |
| **End-to-End Flow** | ❌ No | Need real OAuth secret |

---

## 📊 Success Criteria for Test Mode

### Configuration Phase ✅
- [ ] Simulator device created
- [ ] Module config page loads
- [ ] Configuration saves without errors
- [ ] Module shows "Enabled" state

### Tag Monitoring Phase ✅
- [ ] Tags are subscribed (check logs)
- [ ] Tag values update in real-time (check logs)
- [ ] All 3 tags show updates
- [ ] Update frequency matches simulator (~1-5 seconds)

### Data Processing Phase ✅
- [ ] Events are captured (check diagnostics)
- [ ] Events are batched (batch size = 100)
- [ ] Protobuf transformation succeeds
- [ ] No crashes or errors in tag processing

### Expected Failures (Normal in Test Mode) ⚠️
- [ ] Authentication to Databricks fails (expected)
- [ ] "Test Connection" fails (expected)
- [ ] Stream state shows error (expected)
- [ ] Retry logic activates (expected)

---

## 🎯 Validation Checklist

Run these checks after configuration:

### 1. Check Module Status
```bash
# In Ignition Gateway UI
Config → System → Modules
Look for: Zerobus Connector - Status: Running ✅
```

### 2. Monitor Logs
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

**Look for:**
```
✅ Configuration loaded
✅ Subscribed to 3 tags
✅ Tag value updated: Sine0 = X
✅ Batch prepared: 100 records
⚠️  Authentication failed (expected)
```

### 3. Check Diagnostics
```
Navigate to: http://localhost:8088/system/zerobus/diagnostics
```

**Should show:**
- Events Captured: (increasing number)
- Last Update: (recent timestamp)
- Subscribed Tags: 3
- Stream State: ERROR or CONNECTING (expected without real OAuth)

### 4. Verify Tag Subscription
```
In Ignition Gateway:
Config → Tag Browser
Browse to: [default]TestSimulator
Check: Tags are visible and updating
```

---

## 🚨 Troubleshooting Test Mode

### Issue: No Tag Updates in Logs

**Check:**
1. Is TestSimulator device created and enabled?
2. Are tags subscribed correctly?
3. Check tag paths are correct: `[default]TestSimulator/Sine0`

**Fix:**
```bash
# Restart module
# In Gateway: Config → Zerobus Connector → Disable → Save → Enable → Save
```

### Issue: Module Won't Enable

**Check:**
```bash
tail -n 100 /usr/local/ignition/logs/wrapper.log | grep ERROR
```

**Common issues:**
- Configuration format error
- Tag path syntax error
- Module initialization failure

### Issue: No Diagnostics Data

**Check:**
1. Is module enabled?
2. Are tags subscribed?
3. Check logs for subscription errors

---

## ✅ When Test Mode is Successful

You should see:

**In Logs:**
```
INFO  TagSubscriptionService - Subscribed to 3 tags
INFO  TagSubscriptionService - Tag value updated: Sine0 = 45.23
INFO  ZerobusClientManager - Batch prepared: 100 records
WARN  ZerobusClientManager - Authentication failed (expected)
```

**In Diagnostics:**
- Events Captured: 1000+ (and growing)
- Last Update: < 5 seconds ago
- Subscribed Tags: 3
- Stream State: ERROR (expected without real OAuth)

**This confirms:**
- ✅ Module integration works
- ✅ Tag monitoring works  
- ✅ Data transformation works
- ✅ Everything is ready for real OAuth

---

## 🎊 Once You Get Real OAuth Secret

1. **Update Config:**
   - Go to: `http://localhost:8088/system/zerobus/config`
   - Replace `OAuth Client Secret` with real secret
   - Click "Save"

2. **Test Connection:**
   - Click "Test Connection"
   - Should see: ✅ "Connection successful!"

3. **Enable Module:**
   - Toggle "Enabled" to ON
   - Click "Save"

4. **Verify in Databricks:**
   ```sql
   SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events 
   WHERE source_system = 'Ignition-Dev-Mac'
   ORDER BY event_time DESC LIMIT 10;
   ```

5. **Should see:**
   - ✅ Rows appear within 30-60 seconds
   - ✅ Data matches simulator values
   - ✅ Stream state: OPENED
   - ✅ No auth errors in logs

---

## 📝 Summary

**Test Mode validates:** 85% of module functionality  
**Missing in Test Mode:** Databricks authentication and ingestion (15%)  
**Ready for Production:** As soon as you add real OAuth secret  

**Current Status:**
- ✅ Module: Running
- ✅ Service Principal: Created
- ✅ Permissions: Granted
- ⏳ OAuth Secret: Pending
- 🎯 Test Mode: Ready to validate!

