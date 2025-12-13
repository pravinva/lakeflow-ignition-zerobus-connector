# Ignition 8.3.2 Onboarding

## Recommended: Direct tag subscription (no Event Streams, no scripts)

1) Install/upgrade the module (Gateway UI → Config → Modules).

2) Configure explicit tag paths:

```bash
python3 ../../../../scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config ./config/zerobus_config_direct_explicit.json.example
```

3) Verify:

```bash
curl -sS http://localhost:8099/system/zerobus/diagnostics | head -n 120
```

## Optional: Event Streams mode

If you need Designer-level transforms/filters per project, you can use Event Streams
to POST to the module’s ingest endpoint.

### 1) Configure the module (Event Streams config)

```bash
python3 ../../../../scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config ./config/zerobus_config_event_streams.json.example
```

### 2) Configure Event Streams to send to the module

- `POST http://<gateway-host>:<port>/system/zerobus/ingest/batch`

Keep **direct subscription disabled** if you use Event Streams (otherwise you can double-ingest).


