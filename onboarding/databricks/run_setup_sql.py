#!/usr/bin/env python3
"""Run examples/agl_fleet/setup_databricks.sql via Databricks Statement Execution API.

Replaces __CATALOG__, __SCHEMA__, __SP_APPLICATION_ID__ from env (defaults: agl_demo, ot,
66c066ad-d5a9-496f-8da5-6d7bc2f5d954) then executes each statement.

Usage:
  DATABRICKS_CONFIG_PROFILE=daveok uv run --with databricks-sdk python onboarding/databricks/run_setup_sql.py

Optional env:
  CATALOG (default: agl_demo)
  SCHEMA (default: ot)
  SP_APPLICATION_ID (default: 66c066ad-d5a9-496f-8da5-6d7bc2f5d954)
  DATABRICKS_WAREHOUSE_ID (default: e4082fdb7ea19a15)
  SKIP_CATALOG_CREATE (set to 1 if catalog already exists or you lack CREATE CATALOG on metastore)
"""

from __future__ import annotations

import os
import re
import sys

from databricks.sdk import WorkspaceClient


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SETUP_SQL = os.path.join(REPO_ROOT, "examples/agl_fleet/setup_databricks.sql")
DEFAULT_WAREHOUSE_ID = "e4082fdb7ea19a15"
DEFAULT_CATALOG = "agl_demo"
DEFAULT_SCHEMA = "ot"
DEFAULT_SP_APPLICATION_ID = "66c066ad-d5a9-496f-8da5-6d7bc2f5d954"


def _host_from_profile(profile: str) -> str | None:
    """Read host for profile from ~/.databrickscfg."""
    path = os.path.expanduser("~/.databrickscfg")
    if not os.path.isfile(path):
        return None
    in_section = False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                in_section = line[1:-1].strip() == profile
                continue
            if in_section and line.startswith("host") and "=" in line:
                return line.split("=", 1)[1].strip()
    return None


def split_sql(content: str) -> list[str]:
    """Split SQL into statements by ; at end of line; drop comment-only and empty."""
    statements = []
    for raw in re.split(r";\s*\n", content):
        # Drop full-line comments and empty lines, keep the rest
        lines = []
        for line in raw.splitlines():
            s = line.strip()
            if s and not s.startswith("--"):
                lines.append(line)
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


def main() -> None:
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "agl-demo")
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", DEFAULT_WAREHOUSE_ID)
    catalog = os.environ.get("CATALOG", DEFAULT_CATALOG)
    schema = os.environ.get("SCHEMA", DEFAULT_SCHEMA)
    sp_id = os.environ.get("SP_APPLICATION_ID", DEFAULT_SP_APPLICATION_ID)
    skip_catalog_create = os.environ.get("SKIP_CATALOG_CREATE", "").strip().lower() in ("1", "true", "yes")

    if not os.path.isfile(SETUP_SQL):
        print(f"Not found: {SETUP_SQL}", file=sys.stderr)
        sys.exit(1)

    with open(SETUP_SQL) as f:
        sql_content = f.read()

    sql_content = (
        sql_content.replace("__CATALOG__", catalog)
        .replace("__SCHEMA__", schema)
        .replace("__SP_APPLICATION_ID__", sp_id)
    )
    statements = split_sql(sql_content)
    if skip_catalog_create:
        # Drop only the first statement if it is CREATE CATALOG IF NOT EXISTS <catalog>;
        create_catalog_re = re.compile(
            r"^\s*CREATE\s+CATALOG\s+IF\s+NOT\s+EXISTS\s+" + re.escape(catalog) + r"\s*;\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        if statements and create_catalog_re.match(statements[0].strip()):
            statements = statements[1:]
            print(f"Skipping CREATE CATALOG (SKIP_CATALOG_CREATE=1); running {len(statements)} statements.")
    print(f"Running {len(statements)} statements from {SETUP_SQL}")
    print(f"  CATALOG={catalog} SCHEMA={schema} SP_APPLICATION_ID={sp_id} warehouse_id={warehouse_id}")

    try:
        w = WorkspaceClient(profile=profile)
    except Exception as e:
        host = _host_from_profile(profile) or os.environ.get("DATABRICKS_HOST")
        login_hint = (
            f"  Log in to the workspace (profile [{profile}]):\n"
            f"    databricks auth login --host {host}\n"
            f"  Then re-run: make db-setup-sql"
            if host
            else (
                f"  Log in: databricks auth login (then set DATABRICKS_CONFIG_PROFILE={profile})\n"
                "  If you ran make db-clear-account-cache, re-login to the workspace too."
            )
        )
        print(
            f"✘ Failed to connect with profile [{profile}]: {e}\n"
            f"{login_hint}",
            file=sys.stderr,
        )
        sys.exit(1)

    for i, stmt in enumerate(statements):
        # First line for logging (e.g. CREATE CATALOG...)
        first_line = stmt.split("\n")[0][:70]
        print(f"  [{i+1}/{len(statements)}] {first_line}...")
        try:
            resp = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=stmt,
                wait_timeout="30s",
            )
            status = getattr(resp, "status", None)
            state = getattr(status, "state", None) if status else None
            ok = state is not None and (state == "SUCCEEDED" or str(state).endswith("SUCCEEDED"))
            if not ok:
                msg = getattr(status, "message", "") if status else ""
                err = getattr(status, "error", None) if status else None
                err_str = ""
                if err:
                    err_str = getattr(err, "message", "") or str(err)
                # raw_tags may be a view (old) or table (current); one of DROP VIEW / DROP TABLE will fail
                drop_raw_tags = "raw_tags" in stmt and (
                    stmt.strip().upper().startswith("DROP VIEW ")
                    or stmt.strip().upper().startswith("DROP TABLE ")
                )
                wrong_type = "Cannot drop a table with DROP VIEW" in err_str or "Cannot drop a view with DROP TABLE" in err_str
                if drop_raw_tags and wrong_type:
                    print(f"      -> (ignored: object is other type) {first_line}...")
                else:
                    is_create_catalog = "CREATE CATALOG" in stmt.upper() and "IF NOT EXISTS" in stmt.upper()
                    if is_create_catalog and ("PERMISSION_DENIED" in err_str or "CREATE CATALOG" in err_str):
                        print(
                            f"      -> {err_str}\n"
                            "  You do not have CREATE CATALOG on the metastore.\n"
                            "  Option 1: Ask a metastore admin to run once in SQL:\n"
                            f"    CREATE CATALOG IF NOT EXISTS {catalog};\n"
                            "  Then re-run this script with:\n"
                            f"    SKIP_CATALOG_CREATE=1 make db-setup-sql\n"
                            "  Option 2: Have the admin run the full setup SQL (this file) once.",
                            file=sys.stderr,
                        )
                    else:
                        if "UC_CLOUD_STORAGE_ACCESS_FAILURE" in err_str or "cloud storage" in err_str.lower():
                            print(
                                f"      -> {err_str}\n"
                                "  Unity Catalog cannot access the metastore/catalog storage (Azure).\n"
                                "  Check: Account console → Data → Metastore → root storage location and\n"
                                "  ensure the metastore identity has access to the Azure storage account.",
                                file=sys.stderr,
                            )
                        else:
                            print(f"      -> state={state} message={msg} error={err_str}", file=sys.stderr)
                            print(f"      Failing statement [{i+1}/{len(statements)}]:\n{stmt[:500]}...", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            err_str = str(e)
            if "UC_CLOUD_STORAGE_ACCESS_FAILURE" in err_str or "cloud storage" in err_str.lower():
                print(
                    f"      FAILED: {e}\n"
                    "  Unity Catalog cannot access metastore/catalog storage. Check metastore root location and Azure access.",
                    file=sys.stderr,
                )
            else:
                print(f"      FAILED: {e}", file=sys.stderr)
                print(f"      Failing statement [{i+1}/{len(statements)}]:\n{stmt[:500]}...", file=sys.stderr)
            sys.exit(1)

    print(f"Done. Catalog {catalog}, schema {schema}, tables, volume wheels, and SP grants created.")


if __name__ == "__main__":
    main()
