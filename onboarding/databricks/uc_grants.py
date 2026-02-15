"""Unity Catalog GRANT helpers for service principals (connector SP, app SP)."""

from __future__ import annotations

from databricks.sdk import WorkspaceClient


def run_grants(
    w: WorkspaceClient,
    sp_application_id: str,
    catalog: str,
    schema: str,
    warehouse_id: str,
) -> None:
    """Run UC GRANT statements so the principal can use catalog/schema and read/write tables.

    Used for both the Ignition Zerobus connector SP and the Databricks App's SP.
    """
    stmts = [
        f"GRANT USE CATALOG ON CATALOG {catalog} TO `{sp_application_id}`",
        f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{sp_application_id}`",
        f"GRANT MODIFY, SELECT ON SCHEMA {catalog}.{schema} TO `{sp_application_id}`",
        f"GRANT READ VOLUME ON VOLUME {catalog}.{schema}.wheels TO `{sp_application_id}`",
    ]
    print(f"  Running {len(stmts)} GRANT statements...")
    for i, stmt in enumerate(stmts, 1):
        try:
            resp = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=stmt,
                wait_timeout="30s",
            )
            state = ""
            if resp.status:
                state = str(getattr(resp.status, "state", ""))
            if "SUCCEEDED" in state:
                print(f"    [{i}/{len(stmts)}] OK")
            else:
                msg = getattr(resp.status, "message", "") if resp.status else ""
                print(f"    [{i}/{len(stmts)}] WARN: state={state} {msg}")
        except Exception as e:
            print(f"    [{i}/{len(stmts)}] WARN: {e}")
