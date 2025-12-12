# Configure the Ignition Zerobus Connector (Tilt reference)

This is a reference configuration flow for Tilt-style renewables deployments.

## Step 1: Install the module

- In Ignition Gateway: **Config → System → Modules → Install/Upgrade**
- Upload the `.modl` release artifact

## Step 2: Configure the module (REST)

1) Copy `config.template.json` and fill in your values.

2) POST config:

```bash
curl -X POST http://YOUR_IGNITION_GATEWAY:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @config.json
```

Key fields:

- `targetTable`: should be `{{catalog}}.{{schema}}.ot_events_bronze` from this pack
- `sourceSystemId`: stable per site gateway (recommended format: `tilt-<site>-ignition`)

## Step 3: Trigger setup (Ignition version dependent)

- **Ignition 8.3+**: Use Event Streams (see `docs/EVENT_STREAMS_SETUP.md`)
- **Ignition 8.1/8.2**: Use Gateway Tag Change Scripts (see `IGNITION_8.1_SETUP.md`)

Both trigger mechanisms POST to:

- `http://YOUR_IGNITION_GATEWAY:8088/system/zerobus/ingest/batch`

## Step 4: Verify

```bash
curl http://YOUR_IGNITION_GATEWAY:8088/system/zerobus/health
curl http://YOUR_IGNITION_GATEWAY:8088/system/zerobus/diagnostics
```


