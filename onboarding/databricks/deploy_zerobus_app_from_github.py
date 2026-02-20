#!/usr/bin/env python3
"""Deploy zerobus-ignition-agl app from GitHub using the SDK (create/get app, set Git credential on SP, deploy).

After deployment, runs UC grants for the app's service principal (USE CATALOG, USE SCHEMA, etc.)
so the app can query agl_demo.ot. Use a profile that can manage apps and run GRANTs (e.g. your user profile).

Usage:
  export GITHUB_PAT=ghp_xxxx   # required for private repo
  export GITHUB_USER=dgokeeffe  # optional, for git_username
  uv run python onboarding/databricks/deploy_zerobus_app_from_github.py

  # Grant-only: run UC grants for the app SP without deploying (e.g. after deploy with a different profile)
  uv run python onboarding/databricks/deploy_zerobus_app_from_github.py --grant-only

Or with Databricks profile:
  DATABRICKS_CONFIG_PROFILE=daveok uv run python onboarding/databricks/deploy_zerobus_app_from_github.py

Env: CATALOG (default agl_demo), SCHEMA (default ot), DATABRICKS_WAREHOUSE_ID (for running GRANT statements).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure repo root is on path when run as: uv run python onboarding/databricks/deploy_zerobus_app_from_github.py
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import (
    App,
    AppDeployment,
    AppDeploymentMode,
    AppResource,
    AppResourceSqlWarehouse,
    AppResourceSqlWarehouseSqlWarehousePermission,
    GitRepository,
    GitSource,
)

from onboarding.databricks.uc_grants import run_grants as run_uc_grants

APP_NAME = "zerobus-ignition-agl"
GIT_URL = "https://github.com/dgokeeffe/lakeflow-ignition-zerobus-connector"
GIT_BRANCH = "main"
GIT_PROVIDER = "gitHub"

DEFAULT_CATALOG = "agl_demo"
DEFAULT_SCHEMA = "ot"
DEFAULT_WAREHOUSE_ID = "e4082fdb7ea19a15"


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy zerobus-ignition-agl app from GitHub and grant app SP UC permissions")
    parser.add_argument(
        "--grant-only",
        action="store_true",
        help="Only run UC grants for the app's service principal (skip create/deploy)",
    )
    args = parser.parse_args()

    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "daveok")
    w = WorkspaceClient(profile=profile)

    # Resolve repo URL (allow override)
    git_url = os.environ.get("APP_GIT_URL", GIT_URL)
    branch = os.environ.get("APP_GIT_BRANCH", GIT_BRANCH)

    catalog = os.environ.get("CATALOG", DEFAULT_CATALOG)
    schema = os.environ.get("SCHEMA", DEFAULT_SCHEMA)
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", DEFAULT_WAREHOUSE_ID)

    # Build the SQL warehouse resource (must be attached to the app)
    sql_warehouse_resource = AppResource(
        name="sql-warehouse",  # This matches the valueFrom in app.yaml
        description="SQL warehouse for running queries",
        sql_warehouse=AppResourceSqlWarehouse(
            id=warehouse_id,
            permission=AppResourceSqlWarehouseSqlWarehousePermission.CAN_USE,
        ),
    )

    # Step 1: Get existing app or create with git_repository
    try:
        app = w.apps.get(name=APP_NAME)
        print(f"Using existing app: {APP_NAME} (service_principal_id={app.service_principal_id})")

        # Check if app already has the sql-warehouse resource
        existing_resources = app.resources or []
        has_warehouse = any(r.name == "sql-warehouse" for r in existing_resources)
        if not has_warehouse:
            print(f"Adding sql-warehouse resource (warehouse_id={warehouse_id}) to existing app...")
            app = w.apps.update(
                name=APP_NAME,
                app=App(
                    name=APP_NAME,
                    description=app.description,
                    resources=[sql_warehouse_resource],
                ),
            )
            print("SQL warehouse resource added.")
        else:
            print("App already has sql-warehouse resource.")
    except Exception:
        if args.grant_only:
            print(f"App {APP_NAME} not found; cannot run grants.", file=sys.stderr)
            sys.exit(1)
        print(f"Creating app {APP_NAME} with git_repository={git_url}")
        try:
            app = w.apps.create(
                app=App(
                    name=APP_NAME,
                    description="Zerobus Ignition AGL – OT tag streaming and asset framework demo (from GitHub)",
                    git_repository=GitRepository(url=git_url, provider=GIT_PROVIDER),
                    resources=[sql_warehouse_resource],
                )
            ).result()
            print(f"Created app: service_principal_id={app.service_principal_id}")
        except Exception as e:
            err_msg = str(e).lower()
            if "git repository cannot be defined" in err_msg or "please try again later" in err_msg:
                print(
                    f"✘ Git-backed apps are not available in this workspace yet: {e}\n"
                    "  This often happens on newly created workspaces (feature propagation).\n"
                    "  Options:\n"
                    "    1. Wait a few hours and run again: make db-app-deploy\n"
                    "    2. Deploy via Asset Bundle: make db-bundle-deploy (see databricks.yml)\n"
                    "    3. In the workspace: Settings → check Repos/Apps and enable if needed",
                    file=sys.stderr,
                )
                sys.exit(1)
            raise

    sp_id = app.service_principal_id
    if not sp_id:
        print("App has no service_principal_id; cannot attach Git credential or run grants.", file=sys.stderr)
        sys.exit(1)

    # UC GRANTs require the SP's application_id (UUID), not the workspace principal id
    try:
        sp = w.service_principals.get(id=str(sp_id))
        sp_application_id = sp.application_id or str(sp_id)
    except Exception:
        sp_application_id = str(sp_id)
    if args.grant_only:
        print(f"▸ Grant-only: running UC grants for app SP on {catalog}.{schema}...")
        run_uc_grants(w, sp_application_id, catalog, schema, warehouse_id)
        print("Done.")
        return

    # Step 2: Add Git credential to the app's service principal (for private repo clone)
    pat = os.environ.get("GITHUB_PAT")
    git_username = os.environ.get("GITHUB_USER", "dgokeeffe")
    if pat:
        try:
            w.git_credentials.create(
                git_provider=GIT_PROVIDER,
                personal_access_token=pat,
                git_username=git_username,
                principal_id=sp_id,
            )
            print("Git credential set for app service principal.")
        except Exception as e:
            # May already exist
            print(f"Git credential create: {e}")
    else:
        print("GITHUB_PAT not set; skipping Git credential (ok for public repo).")

    # Step 3: Deploy from Git (repo url/provider are on the app; only pass branch + optional source_code_path)
    source_code_path = os.environ.get("APP_SOURCE_CODE_PATH", "demo/app")
    print(f"Deploying branch={branch} source_code_path={source_code_path} ...")
    try:
        deployment = w.apps.deploy(
            app_name=APP_NAME,
            app_deployment=AppDeployment(
                git_source=GitSource(
                    branch=branch,
                    source_code_path=source_code_path,
                ),
                mode=AppDeploymentMode.SNAPSHOT,
            ),
        ).result()
        print("Deployment result:", deployment)
    except Exception as e:
        if "active deployment in progress" in str(e).lower():
            print(f"App already has a deployment in progress — skipping. Check status in the workspace UI.")
        else:
            raise

    # Step 4: Run UC grants for the app's service principal so the app can query agl_demo.ot
    print(f"▸ Running UC grants for app SP (catalog={catalog}, schema={schema})...")
    run_uc_grants(w, sp_application_id, catalog, schema, warehouse_id)

    print("Done. Start the app from the workspace UI or: databricks bundle run zerobus_ignition_agl -t dev")


if __name__ == "__main__":
    main()
