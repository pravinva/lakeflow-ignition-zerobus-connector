## Saint-Gobain “Glass Line” simulation (Ignition) — business demo

This demo is modeled after a **multi-plant manufacturing** story (glass production) where Saint-Gobain has:

- Local plant OT equipment → Local Ignition
- OT/IT boundary (firewall/VPN/PrivateLink)
- Central Databricks lakehouse (Bronze → Silver → Gold)
- Multiple downstream consumers (BI, SAP, APIs)

### Provider names (recommended)

Use **separate providers per customer** so you can share a single Bronze table and still keep mapping clean:

- `sg` (plant telemetry)
- `sg_grid` (grid/dispatch inputs)
- `sg_cmms` (maintenance/work orders)
- `sg_forecast` (forecast)

> These can run alongside the Tilt demo on the same host.

### What’s included

Import JSON exports into the corresponding providers:

- `sg_site01_tags.json` → provider `sg`
- `sg_grid_site01_tags.json` → provider `sg_grid`
- `sg_cmms_site01_tags.json` → provider `sg_cmms`
- `sg_forecast_site01_tags.json` → provider `sg_forecast`

Gateway Timer Scripts (top-level scripts; paste as-is):

- `timer_script_sg_site01_plant.py` (1s)
- `timer_script_sg_site01_grid.py` (1s)
- `timer_script_sg_site01_cmms.py` (2s)
- `timer_script_sg_site01_forecast.py` (5s)

### Demo tag model (glass production line)

`[sg]SG/Site01/...`

- Furnace (melting/forming temps, pressure, gas flow)
- Conveyor (speed, load, vibration)
- Cutting station (cut count, blade temp, quality score)
- KPIs (line throughput, scrap rate proxy)


