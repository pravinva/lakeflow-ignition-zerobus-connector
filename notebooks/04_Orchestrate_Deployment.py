# Databricks notebook source
# MAGIC %md
# MAGIC # Orchestrate Ignition Deployment (Optional)
# MAGIC 
# MAGIC **Purpose**: Remote configuration of Ignition module via REST API
# MAGIC 
# MAGIC **Use Cases:**
# MAGIC - Centralized deployment orchestration
# MAGIC - Audit logging in Databricks
# MAGIC - Integration with Databricks Jobs/Workflows
# MAGIC 
# MAGIC **⚠️ Important Notes:**
# MAGIC - This notebook can only configure via REST API
# MAGIC - Cannot modify Event Stream files (must run scripts on Gateway)
# MAGIC - Gateway must be network-accessible from Databricks
# MAGIC - Consider security implications (VPN, private link, firewall rules)
# MAGIC 
# MAGIC **Alternative**: Run scripts directly on Gateway (simpler, more secure)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Gateway connection details
GATEWAY_URL = "http://gateway.example.com:8088"  # Replace with actual Gateway URL
GATEWAY_USERNAME = "admin"  # Or use Databricks secrets
GATEWAY_PASSWORD = dbutils.secrets.get(scope="ignition", key="gateway-password")  # Use secrets!

# Databricks Zerobus configuration
WORKSPACE_ID = "1444828305810485"  # Your workspace ID
REGION = "us-west-2"  # Your region
ZEROBUS_ENDPOINT = f"{WORKSPACE_ID}.zerobus.{REGION}.cloud.databricks.com"

# Service Principal credentials (use secrets!)
SERVICE_PRINCIPAL_CLIENT_ID = dbutils.secrets.get(scope="ignition", key="sp-client-id")
SERVICE_PRINCIPAL_SECRET = dbutils.secrets.get(scope="ignition", key="sp-secret")

# Table details
CATALOG_NAME = "ignition_demo"
SCHEMA_NAME = "scada_data"
TABLE_NAME = "tag_events"

print("Configuration loaded")
print(f"Gateway: {GATEWAY_URL}")
print(f"Zerobus Endpoint: {ZEROBUS_ENDPOINT}")
print(f"Target Table: {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Check Gateway Connectivity

# COMMAND ----------

import requests
from datetime import datetime

def check_gateway_health(gateway_url):
    """Check if Gateway is accessible"""
    try:
        response = requests.get(f"{gateway_url}/system/zerobus/diagnostics", timeout=5)
        if response.status_code == 200:
            print("✅ Gateway is accessible")
            return True
        else:
            print(f"⚠️ Gateway returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Gateway: {e}")
        return False

# Check connectivity
gateway_healthy = check_gateway_health(GATEWAY_URL)

if not gateway_healthy:
    print("\n⚠️ WARNING: Cannot proceed without Gateway connectivity")
    print("Options:")
    print("1. Check network connectivity from Databricks to Gateway")
    print("2. Verify Gateway URL and port")
    print("3. Check firewall rules")
    print("4. Alternative: Run scripts directly on Gateway (recommended)")
    dbutils.notebook.exit("FAILED: Gateway not accessible")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Configure Module via REST API

# COMMAND ----------

def configure_module(gateway_url, config):
    """Configure Ignition Zerobus module via REST API"""
    try:
        response = requests.post(
            f"{gateway_url}/system/zerobus/config",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Module configured successfully")
            return True, response.json()
        else:
            print(f"❌ Configuration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error configuring module: {e}")
        return False, None

# Build configuration
module_config = {
    "enabled": True,
    "workspaceUrl": f"https://{spark.conf.get('spark.databricks.workspaceUrl')}",
    "zerobusEndpoint": ZEROBUS_ENDPOINT,
    "oauthClientId": SERVICE_PRINCIPAL_CLIENT_ID,
    "oauthClientSecret": SERVICE_PRINCIPAL_SECRET,
    "catalogName": CATALOG_NAME,
    "schemaName": SCHEMA_NAME,
    "tableName": TABLE_NAME,
    "targetTable": f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}",
    "sourceSystemId": "ignition-gateway-orchestrated",
    "batchSize": 100,
    "batchFlushIntervalMs": 5000,
    "maxQueueSize": 10000
}

# Apply configuration
success, result = configure_module(GATEWAY_URL, module_config)

if not success:
    dbutils.notebook.exit("FAILED: Module configuration failed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Verify Configuration

# COMMAND ----------

import time

def get_module_diagnostics(gateway_url):
    """Get module diagnostics"""
    try:
        response = requests.get(f"{gateway_url}/system/zerobus/diagnostics", timeout=10)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# Wait for initialization
print("Waiting 10 seconds for module to initialize...")
time.sleep(10)

# Get diagnostics
diagnostics = get_module_diagnostics(GATEWAY_URL)
print("\n" + "="*60)
print("Module Diagnostics:")
print("="*60)
print(diagnostics)
print("="*60)

# Parse diagnostics to check key metrics
if "Connected: true" in diagnostics and "Stream State: OPENED" in diagnostics:
    print("\n✅ Module is connected and streaming!")
else:
    print("\n⚠️ Module may not be fully connected. Check diagnostics above.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Log Deployment

# COMMAND ----------

# Create deployment log
deployment_log = spark.createDataFrame([{
    "deployment_time": datetime.now(),
    "gateway_url": GATEWAY_URL,
    "zerobus_endpoint": ZEROBUS_ENDPOINT,
    "target_table": f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}",
    "configuration_success": success,
    "deployed_by": spark.sql("SELECT current_user()").collect()[0][0],
    "diagnostics": diagnostics[:500]  # First 500 chars
}])

# Save to audit table (create if doesn't exist)
deployment_log.write.mode("append").saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.deployment_audit")

print("✅ Deployment logged to audit table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Data Flow

# COMMAND ----------

# Wait for data to arrive
print("Waiting 30 seconds for data to arrive...")
time.sleep(30)

# Check for recent events
recent_events = spark.sql(f"""
SELECT COUNT(*) as event_count
FROM {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL 5 MINUTES
""").collect()[0]["event_count"]

print(f"\nEvents in last 5 minutes: {recent_events}")

if recent_events > 0:
    print("✅ Data is flowing!")
    
    # Show sample
    display(spark.sql(f"""
    SELECT * FROM {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}
    ORDER BY event_time DESC
    LIMIT 10
    """))
else:
    print("⚠️ No recent events detected")
    print("Possible causes:")
    print("1. Event Stream not enabled in Designer")
    print("2. No tags changing values")
    print("3. Event Stream not configured (requires script on Gateway)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Deployment Summary

# COMMAND ----------

summary = f"""
{'='*60}
DEPLOYMENT SUMMARY
{'='*60}

Gateway: {GATEWAY_URL}
Zerobus Endpoint: {ZEROBUS_ENDPOINT}
Target Table: {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}

Configuration: {'✅ SUCCESS' if success else '❌ FAILED'}
Recent Events: {recent_events}

Deployed At: {datetime.now()}
Deployed By: {spark.sql("SELECT current_user()").collect()[0][0]}

{'='*60}

NEXT STEPS:
1. Verify Event Stream is enabled in Ignition Designer
2. Run: notebooks/02_Monitor_Data_Flow.py
3. Set up alerts for production monitoring

⚠️ REMINDER:
- Event Stream configuration requires scripts on Gateway
- Run: scripts/configure_eventstream.py --name ...
- This notebook only handles REST API configuration

{'='*60}
"""

print(summary)

# Return status for job orchestration
dbutils.notebook.exit("SUCCESS" if success and recent_events > 0 else "PARTIAL")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📝 Notes
# MAGIC 
# MAGIC ### What This Notebook CAN Do:
# MAGIC - ✅ Configure module via REST API
# MAGIC - ✅ Check Gateway connectivity
# MAGIC - ✅ Verify Zerobus connection
# MAGIC - ✅ Monitor data flow
# MAGIC - ✅ Log deployments to audit table
# MAGIC 
# MAGIC ### What This Notebook CANNOT Do:
# MAGIC - ❌ Configure Event Streams (requires file system access)
# MAGIC - ❌ Restart Gateway
# MAGIC - ❌ Install module
# MAGIC - ❌ Modify Ignition project files
# MAGIC 
# MAGIC ### For Complete Deployment:
# MAGIC Use scripts on Gateway server:
# MAGIC ```bash
# MAGIC # On Gateway or deployment machine:
# MAGIC ./scripts/configure_eventstream.py --name stream --project Project --tags ...
# MAGIC ./scripts/configure_module.sh production
# MAGIC ```
# MAGIC 
# MAGIC ### Security Considerations:
# MAGIC - Use Databricks Secrets for credentials
# MAGIC - Restrict network access (VPN, private link)
# MAGIC - Use HTTPS for Gateway
# MAGIC - Audit all deployments
# MAGIC - Limit who can run this notebook

