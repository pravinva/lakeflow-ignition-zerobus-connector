### AGL Energy — Tomago Battery (NSW) — BESS demo tag model (Ignition) — example

This example is a **grid-scale Battery Energy Storage System (BESS)** demo inspired by AGL’s Tomago Battery project:

- **500 MW / 2,000 MWh** (4-hour duration)
- **Tomago, New South Wales (Australia)**
- Delivery partner: **Fluence** (Gridstack Pro)

The intent is a leadership-friendly Asset Intelligence story:

- “What is the battery doing right now (SoC / charge / discharge)?”
- “Are we dispatch-limited, constraint-limited, or thermally derated?”
- “Is performance limited by maintenance or alarms?”
- “What’s the (proxy) revenue impact of constraints vs price?”

## What’s included (4 providers → multi-system narrative)

Create these **Standard Tag Providers** in Ignition:

- `agl_bess` (BESS telemetry: PCS/BMS/HVAC)
- `agl_grid` (POI metering + dispatch/constraints)
- `agl_market` (price + FCAS flags)
- `agl_cmms` (maintenance/work orders)

Import JSONs:

- Provider `agl_bess` → `agl_bess_tomago_site01_tags.json`
- Provider `agl_grid` → `agl_grid_tomago_site01_tags.json`
- Provider `agl_market` → `agl_market_tomago_site01_tags.json`
- Provider `agl_cmms` → `agl_cmms_tomago_site01_tags.json`

## Optional: simulation timer scripts (memory tags)

If you want the tags to “move” without external systems, create 4 Gateway Timer Scripts:

- `timer_script_agl_bess_tomago_site01.py` (1s)
- `timer_script_agl_grid_tomago_site01.py` (1s)
- `timer_script_agl_market_tomago_site01.py` (2s)
- `timer_script_agl_cmms_tomago_site01.py` (10s)

Each provider includes `Diagnostics/*` tags:

- `TickCount` increments on each script tick
- `LastRun/LastStatus/LastError` are self-debug signals

## Tag path convention

All paths follow:

`[provider]AGL/Australia/NSW/Tomago/Site01/...`

Examples:

- `[agl_bess]AGL/Australia/NSW/Tomago/Site01/BESS01/Telemetry/SoC_pct`
- `[agl_grid]AGL/Australia/NSW/Tomago/Site01/Substation01/POI/ExportPower_MW`
- `[agl_market]AGL/Australia/NSW/Tomago/Site01/Market/RRP_AUD_per_MWh`
- `[agl_cmms]AGL/Australia/NSW/Tomago/Site01/CMMS/OpenWorkOrders`

