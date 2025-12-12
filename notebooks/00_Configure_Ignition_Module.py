# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Configure Ignition Zerobus Connector (POST /system/zerobus/config)
# MAGIC
# MAGIC This notebook is a **customer-friendly "GUI replacement"** for configuring the Ignition module via REST.
# MAGIC
# MAGIC It:
# MAGIC - Builds the module config JSON (with widgets)
# MAGIC - Prints a ready-to-copy `curl` command
# MAGIC - Optionally **POSTs** the config (if the Databricks workspace can reach your Ignition Gateway)
# MAGIC - Provides quick verification queries for **Bronze → Silver → Gold**
# MAGIC
# MAGIC ## Important networking note
# MAGIC If your Ignition gateway is on `localhost` or behind a firewall, Databricks may not be able to reach it directly.
# MAGIC In that case:
# MAGIC - Copy the generated `curl` command and run it from your laptop/DMZ host instead.

# COMMAND ----------
dbutils.widgets.text("ignition_gateway_base_url", "http://YOUR_IGNITION_HOST:8099", "Ignition Gateway Base URL")
dbutils.widgets.text("catalog", "ignition_demo", "Unity Catalog")
dbutils.widgets.text("schema", "tilt_ot", "Schema")
dbutils.widgets.text("table", "ot_events_bronze", "Bronze Table")

dbutils.widgets.text("workspaceUrl", "https://YOUR_WORKSPACE.cloud.databricks.com", "Databricks Workspace URL")
dbutils.widgets.text("zerobusEndpoint", "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com", "Zerobus Endpoint")
dbutils.widgets.text("oauthClientId", "YOUR_SP_CLIENT_ID", "OAuth Client ID")
dbutils.widgets.text("oauthClientSecret_scope", "", "Secret Scope (optional)")
dbutils.widgets.text("oauthClientSecret_key", "", "Secret Key (optional)")
dbutils.widgets.text("oauthClientSecret_inline", "", "OAuth Client Secret (inline, NOT recommended)")

dbutils.widgets.text("sourceSystemId", "tilt-siteA-ignition", "sourceSystemId")

# For quick testing without Event Streams (works on Ignition 8.1/8.2/8.3)
dbutils.widgets.dropdown("tagSelectionMode", "folder", ["folder", "pattern", "explicit"], "Tag Selection Mode")
dbutils.widgets.text("tagFolderPath", "[Sample_Tags]Ramp", "Tag Folder Path (folder mode)")
dbutils.widgets.text("tagPathPattern", "", "Tag Path Pattern (pattern mode)")
dbutils.widgets.text("explicitTagPaths_csv", "", "Explicit Tag Paths CSV (explicit mode)")
dbutils.widgets.dropdown("includeSubfolders", "true", ["true", "false"], "Include Subfolders")

dbutils.widgets.text("batchSize", "200", "Batch Size")
dbutils.widgets.text("batchFlushIntervalMs", "500", "Flush Interval (ms)")
dbutils.widgets.text("maxQueueSize", "10000", "Max Queue Size")
dbutils.widgets.text("maxEventsPerSecond", "10000", "Max Events/Sec")
dbutils.widgets.dropdown("onlyOnChange", "true", ["true", "false"], "Only On Change")
dbutils.widgets.text("numericDeadband", "0.0", "Numeric Deadband")
dbutils.widgets.dropdown("debugLogging", "true", ["true", "false"], "Debug Logging")
dbutils.widgets.dropdown("enabled", "true", ["true", "false"], "Enable Module")

# COMMAND ----------
import json

def _bool(v: str) -> bool:
    return str(v).strip().lower() == "true"

def _get_secret() -> str:
    scope = dbutils.widgets.get("oauthClientSecret_scope").strip()
    key = dbutils.widgets.get("oauthClientSecret_key").strip()
    inline = dbutils.widgets.get("oauthClientSecret_inline")
    if scope and key:
        return dbutils.secrets.get(scope=scope, key=key)
    if inline:
        return inline
    return ""

gateway_base = dbutils.widgets.get("ignition_gateway_base_url").rstrip("/")
catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
table = dbutils.widgets.get("table").strip()

target_table = f"{catalog}.{schema}.{table}"

explicit_csv = dbutils.widgets.get("explicitTagPaths_csv").strip()
explicit_paths = [p.strip() for p in explicit_csv.split(",") if p.strip()] if explicit_csv else []

config = {
    "enabled": _bool(dbutils.widgets.get("enabled")),
    "workspaceUrl": dbutils.widgets.get("workspaceUrl").strip(),
    "zerobusEndpoint": dbutils.widgets.get("zerobusEndpoint").strip(),
    "oauthClientId": dbutils.widgets.get("oauthClientId").strip(),
    "oauthClientSecret": _get_secret(),
    "targetTable": target_table,
    "sourceSystemId": dbutils.widgets.get("sourceSystemId").strip(),

    "tagSelectionMode": dbutils.widgets.get("tagSelectionMode").strip(),
    "tagFolderPath": dbutils.widgets.get("tagFolderPath").strip(),
    "tagPathPattern": dbutils.widgets.get("tagPathPattern").strip(),
    "explicitTagPaths": explicit_paths,
    "includeSubfolders": _bool(dbutils.widgets.get("includeSubfolders")),

    "batchSize": int(dbutils.widgets.get("batchSize")),
    "batchFlushIntervalMs": int(dbutils.widgets.get("batchFlushIntervalMs")),
    "maxQueueSize": int(dbutils.widgets.get("maxQueueSize")),
    "maxEventsPerSecond": int(dbutils.widgets.get("maxEventsPerSecond")),
    "onlyOnChange": _bool(dbutils.widgets.get("onlyOnChange")),
    "numericDeadband": float(dbutils.widgets.get("numericDeadband")),
    "debugLogging": _bool(dbutils.widgets.get("debugLogging")),
}

print("Target table:", target_table)
print("\nConfig JSON:\n")
print(json.dumps(config, indent=2))

if not config.get("oauthClientSecret"):
    print("\n" + "=" * 80)
    print("WARNING: oauthClientSecret is empty")
    print("- The module requires oauthClientSecret (ConfigModel.validate()).")
    print("- Recommended: store the secret in a Databricks Secret Scope and set:")
    print("    oauthClientSecret_scope + oauthClientSecret_key")
    print("- Fallback (not recommended): set oauthClientSecret_inline")
    print("=" * 80 + "\n")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Generated curl command (run from a machine that can reach Ignition)

# COMMAND ----------
import shlex

config_json = json.dumps(config)
curl_cmd = (
    "curl -X POST "
    + shlex.quote(f"{gateway_base}/system/zerobus/config")
    + " -H 'Content-Type: application/json' "
    + " -d "
    + shlex.quote(config_json)
)

print(curl_cmd)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Optional: POST from this notebook (only works if Databricks can reach your Ignition Gateway)

# COMMAND ----------
import urllib.request, urllib.error

def http_post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "ignore")

def http_get(url: str):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "ignore")

post_url = f"{gateway_base}/system/zerobus/config"

try:
    status, body = http_post_json(post_url, config)
    print("POST", post_url, "=>", status)
    print(body[:2000])
except Exception as e:
    print("POST failed (this is common if your gateway is not reachable from Databricks):")
    print(type(e).__name__, str(e)[:500])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Verify module endpoints

# COMMAND ----------
for suffix in ["/system/zerobus/config", "/system/zerobus/health", "/system/zerobus/diagnostics"]:
    url = gateway_base + suffix
    try:
        status, body = http_get(url)
        print("\nGET", url, "=>", status)
        print(body[:1200])
    except Exception as e:
        print("\nGET failed:", url)
        print(type(e).__name__, str(e)[:300])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Databricks verification (Bronze → Silver → Gold)
# MAGIC
# MAGIC Run after data starts arriving in Bronze.

# COMMAND ----------
bronze_fqn = target_table
print("Bronze table:", bronze_fqn)

# COMMAND ----------
# MAGIC %sql
# MAGIC -- Bronze: latest events
# MAGIC -- Replace with your table if you changed widgets.
# MAGIC SELECT *
# MAGIC FROM ${catalog}.${schema}.${table}
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 50;

# COMMAND ----------
# MAGIC %sql
# MAGIC -- Silver: normalized events (from onboarding/tilt SQL pack)
# MAGIC SELECT *
# MAGIC FROM ${catalog}.${schema}.v_silver_events
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 50;

# COMMAND ----------
# MAGIC %sql
# MAGIC -- Gold: daily KPIs (template)
# MAGIC SELECT *
# MAGIC FROM ${catalog}.${schema}.gold_daily_asset_kpis
# MAGIC ORDER BY kpi_date DESC, site, asset_type, asset_id
# MAGIC LIMIT 50;


