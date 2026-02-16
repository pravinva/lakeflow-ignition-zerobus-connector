"""Sync a Databricks workspace repo to a given branch.

Usage:
    python repo_sync.py <repo_path> <branch>

Requires DATABRICKS_CONFIG_PROFILE / DATABRICKS_HOST to be set in the
environment so that WorkspaceClient() can authenticate.
"""

import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import BadRequest


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <repo_path> <branch>", file=sys.stderr)
        sys.exit(2)

    repo_path = sys.argv[1].rstrip("/")
    branch = sys.argv[2]

    w = WorkspaceClient()
    repos = [
        r
        for r in w.repos.list(path_prefix=repo_path)
        if r.path.rstrip("/") == repo_path
    ]
    if not repos:
        print(f"✗ Repo not found at {repo_path}", file=sys.stderr)
        sys.exit(1)

    repo = repos[0]
    try:
        w.repos.update(repo_id=repo.id, branch=branch)
        print(f"✔ Repo {repo.path} (id={repo.id}) synced to {branch}")
    except BadRequest as e:
        msg = str(e).strip()
        if "Conflict pulling from remote" in msg:
            print(
                "✗ Repo sync failed: pull conflicts with local changes.",
                file=sys.stderr,
            )
            print(msg, file=sys.stderr)
            print("", file=sys.stderr)
            print(
                "Resolve in Databricks: open the repo in Workspace → Repos, then:",
                file=sys.stderr,
            )
            print(
                '  • Pull (or switch branch) and choose "Take all incoming changes"'
                " to overwrite local, or",
                file=sys.stderr,
            )
            print(
                "  • Resolve conflicts manually, then re-run: make db-repo-sync",
                file=sys.stderr,
            )
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
