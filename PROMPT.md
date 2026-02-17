# Task: AGL fleet Ignition tag config generator

## Objective

Create a Python package that generates Ignition Gateway tag configs (JSON) and timer scripts (Python) for the AGL renewable energy fleet. The generated configs must produce tag data that matches what the phase-7 SDP analytics pipeline expects in `agl_demo.ot.raw_tags`.

This is a **data simulation layer** - it produces the OT tag events that flow through Zerobus to Delta tables, which the analytics pipeline then processes.

## Context

Read these files to understand the current state:
- `prompts/phase-7-sdp-analytics-pipeline.md` - The analytics pipeline that consumes this data (key tags, schemas)
- `APP-PRD.md` - The app that displays analytics (asset fleet definition, FR-103)
- `pipelines/sql/setup_tables.sql` - Target schema for `raw_tags` table
- `examples/agl_tomago_bess_site01/` - Existing AGL battery example (pattern reference)
- `examples/tilt_renewables_site01/` - Existing wind turbine example (pattern reference)
- `CLAUDE.md` - Project conventions
- `progress.txt` - Learnings from previous iterations

Also read `progress.txt` if it exists - it contains learnings from previous iterations.

Check recent changes:
```bash
git log --oneline -10
ls examples/
```

## Technical constraints

- **Python 3.11+**: Use modern Python features (dataclasses, type hints, pathlib)
- **Output format**: Ignition-compatible JSON for tag import, and Python timer scripts for Gateway Script Console
- **Tag names must match phase-7 expectations**:
  - Wind: `nacelle/temperature_c`, `generator/power_kw`, `grid/frequency_hz`, `rotor/wind_speed_ms`
  - Battery: `battery/temperature_c`, `battery/soc_pct`, `thermal/coolant_temp_c`, `inverter/efficiency_pct`
- **Asset ID format**: `{type}_{site}_{number}` e.g., `wind_hexham_t01`, `bess_tomago_01`
- **Asset types**: `wind_turbine` for wind, `battery_bess` for batteries
- **Fleet from APP-PRD FR-103**:
  - Hexham: 50 wind turbines, 12 MW each
  - Pottinger: 40 wind turbines, 12 MW each
  - Liddell Battery: 20 BESS units, 25 MW each
  - Tomago Battery: 15 BESS units, 33 MW each
  - Broken Hill Battery: 10 BESS units, 5 MW each
- **Realistic patterns**: Temperature follows sinusoidal daily pattern, power follows random walk with bounds, SoC cycles
- **Degradation injection**: Support for injecting anomalies (temperature drift, efficiency drop) for demo scenarios
- **No PySpark**: Generator is pure Python, no Spark dependencies
- **ruff for lint/format**: Line length 120, Python 3.11+ target

## Requirements

### FR-300: Python package scaffold
Create a Python package at `examples/agl_fleet/` with:
```
examples/agl_fleet/
  pyproject.toml          # Package config with [dev] extras (ruff, pytest)
  src/
    agl_fleet_gen/
      __init__.py
      models.py           # Asset, Tag, TagProfile dataclasses
      profiles.py         # Tag profile configs (wind, battery)
      generators.py       # Tag JSON + timer script generators
      cli.py              # CLI entry point
  tests/
    __init__.py
    conftest.py           # Shared fixtures
    test_models.py
    test_profiles.py
    test_generators.py
  output/                 # Generated files (gitignored)
```

- `pyproject.toml` includes: ruff, pytest as dev deps
- `ruff` config: line-length 120, target Python 3.11+

### FR-301: Asset and tag models (`models.py`)
Define dataclasses for the data model:

- `TagProfile` - configuration for a tag type:
  - `name: str` - tag name (e.g., `nacelle/temperature_c`)
  - `unit: str` - engineering unit
  - `min: float`, `max: float` - value bounds
  - `typical: float` - nominal value
  - `pattern: str` - `sinusoidal` | `random_walk` | `step` | `constant`
  - `noise_factor: float` - noise amplitude (0.0 - 1.0)
  - `sdt_comp_dev: float | None` - SDT compression deviation

- `Asset` - an individual asset:
  - `asset_id: str` - unique ID (e.g., `wind_hexham_t01`)
  - `asset_type: str` - `wind_turbine` | `battery_bess`
  - `site_name: str` - e.g., `Hexham`
  - `capacity_mw: float` - rated capacity
  - `tags: list[TagProfile]` - tag configurations for this asset

- `Fleet` - collection of assets:
  - `name: str` - fleet name (e.g., `AGL Energy`)
  - `assets: list[Asset]`

### FR-302: Tag profiles (`profiles.py`)
Define standard tag profiles that match phase-7 analytics expectations:

**Wind turbine profiles** (4 key tags + supporting):
- `nacelle/temperature_c`: sinusoidal, min=20, max=85, typical=65, noise=0.02
- `generator/power_kw`: random_walk, min=0, max=12000 (scaled by capacity), typical=6000
- `grid/frequency_hz`: sinusoidal, min=49.85, max=50.15, typical=50.0, noise=0.001
- `rotor/wind_speed_ms`: random_walk, min=0, max=30, typical=9

**Battery BESS profiles** (4 key tags + supporting):
- `battery/temperature_c`: sinusoidal, min=15, max=45, typical=28, noise=0.03
- `battery/soc_pct`: random_walk, min=10, max=95, typical=50
- `thermal/coolant_temp_c`: sinusoidal, min=18, max=35, typical=24, noise=0.02
- `inverter/efficiency_pct`: constant, min=90, max=99, typical=96, noise=0.005

Functions:
- `get_wind_profiles(capacity_mw: float) -> list[TagProfile]`
- `get_battery_profiles(capacity_mw: float) -> list[TagProfile]`
- `create_fleet() -> Fleet` - Creates the full AGL fleet per APP-PRD FR-103

### FR-303: Ignition JSON generator (`generators.py`)
Generate Ignition-compatible tag JSON configs:

- `generate_tag_json(asset: Asset) -> dict` - Single asset's tag structure
- `generate_fleet_json(fleet: Fleet, provider_name: str = "ot") -> dict` - Full fleet as Ignition folder hierarchy
- `generate_timer_script(asset: Asset) -> str` - Python timer script for Ignition Gateway

The JSON format must match Ignition's tag import schema (see existing examples):
```json
{
  "name": "FolderName",
  "tagType": "Folder",
  "tags": [
    { "name": "TagName", "tagType": "AtomicTag", "valueSource": "memory", "dataType": "Float4", "value": 0.0 }
  ]
}
```

Timer scripts must:
- Be valid Ignition Jython (Python 2.7-compatible syntax)
- Use `system.tag.readBlocking()` and `system.tag.writeBlocking()`
- Implement the pattern logic from TagProfile
- Support configurable update intervals

### FR-304: CLI entry point (`cli.py`)
Create a CLI for generating configs:

```bash
# Generate full fleet
python -m agl_fleet_gen generate --output output/

# Generate subset
python -m agl_fleet_gen generate --sites hexham,tomago --count 5 --output output/

# List available sites
python -m agl_fleet_gen list-sites
```

Arguments:
- `--output`: Output directory (default: `output/`)
- `--sites`: Comma-separated site names to include (default: all)
- `--count`: Max assets per site (default: all)
- `--provider`: Ignition tag provider name (default: `ot`)

### FR-305: Degradation scenario support
Support injecting degradation scenarios for demo:

- `inject_degradation(asset: Asset, scenario: str) -> Asset` - Returns modified asset with degraded profiles

Scenarios:
- `gearbox_overheat`: `nacelle/temperature_c` typical +20, max +30
- `thermal_runaway`: `battery/temperature_c` typical +15, `thermal/coolant_temp_c` typical -5 (divergence)
- `inverter_degradation`: `inverter/efficiency_pct` typical -10, max -15

## Test plan (write these FIRST)

Follow TDD - write failing tests before writing implementation code.

### Tests to create

**`tests/test_models.py`** (5 tests):
- [ ] `test_tag_profile_dataclass_fields` - TagProfile has all required fields
- [ ] `test_asset_dataclass_fields` - Asset has all required fields
- [ ] `test_fleet_dataclass_fields` - Fleet has all required fields
- [ ] `test_asset_id_format` - Asset ID follows `{type}_{site}_{number}` pattern
- [ ] `test_asset_type_values` - Asset type is `wind_turbine` or `battery_bess`

**`tests/test_profiles.py`** (8 tests):
- [ ] `test_wind_profiles_has_key_tags` - Wind profiles include all 4 phase-7 key tags
- [ ] `test_battery_profiles_has_key_tags` - Battery profiles include all 4 phase-7 key tags
- [ ] `test_wind_profiles_tag_names_match` - Tag names exactly match phase-7 expectations
- [ ] `test_battery_profiles_tag_names_match` - Tag names exactly match phase-7 expectations
- [ ] `test_create_fleet_asset_counts` - Fleet has correct asset counts per site
- [ ] `test_create_fleet_capacities` - Fleet assets have correct MW capacities
- [ ] `test_create_fleet_total_assets` - Total is 50+40+20+15+10 = 135 assets
- [ ] `test_wind_profiles_power_scaled_by_capacity` - Generator power max scales with capacity_mw

**`tests/test_generators.py`** (10 tests):
- [ ] `test_tag_json_valid_structure` - Generated JSON has valid Ignition tag import structure
- [ ] `test_tag_json_has_atomic_tags` - JSON includes AtomicTag entries for all profiles
- [ ] `test_tag_json_folder_hierarchy` - JSON has proper folder nesting
- [ ] `test_fleet_json_all_assets_included` - Fleet JSON includes all assets
- [ ] `test_timer_script_valid_python` - Generated timer script compiles as Python
- [ ] `test_timer_script_has_read_write` - Script includes system.tag.readBlocking/writeBlocking
- [ ] `test_timer_script_pattern_logic` - Script implements pattern (sinusoidal, random_walk, etc.)
- [ ] `test_degradation_gearbox_overheat` - Gearbox scenario modifies nacelle temp profile
- [ ] `test_degradation_thermal_runaway` - Thermal scenario creates temp divergence
- [ ] `test_degradation_inverter_drop` - Inverter scenario reduces efficiency

## Gates

Run `bash gates.sh` to verify all completion criteria at once. This script creates a venv and runs:

| Gate | Command |
|------|---------|
| Install | `pip install -e "examples/agl_fleet[dev]"` |
| Lint | `ruff check examples/agl_fleet/src/ examples/agl_fleet/tests/` |
| Format | `ruff format --check examples/agl_fleet/src/ examples/agl_fleet/tests/` |
| Tests | `pytest examples/agl_fleet/tests/ -v --tb=short` |

Output looks like:
```
  Install              ok
  Lint                 ok
  Format               ok
  Tests                ok

All 4 gate(s) passed
```

## Completion criteria

The task is COMPLETE only when:
- [ ] `bash gates.sh` exits with code 0
- [ ] All 23 tests from the test plan above are written and passing
- [ ] `examples/agl_fleet/pyproject.toml` exists with ruff + pytest dev deps
- [ ] Generator produces valid Ignition JSON that can be imported
- [ ] Generated timer scripts are valid Python
- [ ] Tag names match phase-7 analytics expectations exactly
- [ ] Fleet includes all 135 assets per APP-PRD FR-103

Do NOT assess completion subjectively. Run `bash gates.sh` and check the exit code.

## Workflow

You MUST follow this exact workflow. Do NOT use EnterPlanMode or AskUserQuestion - this runs unattended.

### Step 1: Assess
Read the context files listed above, check git history, and read `progress.txt` if it exists. Determine what has already been done in previous iterations.

### Step 2: Plan
Write out a FULL numbered implementation plan for the entire task. Number every step. Then identify which SINGLE step to tackle THIS iteration. You MUST only pick ONE step per iteration.

### Step 3: Execute ONE step
Execute ONLY the single step you identified, following TDD (red-green-refactor):

1. **Red**: Write failing tests for this ONE step
2. Run `bash gates.sh` - the test gate should fail (expected)
3. **Green**: Write the minimum code to make those tests pass
4. Run `bash gates.sh` - all gates should pass now
5. **Refactor**: Clean up while keeping gates green
6. Commit working changes with clear messages
7. Append to `progress.txt` what you learned this iteration

## Critical: scope control
- You MUST do only ONE meaningful unit of work per iteration.
- Do NOT chain multiple steps together. Stop after completing one step.
- The loop will bring you back to assess and pick the next step.

## Important rules
- This runs UNATTENDED. Never use EnterPlanMode or AskUserQuestion.
- Do NOT declare yourself done or try to exit. The loop continues automatically.
- Each iteration: assess, plan full scope, execute ONE step, commit.
- If the task appears complete, look for improvements, edge cases, tests, or documentation to add - one at a time.
- If genuinely stuck, append your blockers to `progress.txt` for the next iteration.
- Reference existing examples (`examples/agl_tomago_bess_site01/`, `examples/tilt_renewables_site01/`) for Ignition JSON format and timer script patterns.
- Timer scripts must be Ignition Jython compatible (Python 2.7 syntax) - no f-strings, no type hints in the scripts themselves.
