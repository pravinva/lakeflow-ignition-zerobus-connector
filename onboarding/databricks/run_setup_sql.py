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
  WAREHOUSE_ID (default: e65d34bf5b095b0f)
"""

from __future__ import annotations

import os
import re
import sys

from databricks.sdk import WorkspaceClient


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SETUP_SQL = os.path.join(REPO_ROOT, "examples/agl_fleet/setup_databricks.sql")
DEFAULT_WAREHOUSE_ID = "e65d34bf5b095b0f"
DEFAULT_CATALOG = "agl_demo"
DEFAULT_SCHEMA = "ot"
DEFAULT_SP_APPLICATION_ID = "66c066ad-d5a9-496f-8da5-6d7bc2f5d954"


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
    warehouse_id = os.environ.get("WAREHOUSE_ID", DEFAULT_WAREHOUSE_ID)
    catalog = os.environ.get("CATALOG", DEFAULT_CATALOG)
    schema = os.environ.get("SCHEMA", DEFAULT_SCHEMA)
    sp_id = os.environ.get("SP_APPLICATION_ID", DEFAULT_SP_APPLICATION_ID)

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
    print(f"Running {len(statements)} statements from {SETUP_SQL}")
    print(f"  CATALOG={catalog} SCHEMA={schema} SP_APPLICATION_ID={sp_id} warehouse_id={warehouse_id}")

    w = WorkspaceClient(profile=profile)

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
                print(f"      -> state={state} message={msg} error={err_str}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"      FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Done. Catalog {catalog}, schema {schema}, tables, volume wheels, and SP grants created.")


if __name__ == "__main__":
    main()
