#!/usr/bin/env python3
"""Create or update the AGL ETL pipeline via the Databricks SDK, pointing to a Git folder in the workspace.

Pipeline root_path = <repo_path>/pipelines/sdp; libraries = transformations/** (absolute path).
Environment uses the agl_analytics wheel from the UC volume (no -e workspace install; clusters
often fail to install editable workspace paths). Ensure the wheel is in the volume before running
the pipeline: run setup SQL, then `uv build pipelines/sdp` and upload dist/agl_analytics-0.1.0-py3-none-any.whl
to /Volumes/<catalog>/<schema>/wheels/.

Usage:
  ... deploy_pipeline_sdk.py --repo-path /Users/david.okeeffe@databricks.com/lakeflow-ignition-zerobus-connector

Optional env (same as run_setup_sql.py):
  CATALOG (default: agl_demo)
  SCHEMA (default: ot)
  PIPELINE_NAME (default: [production] agl-etl)
"""

from __future__ import annotations

import argparse
import os
import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import pipelines as pipelines_api

DEFAULT_CATALOG = "agl_demo"
DEFAULT_SCHEMA = "ot"
DEFAULT_PIPELINE_NAME = "[production] agl-etl"
SDP_SUBPATH = "pipelines/sdp"
WHEEL_FILENAME = "agl_analytics-0.1.0-py3-none-any.whl"


def normalize_repo_path(path: str) -> str:
    """Ensure path is absolute workspace path (starts with /)."""
    path = path.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or update AGL ETL pipeline from a Git folder in the workspace."
    )
    parser.add_argument(
        "--repo-path",
        required=True,
        help="Workspace path to the repo root. For a browse URL .../browse/folders/<id>, open the folder and copy the path from the breadcrumb (e.g. /Users/<you>@databricks.com/lakeflow-ignition-zerobus-connector).",
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="If set, fail when pipeline already exists instead of updating.",
    )
    parser.add_argument(
        "--upload-wheel",
        action="store_true",
        help="Build the wheel (if needed) and upload it to the UC volume before updating the pipeline.",
    )
    args = parser.parse_args()

    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "agl-demo")
    catalog = os.environ.get("CATALOG", DEFAULT_CATALOG)
    schema = os.environ.get("SCHEMA", DEFAULT_SCHEMA)
    pipeline_name = os.environ.get("PIPELINE_NAME", DEFAULT_PIPELINE_NAME)

    w = WorkspaceClient(profile=profile)
    repo_path = normalize_repo_path(args.repo_path)

    root_path = f"{repo_path}/{SDP_SUBPATH}"
    # Use wheel from UC volume (editable -e workspace path fails on cluster install)
    wheel_path = f"/Volumes/{catalog}/{schema}/wheels/{WHEEL_FILENAME}"

    if args.upload_wheel:
        # Build and upload wheel to volume (requires volume to exist from setup SQL)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        sdp_dir = os.path.join(repo_root, "pipelines", "sdp")
        local_whl = os.path.join(sdp_dir, "dist", WHEEL_FILENAME)
        if not os.path.isfile(local_whl):
            import subprocess
            subprocess.run(["uv", "build", "pipelines/sdp"], cwd=repo_root, check=True)
            if not os.path.isfile(local_whl):
                print(f"Wheel not found at {local_whl}", file=sys.stderr)
                return 1
        print(f"Uploading {local_whl} -> {wheel_path}")
        w.files.upload_from(file_path=wheel_path, source_path=local_whl, overwrite=True)

    # Resolve pipeline by name (list and find)
    existing_id = None
    for p in w.pipelines.list_pipelines():
        if p.name == pipeline_name:
            existing_id = p.pipeline_id
            break

    # Glob include must be an absolute workspace path (path doesn't start with '/' otherwise)
    lib_glob = pipelines_api.PipelineLibrary(
        glob=pipelines_api.PathPattern(include=f"{root_path}/transformations/**")
    )
    env = pipelines_api.PipelinesEnvironment(dependencies=[wheel_path])

    if existing_id:
        if args.create_only:
            print(f"Pipeline already exists: {pipeline_name} (id={existing_id}). Use without --create-only to update.", file=sys.stderr)
            return 1
        print(f"Updating pipeline: {pipeline_name} (id={existing_id})")
        w.pipelines.update(
            pipeline_id=existing_id,
            name=pipeline_name,
            catalog=catalog,
            schema=schema,
            root_path=root_path,
            libraries=[lib_glob],
            environment=env,
            serverless=True,
            development=False,
            channel="PREVIEW",
            photon=True,
            continuous=False,
        )
        print(f"Updated. root_path={root_path}")
        return 0
    else:
        print(f"Creating pipeline: {pipeline_name}")
        created = w.pipelines.create(
            name=pipeline_name,
            catalog=catalog,
            schema=schema,
            root_path=root_path,
            libraries=[lib_glob],
            environment=env,
            serverless=True,
            development=False,
            channel="PREVIEW",
            photon=True,
            continuous=False,
        )
        print(f"Created pipeline_id={created.pipeline_id} root_path={root_path}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
