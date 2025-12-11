# Finding Your Databricks Workspace ID

The Workspace ID is required to build the correct Zerobus endpoint.

---

## Format Required

```
WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
```

**Example**: `1444828305810485.zerobus.us-west-2.cloud.databricks.com`

---

## Method 1: From Databricks URL

When logged into Databricks, check the URL:

```
https://xxxxx.cloud.databricks.com/?o=1444828305810485
                                        ^^^^^^^^^^^^^^^^^
                                        Your Workspace ID
```

The number after `?o=` is your Workspace ID.

---

## Method 2: From Workspace Settings

1. Log into Databricks
2. Click your username (top right)
3. Go to **Settings** → **Workspace Admin**
4. Look for **Workspace ID** field

---

## Method 3: Using Databricks CLI

```bash
databricks workspace get-status
```

Output will include `workspace_id`.

---

## Method 4: From Databricks Notebook

```python
# Run this in a Databricks notebook
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
print(f"Workspace URL: {workspace_url}")

# The workspace ID is in the URL path
# Or get it from the API
import requests
import os

token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
instance = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()

response = requests.get(
    f"{instance}/api/2.0/workspace/get-status",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Workspace ID: {response.json()['workspace_id']}")
```

---

## Building the Zerobus Endpoint

### AWS
```
Format: WORKSPACE_ID.zerobus.REGION.cloud.databricks.com

Examples:
- us-west-2: 1444828305810485.zerobus.us-west-2.cloud.databricks.com
- us-east-1: 1444828305810485.zerobus.us-east-1.cloud.databricks.com
- eu-west-1: 1444828305810485.zerobus.eu-west-1.cloud.databricks.com
```

### Azure
```
Format: WORKSPACE_ID.zerobus.REGION.azuredatabricks.net

Examples:
- westus2: 1444828305810485.zerobus.westus2.azuredatabricks.net
- eastus2: 1444828305810485.zerobus.eastus2.azuredatabricks.net
```

### GCP
```
Format: WORKSPACE_ID.zerobus.REGION.gcp.databricks.com

Examples:
- us-central1: 1444828305810485.zerobus.us-central1.gcp.databricks.com
- europe-west1: 1444828305810485.zerobus.europe-west1.gcp.databricks.com
```

---

## Verification

Test if the endpoint resolves:

```bash
nslookup WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
```

Should return IP addresses if correct.

---

## Common Mistakes ❌

### Wrong Formats:
```
❌ https://e2-demo-field-eng.cloud.databricks.com/api/2.0/zerobus/streams/ingest
❌ https://e2-demo-field-eng.cloud.databricks.com
❌ e2-demo-field-eng.zerobus.us-west-2.cloud.databricks.com  (must use numeric ID)
❌ workspace-name.zerobus.us-west-2.cloud.databricks.com     (must use numeric ID)
```

### Correct Format:
```
✅ 1444828305810485.zerobus.us-west-2.cloud.databricks.com
```

---

## Module Configuration Template

Once you have the Workspace ID, configure the module:

```json
{
  "enabled": true,
  "workspaceUrl": "https://your-workspace-name.cloud.databricks.com",
  "zerobusEndpoint": "YOUR_WORKSPACE_ID.zerobus.YOUR_REGION.cloud.databricks.com",
  "oauthClientId": "service-principal-client-id",
  "oauthClientSecret": "service-principal-secret",
  "catalogName": "your_catalog",
  "schemaName": "your_schema",
  "tableName": "your_table"
}
```

Apply via:
```bash
curl -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @config.json
```

---

## Need Help?

See:
- **USER_GUIDE.md** - Section: "Finding Workspace ID"
- **AUTOMATION_SETUP_GUIDE.md** - Section: "Zerobus Endpoint Format"
- **QUICK_START.md** - Step 1: Configuration

