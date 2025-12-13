# Ignition 8.1.50 Onboarding (Direct Subscription + Optional Script Mode)

## Recommended: Direct tag subscription (no Gateway scripts)

1) **Install/upgrade** the module in Gateway UI (Modules → Install/Upgrade).

2) **Configure** with explicit tag paths:

```bash
python3 ../../../../scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config ./config/zerobus_config_direct_explicit.json.example
```

3) **Verify**:

```bash
curl -sS http://localhost:8099/system/zerobus/diagnostics | head -n 120
```

You should see:
- `Module Enabled: true`
- `Direct Subscriptions: <N> tags`
- `Total Events Received/Sent` increasing

## Optional: Gateway Tag Change Script → HTTP ingest

Use this if you prefer scripts or can’t use direct subscriptions.

1) Keep module config enabled (same `configure_gateway.py` flow).
2) In Ignition Designer: Project → Gateway Events → Tag Change
3) Paste the script from `gateway_scripts/tag_change_forwarder_http.py`
4) Ensure you do **not** also enable direct subscriptions, or you’ll double-ingest.


