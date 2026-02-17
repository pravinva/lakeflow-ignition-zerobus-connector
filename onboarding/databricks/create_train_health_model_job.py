#!/usr/bin/env python3
"""Create or update the train_health_model Databricks job and run it until the model is registered in UC.

The job runs pipelines/sdp/transformations/train_health_model.py from the repo (Spark Python task),
trains an IsolationForest and registers it to agl_demo.ot.asset_health_model. Waits for the run
to complete and exits 0 only if the run succeeded.

Usage:
  DATABRICKS_CONFIG_PROFILE=daveok uv run --with databricks-sdk python onboarding/databricks/create_train_health_model_job.py --repo-path /Users/david.okeeffe@databricks.com/lakeflow-ignition-zerobus-connector

Optional env:
  CATALOG (default: agl_demo)
  SCHEMA (default: ot)
  REPO_PATH (if not passed via --repo-path)
  JOB_NAME (default: [production] agl-train-health-model)
  RUN_AND_WAIT (default: true) - if false, only create/update job, do not run
  POLL_INTERVAL_SEC (default: 30)
  TIMEOUT_SEC (default: 1800)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterSpec
from databricks.sdk.service.jobs import JobSettings, RunResultState, SparkPythonTask, Task

DEFAULT_CATALOG = "agl_demo"
DEFAULT_SCHEMA = "ot"
DEFAULT_JOB_NAME = "[production] agl-train-health-model"
TRAIN_SCRIPT_SUBPATH = "pipelines/sdp/transformations/train_health_model.py"
# Fallbacks when cluster selectors are not available (e.g. no permission)
DEFAULT_SPARK_VERSION = "14.3.x-scala2.12"
DEFAULT_NODE_TYPE = "Standard_DS3_v2"  # Azure; override with NODE_TYPE_ID env if needed


def normalize_repo_path(path: str) -> str:
    path = path.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def get_cluster_spec(w: WorkspaceClient) -> ClusterSpec:
    try:
        spark_version = w.clusters.select_spark_version(long_term_support=True)
    except Exception:
        spark_version = os.environ.get("SPARK_VERSION", DEFAULT_SPARK_VERSION)
    try:
        node_type_id = w.clusters.select_node_type(local_disk=True)
    except Exception:
        node_type_id = os.environ.get("NODE_TYPE_ID", DEFAULT_NODE_TYPE)
    return ClusterSpec(
        spark_version=spark_version,
        node_type_id=node_type_id,
        num_workers=0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create/update train_health_model job and run until model is registered."
    )
    parser.add_argument(
        "--repo-path",
        default=os.environ.get("REPO_PATH"),
        help="Workspace path to repo root (e.g. /Users/you@databricks.com/repo).",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Only create/update the job; do not run it.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("TIMEOUT_SEC", "1800")),
        help="Max seconds to wait for run (default 1800).",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.environ.get("POLL_INTERVAL_SEC", "30")),
        help="Seconds between run status polls (default 30).",
    )
    args = parser.parse_args()

    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "daveok")
    catalog = os.environ.get("CATALOG", DEFAULT_CATALOG)
    schema = os.environ.get("SCHEMA", DEFAULT_SCHEMA)
    job_name = os.environ.get("JOB_NAME", DEFAULT_JOB_NAME)

    if not args.repo_path:
        print("Provide --repo-path or set REPO_PATH.", file=sys.stderr)
        return 1
    repo_path = normalize_repo_path(args.repo_path)
    python_file = f"{repo_path}/{TRAIN_SCRIPT_SUBPATH}"

    w = WorkspaceClient(profile=profile)
    cluster_spec = get_cluster_spec(w)

    # Find existing job by name
    existing_id = None
    for j in w.jobs.list():
        if j.settings.name == job_name:
            existing_id = j.job_id
            break

    task = Task(
        task_key="train_health_model",
        description="Train IsolationForest and register to UC asset_health_model",
        new_cluster=cluster_spec,
        spark_python_task=SparkPythonTask(python_file=python_file),
    )

    if existing_id:
        print(f"Updating job: {job_name} (id={existing_id})")
        w.jobs.reset(
            job_id=existing_id,
            new_settings=JobSettings(
                name=job_name,
                tasks=[task],
                max_concurrent_runs=1,
            ),
        )
        job_id = existing_id
    else:
        print(f"Creating job: {job_name}")
        created = w.jobs.create(
            name=job_name,
            tasks=[task],
            max_concurrent_runs=1,
        )
        job_id = created.job_id
        print(f"Created job_id={job_id}")

    if args.no_run:
        print("Skipping run (--no-run). Trigger manually or run without --no-run.")
        return 0

    print("Starting run...")
    run = w.jobs.run_now(job_id=job_id)
    run_id = run.run_id
    print(f"Run id: {run_id}")

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        r = w.jobs.get_run(run_id=run_id)
        state = r.state and r.state.life_cycle_state
        result_state = r.state and getattr(r.state, "result_state", None)
        if state == "TERMINATED":
            if result_state == RunResultState.SUCCESS:
                print("Run SUCCESS. Model should be registered in Unity Catalog.")
                return 0
            msg = getattr(r.state, "state_message", "") or ""
            print(f"Run FAILED: result_state={result_state} {msg}", file=sys.stderr)
            return 1
        if state == "INTERNAL_ERROR" or state == "SKIPPED":
            print(f"Run ended with state={state}", file=sys.stderr)
            return 1
        print(f"  Run state: {state} (result_state={result_state}) ... waiting {args.poll_interval}s")
        time.sleep(args.poll_interval)

    print("Run did not complete within timeout.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
