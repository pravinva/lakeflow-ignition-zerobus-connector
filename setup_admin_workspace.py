#!/usr/bin/env python3
"""
Setup script for admin workspace.
Creates all necessary resources for Ignition → Databricks integration.
"""

from databricks import sql
import requests
import json
import os
import uuid
from datetime import datetime

# Admin workspace configuration
WORKSPACE_HOST = "dbc-8cee2ece-f274.cloud.databricks.com"
WORKSPACE_URL = f"https://{WORKSPACE_HOST}"
TOKEN = os.environ.get("DATABRICKS_TOKEN") or "<your-token-from-~/.databrickscfg>"

# Configuration
CATALOG_NAME = "lakeflow_ignition"
SCHEMA_NAME = "ot_data"
TABLE_NAME = "bronze_events"
SP_NAME = "zerobus-sp"

print("=" * 80)
print("🚀 SETTING UP ADMIN WORKSPACE FOR IGNITION → DATABRICKS")
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
    print(f"   Application ID (Client ID): {app_id}")
    print(f"   Service Principal ID: {sp_id}")
    
    # Create OAuth secret
    print(f"\n📝 Creating OAuth Secret...")
    
    # Try different API endpoints for secret creation
    secret_created = False
    client_secret = None
    
    # Method 1: SCIM API
    secret_response = requests.post(
        f"{WORKSPACE_URL}/api/2.0/preview/scim/v2/ServicePrincipals/{sp_id}/secrets",
        headers=headers,
        json={"description": "Ignition Zerobus Module"}
    )
    
    if secret_response.status_code in [200, 201]:
        secret_data = secret_response.json()
        client_secret = secret_data.get('secret', {}).get('value') or secret_data.get('value')
        if client_secret:
            secret_created = True
            print(f"✅ OAuth Secret Created via SCIM API!")
    
    # Method 2: Account API (if Method 1 failed)
    if not secret_created:
        secret_response2 = requests.post(
            f"{WORKSPACE_URL}/api/2.0/account/servicePrincipals/{sp_id}/credentials/secrets",
            headers=headers,
            json={"description": "Ignition Zerobus Module"}
        )
        
        if secret_response2.status_code in [200, 201]:
            secret_data = secret_response2.json()
            client_secret = secret_data.get('secret') or secret_data.get('value')
            if client_secret:
                secret_created = True
                print(f"✅ OAuth Secret Created via Account API!")
    
    if secret_created and client_secret:
        print(f"   Client ID:     {app_id}")
        print(f"   Client Secret: {client_secret}")
        print()
        print("   ⚠️  SAVE THESE CREDENTIALS - Secret won't be shown again!")
        
        # Save to config file
        config = {
            "workspace": "admin-workspace",
            "workspaceUrl": WORKSPACE_URL,
            "workspaceHost": WORKSPACE_HOST,
            "zerobusEndpoint": WORKSPACE_HOST,
            "oauthClientId": app_id,
            "oauthClientSecret": client_secret,
            "servicePrincipalId": sp_id,
            "targetTable": f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}",
            "createdAt": datetime.now().isoformat()
        }
        
        with open('admin_workspace_credentials.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("   📄 Credentials saved to: admin_workspace_credentials.json")
    else:
        print(f"⚠️  OAuth secret creation failed")
        print(f"   SCIM API Status: {secret_response.status_code}")
        print(f"   Response: {secret_response.text[:200]}")
        print()
        print("   You can create OAuth secret manually:")
        print(f"   1. Go to: {WORKSPACE_URL}/settings/workspace/service-principals")
        print(f"   2. Find: {SP_NAME}")
        print(f"   3. Generate OAuth secret")
        client_secret = "MANUALLY_CREATED_SECRET"
else:
    print(f"❌ Failed to create service principal: {response.status_code}")
    print(f"   Response: {response.text}")
    print()
    print("   Trying to find existing service principal...")
    
    # Try to get existing SP
    list_response = requests.get(
        f"{WORKSPACE_URL}/api/2.0/preview/scim/v2/ServicePrincipals",
        headers=headers
    )
    
    if list_response.status_code == 200:
        sps = list_response.json().get('Resources', [])
        existing_sp = next((sp for sp in sps if sp.get('displayName') == SP_NAME), None)
        
        if existing_sp:
            print(f"   ✅ Found existing service principal: {SP_NAME}")
            app_id = existing_sp.get('applicationId')
            sp_id = existing_sp.get('id')
            print(f"   Application ID: {app_id}")
            print(f"   Service Principal ID: {sp_id}")
            client_secret = "USE_EXISTING_SECRET"
        else:
            print("   ❌ No existing service principal found")
            exit(1)
    else:
        exit(1)

print()

# Step 2: Find or Create Warehouse
print("📋 Step 2: Finding Serverless Warehouse...")
print("-" * 80)

warehouse_response = requests.get(
    f"{WORKSPACE_URL}/api/2.0/sql/warehouses",
    headers=headers
)

warehouse_id = None
if warehouse_response.status_code == 200:
    warehouses = warehouse_response.json().get('warehouses', [])
    
    # Look for serverless warehouse
    serverless = next((w for w in warehouses if w.get('enable_serverless_compute') == True), None)
    
    if serverless:
        warehouse_id = serverless.get('id')
        print(f"✅ Found serverless warehouse: {serverless.get('name')}")
        print(f"   Warehouse ID: {warehouse_id}")
    elif warehouses:
        # Use first available warehouse
        warehouse_id = warehouses[0].get('id')
        print(f"✅ Using warehouse: {warehouses[0].get('name')}")
        print(f"   Warehouse ID: {warehouse_id}")
    else:
        print("⚠️  No warehouses found - you may need to create one")

print()

# Step 3: Create Catalog, Schema, Table
if warehouse_id:
    print("📋 Step 3: Setting up Databricks Resources...")
    print("-" * 80)
    
    try:
        connection = sql.connect(
            server_hostname=WORKSPACE_HOST,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=TOKEN
        )
        
        cursor = connection.cursor()
        
        # Create catalog
        print(f"Creating catalog: {CATALOG_NAME}")
        try:
            cursor.execute(f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}")
            print(f"✅ Catalog created: {CATALOG_NAME}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"✅ Catalog already exists: {CATALOG_NAME}")
            else:
                print(f"⚠️  Error creating catalog: {e}")
        
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

# Step 4: Grant Permissions
if warehouse_id and app_id:
    print("📋 Step 4: Granting Permissions to Service Principal...")
    print("-" * 80)
    
    try:
        connection = sql.connect(
            server_hostname=WORKSPACE_HOST,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
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
            try:
                cursor.execute(grant_sql)
                print("✅ Granted")
            except Exception as e:
                print(f"⚠️  {e}")
        
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

if client_secret and client_secret != "MANUALLY_CREATED_SECRET" and client_secret != "USE_EXISTING_SECRET":
    print()
    print("📋 CONFIGURATION FOR IGNITION MODULE:")
    print("-" * 80)
    print(f"Workspace URL:        {WORKSPACE_URL}")
    print(f"Zerobus Endpoint:     {WORKSPACE_HOST}")
    print(f"OAuth Client ID:      {app_id}")
    print(f"OAuth Client Secret:  {client_secret}")
    print(f"Target Table:         {CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}")
    print(f"Source System:        Ignition-Dev-Mac")
    print(f"Warehouse ID:         {warehouse_id}")
    print("-" * 80)
    print()
    print("📄 Full config saved to: admin_workspace_credentials.json")
else:
    print()
    print("⚠️  OAuth secret needs to be created manually or retrieved")
    print(f"   Service Principal Application ID: {app_id}")
    print(f"   Go to: {WORKSPACE_URL}/settings/workspace/service-principals")

print()
print("🎯 Next Steps:")
print("   1. Use these credentials to configure Ignition module")
print("   2. Configure Generic Simulator in Ignition")
print("   3. Subscribe to simulator tags")
print("   4. Enable module and verify data flow")
print()
print(f"   Test Query: SELECT * FROM {CATALOG_NAME}.{SCHEMA_NAME}.vw_recent_events LIMIT 10;")
print()
print("=" * 80)

