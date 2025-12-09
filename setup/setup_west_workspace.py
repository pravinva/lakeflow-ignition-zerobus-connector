#!/usr/bin/env python3
"""
Setup script for e2-demo-west workspace with admin permissions.
Creates all necessary resources for Ignition → Databricks integration.
"""

from databricks import sql
import requests
import json
import os
import uuid
from datetime import datetime

# Workspace configuration
WORKSPACE_HOST = "e2-demo-west.cloud.databricks.com"
WORKSPACE_URL = f"https://{WORKSPACE_HOST}"
TOKEN = os.environ.get("DATABRICKS_TOKEN") or "<your-token-from-~/.databrickscfg>"

# Configuration
CATALOG_NAME = "lakeflow_ignition"
SCHEMA_NAME = "ot_data"
TABLE_NAME = "bronze_events"
SP_NAME = "ignition-zerobus-connector"

print("=" * 80)
print("🚀 SETTING UP E2-DEMO-WEST WORKSPACE")
print("=" * 80)
print(f"Workspace: {WORKSPACE_URL}")
print(f"Catalog: {CATALOG_NAME}")
print(f"Schema: {SCHEMA_NAME}")
print(f"Table: {TABLE_NAME}")
print(f"Service Principal: {SP_NAME}")
print("=" * 80)
print()

# Step 1: Create Service Principal with OAuth
print("📋 Step 1: Creating Service Principal with OAuth...")
print("-" * 80)

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create service principal
sp_data = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServicePrincipal"],
    "displayName": SP_NAME,
    "applicationId": str(uuid.uuid4()),
    "active": True
}

response = requests.post(
    f"{WORKSPACE_URL}/api/2.0/preview/scim/v2/ServicePrincipals",
    headers=headers,
    json=sp_data
)

if response.status_code in [200, 201]:
    sp = response.json()
    sp_id = sp.get('id')
    app_id = sp.get('applicationId')
    
    print(f"✅ Service Principal Created!")
    print(f"   Display Name: {sp.get('displayName')}")
    print(f"   Application ID: {app_id}")
    print(f"   Service Principal ID: {sp_id}")
    
    # Create OAuth secret
    print(f"\n📝 Creating OAuth Secret...")
    secret_response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/preview/scim/v2/ServicePrincipals/{sp_id}/secrets",
        headers=headers,
        json={"description": "Ignition Zerobus Module"}
    )
    
    if secret_response.status_code in [200, 201]:
        secret_data = secret_response.json()
        client_secret = secret_data.get('secret', {}).get('value')
        
        print(f"✅ OAuth Secret Created!")
        print(f"   Client ID: {app_id}")
        print(f"   Client Secret: {client_secret}")
        print()
        print("   ⚠️  SAVE THESE CREDENTIALS - Secret won't be shown again!")
        
        # Save to config file
        config = {
            "workspace": "e2-demo-west",
            "workspaceUrl": WORKSPACE_URL,
            "zerobusEndpoint": f"{WORKSPACE_HOST.replace('https://', '').replace('/', '')}",
            "oauthClientId": app_id,
            "oauthClientSecret": client_secret,
            "servicePrincipalId": sp_id,
            "createdAt": datetime.now().isoformat()
        }
        
        with open('west_workspace_credentials.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("   📄 Credentials saved to: west_workspace_credentials.json")
    else:
        print(f"❌ Failed to create OAuth secret: {secret_response.status_code}")
        print(f"   Response: {secret_response.text}")
        app_id = sp.get('applicationId')
        client_secret = None
else:
    print(f"❌ Failed to create service principal: {response.status_code}")
    print(f"   Response: {response.text}")
    exit(1)

print()

# Step 2: Create Catalog, Schema, Table
print("📋 Step 2: Setting up Databricks Resources...")
print("-" * 80)

try:
    # Try to connect with serverless warehouse
    # You may need to update this warehouse ID for west workspace
    connection = sql.connect(
        server_hostname=WORKSPACE_HOST,
        http_path="/sql/1.0/warehouses/4b9b953939869799",  # Update if different
        access_token=TOKEN
    )
    
    cursor = connection.cursor()
    
    # Create catalog
    print(f"Creating catalog: {CATALOG_NAME}")
    try:
        cursor.execute(f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}")
        print(f"✅ Catalog created: {CATALOG_NAME}")
    except Exception as e:
        print(f"⚠️  Catalog may already exist: {e}")
    
    # Create schema
    print(f"Creating schema: {CATALOG_NAME}.{SCHEMA_NAME}")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}")
    print(f"✅ Schema created: {CATALOG_NAME}.{SCHEMA_NAME}")
    
    # Create table
    print(f"Creating table: {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME} (
        event_id STRING COMMENT 'Unique event identifier',
        event_time TIMESTAMP COMMENT 'Event timestamp from tag',
        tag_path STRING COMMENT 'Full Ignition tag path',
        tag_provider STRING COMMENT 'Tag provider name',
        numeric_value DOUBLE COMMENT 'Numeric value if applicable',
        string_value STRING COMMENT 'String value if applicable',
        boolean_value BOOLEAN COMMENT 'Boolean value if applicable',
        quality STRING COMMENT 'Tag quality (GOOD/BAD/UNCERTAIN)',
        quality_code INT COMMENT 'Numeric quality code',
        source_system STRING COMMENT 'Source Ignition gateway identifier',
        ingestion_timestamp TIMESTAMP COMMENT 'Time data was ingested to Databricks',
        data_type STRING COMMENT 'Original data type from tag',
        alarm_state STRING COMMENT 'Alarm state if applicable',
        alarm_priority INT COMMENT 'Alarm priority if applicable'
    )
    USING DELTA
    COMMENT 'Ignition OT events ingested via Zerobus'
    TBLPROPERTIES (
        'delta.enableChangeDataFeed' = 'true',
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true'
    )
    """
    
    cursor.execute(create_table_sql)
    print(f"✅ Table created: {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")
    
    # Create view
    print(f"Creating view: {CATALOG_NAME}.{SCHEMA_NAME}.vw_recent_events")
    
    create_view_sql = f"""
    CREATE OR REPLACE VIEW {CATALOG_NAME}.{SCHEMA_NAME}.vw_recent_events AS
    SELECT 
        event_time,
        tag_path,
        tag_provider,
        COALESCE(
            CAST(numeric_value AS STRING),
            string_value,
            CAST(boolean_value AS STRING)
        ) AS value,
        quality,
        source_system,
        ingestion_timestamp,
        data_type
    FROM {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}
    WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
    ORDER BY event_time DESC
    """
    
    cursor.execute(create_view_sql)
    print(f"✅ View created: {CATALOG_NAME}.{SCHEMA_NAME}.vw_recent_events")
    
    cursor.close()
    connection.close()
    
    print()
    
except Exception as e:
    print(f"❌ Error setting up Databricks resources: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("⚠️  You may need to:")
    print("   1. Update the warehouse ID for west workspace")
    print("   2. Check you have CREATE CATALOG permissions")
    print()

# Step 3: Grant Permissions
print("📋 Step 3: Granting Permissions to Service Principal...")
print("-" * 80)

if app_id:
    try:
        connection = sql.connect(
            server_hostname=WORKSPACE_HOST,
            http_path="/sql/1.0/warehouses/4b9b953939869799",
            access_token=TOKEN
        )
        
        cursor = connection.cursor()
        
        grants = [
            f"GRANT USE CATALOG ON CATALOG {CATALOG_NAME} TO `{app_id}`",
            f"GRANT USE SCHEMA ON SCHEMA {CATALOG_NAME}.{SCHEMA_NAME} TO `{app_id}`",
            f"GRANT SELECT, MODIFY ON TABLE {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME} TO `{app_id}`"
        ]
        
        for grant_sql in grants:
            print(f"Executing: {grant_sql}")
            cursor.execute(grant_sql)
            print("✅ Granted")
        
        # Verify
        print(f"\nVerifying permissions...")
        cursor.execute(f"SHOW GRANTS ON TABLE {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")
        grants_result = cursor.fetchall()
        
        print(f"Current grants on table:")
        for grant in grants_result:
            if app_id in str(grant):
                print(f"  ✅ {grant}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error granting permissions: {e}")

print()
print("=" * 80)
print("✅ SETUP COMPLETE!")
print("=" * 80)

if client_secret:
    print()
    print("📋 CONFIGURATION FOR IGNITION MODULE:")
    print("-" * 80)
    print(f"Workspace URL:        {WORKSPACE_URL}")
    print(f"Zerobus Endpoint:     {WORKSPACE_HOST}")
    print(f"OAuth Client ID:      {app_id}")
    print(f"OAuth Client Secret:  {client_secret}")
    print(f"Target Table:         {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")
    print(f"Source System:        Ignition-Dev-Mac")
    print("-" * 80)
    print()
    print("📄 Credentials saved to: west_workspace_credentials.json")
    print()
    print("🎯 Next Steps:")
    print("   1. Use these credentials in Ignition module config")
    print("   2. Subscribe to simulator tags")
    print("   3. Enable module")
    print("   4. Verify data in Databricks")
    print()
    print(f"   Query: SELECT * FROM {CATALOG_NAME}.{SCHEMA_NAME}.vw_recent_events LIMIT 10;")
else:
    print()
    print("⚠️  OAuth secret creation failed")
    print("   You'll need to create it manually in the Databricks Account Console")

print()
print("=" * 80)

