### Tilt Renewables “Site01” simulation (Ignition) — end-to-end OT demo

This example is a richer, **multi-asset** Tilt Renewables demo (not just wind). It is designed to showcase:

- **Ingest** (Ignition → Databricks Zerobus → Bronze table)
- **Silver** (normalized, typed time series + dimensions)
- **Gold** (KPIs and operations analytics)
- **Dashboards** (AI/BI dashboards in Databricks)
- **Genie** (natural-language questions against Gold/Silver)

This demo uses **Memory tags** + **Gateway Timer Scripts** (Jython) so it works without external hardware.

## What’s included

This demo uses **four “sources”** (four tag providers) to make the business story realistic:

- **Plant telemetry SCADA**: `[tilt_sim]...` (Wind + Solar + BESS + Met)
- **Grid + market**: `[grid_sim]...` (POI meter, dispatch target, curtailment, price)
- **Maintenance / CMMS**: `[cmms_sim]...` (forced outage flags, work orders, reasons)
- **Forecast**: `[forecast_sim]...` (next-hour forecasts for wind/solar/net)

Included files:

- **`tilt_sim_site01_tags.json`**: Import into provider **`tilt_sim`**.
- **`grid_sim_site01_tags.json`**: Import into provider **`grid_sim`**.
- **`cmms_sim_site01_tags.json`**: Import into provider **`cmms_sim`**.
- **`forecast_sim_site01_tags.json`**: Import into provider **`forecast_sim`**.

Gateway Timer Scripts (create 4 timers at 1s or 2s):

- **`timer_script_site01_plant_telemetry.py`**
- **`timer_script_site01_grid_market.py`**
- **`timer_script_site01_maintenance_events.py`**
- **`timer_script_site01_weather_forecast.py`**

## 1) Create the tag providers

In the Gateway UI:

- Go to **Configure → Tags → Realtime Tag Providers**
- Create **four** **Standard Tag Providers**:
  - `tilt_sim`
  - `grid_sim`
  - `cmms_sim`
  - `forecast_sim`
- Ensure each is **Enabled** and **NOT Read Only**

> The provider names matter because each JSON export assumes you import into the matching provider.

## 2) Import the tags

In the Designer:

- Open **Tag Browser**
- For each provider, select it and import its JSON:
  - Provider `tilt_sim` → import `tilt_sim_site01_tags.json`
  - Provider `grid_sim` → import `grid_sim_site01_tags.json`
  - Provider `cmms_sim` → import `cmms_sim_site01_tags.json`
  - Provider `forecast_sim` → import `forecast_sim_site01_tags.json`

You should see (examples):

- `[tilt_sim]Tilt/Site01/MetMast01/...`
- `[tilt_sim]Tilt/Site01/Windfarm01/...`
- `[tilt_sim]Tilt/Site01/SolarFarm01/...`
- `[tilt_sim]Tilt/Site01/BESS01/...`
- `[grid_sim]Tilt/Site01/Substation01/...`
- `[cmms_sim]Tilt/Site01/...`
- `[forecast_sim]Tilt/Site01/...`

## 3) Add the Gateway Timer Scripts (simulators)

Designer → **Scripting → Gateway Events → Timer**

- Delay Type: **Fixed Delay**
- Delay (ms): **1000**
- Enabled: **true**
- Create 4 timers and paste one script into each:
  - `timer_script_site01_plant_telemetry.py`
  - `timer_script_site01_grid_market.py`
  - `timer_script_site01_maintenance_events.py`
  - `timer_script_site01_weather_forecast.py`

## 4) Ingest (Zerobus module)

The module’s **direct subscriptions** currently support `tagSelectionMode = explicit` only.

Start with a small, high-signal list:

- `[tilt_sim]Tilt/Site01/MetMast01/WindSpeed_mps`
- `[tilt_sim]Tilt/Site01/MetMast01/Irradiance_Wm2`
- `[tilt_sim]Tilt/Site01/Windfarm01/Turbines/T01/Electrical/Power_kW`
- `[tilt_sim]Tilt/Site01/SolarFarm01/Inverters/I01/AC/Power_kW`
- `[tilt_sim]Tilt/Site01/BESS01/Power/NetPower_kW`
- `[grid_sim]Tilt/Site01/Substation01/POI/ExportPower_kW`
- `[grid_sim]Tilt/Site01/Substation01/POI/Frequency_Hz`
- `[grid_sim]Tilt/Site01/Dispatch/Curtailment_pct`
- `[cmms_sim]Tilt/Site01/WorkOrders/ActiveCount`
- `[forecast_sim]Tilt/Site01/Forecast/H01/NetPower_kW`

Then validate:

- `GET /system/zerobus/health`
- `GET /system/zerobus/diagnostics`

## 5) Databricks end-to-end (Bronze → Silver → Gold → Dashboards → Genie)

See:

- `tools/databricks_end2end_tilt/README.md`


