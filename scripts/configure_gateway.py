#!/usr/bin/env python3
"""
Interactive Gateway configurator for the Zerobus Connector.

- Reads non-secret fields from a config template (or a path you provide)
- Prompts for oauthClientSecret using a hidden prompt (not echoed)
- POSTs to <gateway_url>/system/zerobus/config

This avoids putting the secret in shell history or in a checked-in config file.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object")
    return data


def _prompt_if_missing(config: Dict[str, Any], key: str, prompt: str) -> None:
    val = str(config.get(key) or "").strip()
    if val:
        return
    entered = input(prompt).strip()
    if not entered:
        raise ValueError(f"Missing required field: {key}")
    config[key] = entered


def _prompt_secret(config: Dict[str, Any], key: str, prompt: str) -> None:
    val = str(config.get(key) or "").strip()
    if val:
        return
    entered = getpass.getpass(prompt).strip()
    if not entered:
        raise ValueError(f"Missing required field: {key}")
    config[key] = entered


def _post_json(url: str, payload: Dict[str, Any], timeout_s: int = 15) -> str:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _get(url: str, timeout_s: int = 10) -> str:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gateway-url",
        default=os.environ.get("GATEWAY_URL", "http://localhost:8099"),
        help="Ignition gateway base URL (default: http://localhost:8099)",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get(
            "ZEROBUS_CONFIG",
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "onboarding",
                "ignition",
                "8.1.50",
                "config",
                "zerobus_config_direct_explicit.json.example",
            ),
        ),
        help="Path to config JSON template (default: onboarding/ignition/8.1.50/config/zerobus_config_direct_explicit.json.example)",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip GET /health and /diagnostics after configuration",
    )
    args = parser.parse_args()

    config = _read_json(args.config)

    # Ensure enabled is true unless explicitly set
    if "enabled" not in config:
        config["enabled"] = True

    # Prompt for required fields (secret hidden)
    _prompt_if_missing(config, "workspaceUrl", "Databricks Workspace URL: ")
    _prompt_if_missing(config, "zerobusEndpoint", "Zerobus Endpoint (workspaceId.zerobus.<region>.cloud.databricks.com): ")
    _prompt_if_missing(config, "oauthClientId", "OAuth Client ID: ")
    _prompt_secret(config, "oauthClientSecret", "OAuth Client Secret (hidden): ")
    _prompt_if_missing(config, "targetTable", "Target table (catalog.schema.table): ")

    post_url = args.gateway_url.rstrip("/") + "/system/zerobus/config"
    try:
        resp_text = _post_json(post_url, config, timeout_s=20)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        print(f"HTTP {e.code} from {post_url}: {err_body}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed to POST config: {e}", file=sys.stderr)
        return 1

    print(f"Configured module via {post_url}")
    if resp_text.strip():
        print(resp_text)

    if not args.skip_health:
        try:
            health = _get(args.gateway_url.rstrip("/") + "/system/zerobus/health")
            diag = _get(args.gateway_url.rstrip("/") + "/system/zerobus/diagnostics")
            print("\n--- /health ---")
            print(health)
            print("\n--- /diagnostics ---")
            print(diag)
        except Exception as e:
            print(f"(Configured, but failed to fetch health/diagnostics: {e})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


