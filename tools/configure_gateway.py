#!/usr/bin/env python3
"""
Configure Ignition Zerobus Connector via REST without pasting secrets into curl.

Typical flow:
  1) Generate a non-secret config.json (from Databricks notebook or template)
  2) Run this script on your laptop (same machine/network as the Ignition Gateway)
  3) The script prompts for any missing values (including oauthClientSecret) and POSTs.

Usage examples:
  python3 tools/configure_gateway.py --gateway-url http://localhost:8099 --config config.json
  python3 tools/configure_gateway.py --config config.json --secret-env OAUTH_CLIENT_SECRET
  OAUTH_CLIENT_SECRET=... python3 tools/configure_gateway.py --config config.json --no-prompt
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


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def _prompt_if_missing(cfg: Dict[str, Any], key: str, prompt: str, secret: bool = False) -> None:
    if cfg.get(key):
        return
    if secret:
        val = getpass.getpass(prompt)
    else:
        val = input(prompt)
    cfg[key] = val.strip()


def _http_get(url: str) -> str:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "ignore")


def _http_post_json(url: str, payload: Dict[str, Any]) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gateway-url", default="http://localhost:8099", help="Ignition gateway base URL")
    ap.add_argument("--config", default="config.json", help="Path to config.json (typically without secrets)")
    ap.add_argument(
        "--secret-env",
        default="",
        help="Env var name that contains oauthClientSecret (e.g. OAUTH_CLIENT_SECRET).",
    )
    ap.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt for missing fields; fail instead.",
    )
    ap.add_argument(
        "--write-back",
        action="store_true",
        help="Write the final merged config (including secret) back to --config (not recommended).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print final config (redacting secret) but do not POST.",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="After POST, GET /health and /diagnostics and print results.",
    )
    args = ap.parse_args()

    gateway = args.gateway_url.rstrip("/")
    cfg = _load_json(args.config)

    # Fill secret from env if requested.
    if args.secret_env:
        env_val = os.environ.get(args.secret_env, "")
        if env_val and not cfg.get("oauthClientSecret"):
            cfg["oauthClientSecret"] = env_val

    required = [
        "workspaceUrl",
        "zerobusEndpoint",
        "oauthClientId",
        "oauthClientSecret",
        "targetTable",
        "sourceSystemId",
    ]

    if args.no_prompt:
        missing = [k for k in required if not cfg.get(k)]
        if missing:
            print(f"ERROR: missing required fields in {args.config}: {', '.join(missing)}", file=sys.stderr)
            return 2
    else:
        _prompt_if_missing(cfg, "workspaceUrl", "Databricks workspaceUrl: ")
        _prompt_if_missing(cfg, "zerobusEndpoint", "Zerobus endpoint (WORKSPACE_ID.zerobus.REGION...): ")
        _prompt_if_missing(cfg, "oauthClientId", "OAuth client id (Application ID): ")
        _prompt_if_missing(cfg, "oauthClientSecret", "OAuth client secret (hidden): ", secret=True)
        _prompt_if_missing(cfg, "targetTable", "Target table (catalog.schema.table): ")
        _prompt_if_missing(cfg, "sourceSystemId", "sourceSystemId: ")

    # Default enable if not present
    if "enabled" not in cfg:
        cfg["enabled"] = True

    if args.dry_run:
        redacted = dict(cfg)
        if redacted.get("oauthClientSecret"):
            redacted["oauthClientSecret"] = "*****"
        print(json.dumps(redacted, indent=2))
        return 0

    # POST config
    post_url = f"{gateway}/system/zerobus/config"
    try:
        resp = _http_post_json(post_url, cfg)
        print(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore") if hasattr(e, "read") else ""
        print(f"HTTP {e.code} POST {post_url}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR posting config: {type(e).__name__}: {e}", file=sys.stderr)
        return 4

    if args.write_back:
        _save_json(args.config, cfg)
        print(f"Wrote updated config to {args.config}")

    if args.verify:
        for suffix in ["/system/zerobus/health", "/system/zerobus/diagnostics"]:
            url = gateway + suffix
            try:
                print(f"\nGET {url}")
                print(_http_get(url)[:4000])
            except Exception as e:
                print(f"ERROR GET {url}: {type(e).__name__}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


