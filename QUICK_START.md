# Quick Start - Deploy in 10 Minutes

## Prerequisites
- Ignition Gateway 8.3.0+
- Databricks workspace with Zerobus enabled
- Service Principal credentials

## Step 1: Find Your Zerobus Endpoint (2 min)

### Get Workspace ID
Check your Databricks URL:
```
https://xxxxx.cloud.databricks.com/?o=1444828305810485
                                        ^^^^^^^^^^^^^^^^^
                                        Your Workspace ID
```

### Build Zerobus Endpoint
Format: `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com`

**Examples:**
- AWS us-west-2: `1444828305810485.zerobus.us-west-2.cloud.databricks.com`
- Azure westus2: `1444828305810485.zerobus.westus2.azuredatabricks.net`
- GCP us-central1: `1444828305810485.zerobus.us-central1.gcp.databricks.com`

## Step 2: Install Module (3 min)

```bash
# Copy module
sudo cp Ignition-Zerobus-unsigned.modl /usr/local/ignition/user-lib/modules/

# Restart Gateway
sudo /usr/local/ignition/ignition.sh restart

# Wait 30 seconds, then verify
curl http://localhost:8088/system/zerobus/diagnostics
```

## Step 3: Create Configuration (2 min)

```bash
cat > my-config.json <<'EOF'
{
  "enabled": true,
  "workspaceUrl": "https://YOUR-WORKSPACE.cloud.databricks.com",
  "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
  "oauthClientId": "YOUR-CLIENT-ID",
  "oauthClientSecret": "YOUR-CLIENT-SECRET",
  "catalogName": "YOUR_CATALOG",
  "schemaName": "YOUR_SCHEMA",
  "tableName": "YOUR_TABLE",
  "targetTable": "CATALOG.SCHEMA.TABLE",
  "sourceSystemId": "ignition-gateway-001"
}
EOF
```

```bash
cat > my-tags.txt <<'EOF'
[default]Tag1
[default]Tag2
[default]Tag3
EOF
```

## Step 4: Create Event Stream (1 min)

In Designer:
1. Event Streams → Right-click → New Event Stream
2. Name: `my_stream`
3. Save (leave empty)
4. Close Designer

## Step 5: Run Automation (2 min)

```bash
# Configure Event Stream
./scripts/configure_eventstream.py \
  --name my_stream \
  --project MyProject \
  --tag-file my-tags.txt

# Configure Module  
curl -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @my-config.json

# Wait for initialization
sleep 10
```

## Step 6: Verify (1 min)

```bash
# Check module
curl http://localhost:8088/system/zerobus/diagnostics

# Should show:
# Connected: true
# Stream State: OPENED
# Total Events Sent: (increasing)
```

```sql
-- Check Databricks
SELECT * FROM your_catalog.your_schema.your_table
ORDER BY event_time DESC LIMIT 100;
```

## ✅ Done!

Data is now flowing: **Tags → Event Streams → Module → Databricks**

---

## Common Issues

### "UNAUTHENTICATED" Error
**Fix:** Check Zerobus endpoint format - must use numeric workspace ID

### "Event Stream empty in Designer"
**Fix:** Restart Gateway after running configuration script

### "No data in Databricks"
**Fix:** Enable Event Stream in Designer (toggle switch)

---

## Next Steps

- [Complete Automation Guide](AUTOMATION_SETUP_GUIDE.md) - Multi-environment setup
- [Event Streams Setup](docs/EVENT_STREAMS_SETUP.md) - Detailed Event Stream guide
- [Handover Document](docs/HANDOVER.md) - User guide and troubleshooting
- [README](README.md) - Full project documentation

