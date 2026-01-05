-- Seed asset registry + signal mapping for the Site01 Ignition demo
-- NOTE: You can extend this list as you ingest more tags.

-- Asset registry
MERGE INTO ignition_demo.tilt_ot.silver_asset_registry t
USING (
  SELECT * FROM VALUES
    ('site01', NULL, 'site', 'Site01', 'Tilt Site01 (Demo)', true),
    ('metmast01', 'site01', 'met_mast', 'Site01', 'Met Mast 01', true),
    ('windfarm01', 'site01', 'wind_farm', 'Site01', 'Windfarm 01', true),
    ('t01', 'windfarm01', 'wind_turbine', 'Site01', 'Turbine T01', true),
    ('t02', 'windfarm01', 'wind_turbine', 'Site01', 'Turbine T02', true),
    ('t03', 'windfarm01', 'wind_turbine', 'Site01', 'Turbine T03', true),
    ('solarfarm01', 'site01', 'solar_farm', 'Site01', 'Solar Farm 01', true),
    ('inv01', 'solarfarm01', 'inverter', 'Site01', 'Inverter I01', true),
    ('inv02', 'solarfarm01', 'inverter', 'Site01', 'Inverter I02', true),
    ('bess01', 'site01', 'bess', 'Site01', 'BESS 01', true),
    ('substation01', 'site01', 'substation', 'Site01', 'Substation 01', true),
    ('poi', 'substation01', 'poi', 'Site01', 'Point of Interconnect (POI)', true)
) s(asset_id, parent_asset_id, asset_type, site, display_name, active)
ON t.asset_id = s.asset_id
WHEN MATCHED THEN UPDATE SET
  t.parent_asset_id = s.parent_asset_id,
  t.asset_type = s.asset_type,
  t.site = s.site,
  t.display_name = s.display_name,
  t.active = s.active
WHEN NOT MATCHED THEN INSERT *;

-- Signal mapping: tag_path -> business signals
-- Plant telemetry ([tilt])
MERGE INTO ignition_demo.tilt_ot.silver_signal_mapping t
USING (
  SELECT * FROM VALUES
    -- met mast
    ('[tilt]Tilt/Site01/MetMast01/WindSpeed_mps', 'metmast01', 'wind_speed', 'm/s', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/MetMast01/WindDir_deg', 'metmast01', 'wind_direction', 'deg', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/MetMast01/Irradiance_Wm2', 'metmast01', 'irradiance', 'W/m2', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/MetMast01/AmbientTemp_C', 'metmast01', 'ambient_temp', 'C', 1.0, 0.0, 'plant', true),

    -- wind farm totals
    ('[tilt]Tilt/Site01/Windfarm01/Site/Power_Total_kW', 'windfarm01', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/Windfarm01/Site/Availability_pct', 'windfarm01', 'availability', '%', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/Windfarm01/Site/Curtailment_pct', 'windfarm01', 'curtailment', '%', 1.0, 0.0, 'plant', true),

    -- turbine power
    ('[tilt]Tilt/Site01/Windfarm01/Turbines/T01/Electrical/Power_kW', 't01', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/Windfarm01/Turbines/T02/Electrical/Power_kW', 't02', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/Windfarm01/Turbines/T03/Electrical/Power_kW', 't03', 'power', 'kW', 1.0, 0.0, 'plant', true),

    -- solar totals + inverter power
    ('[tilt]Tilt/Site01/SolarFarm01/Plant/Power_Total_kW', 'solarfarm01', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/SolarFarm01/Plant/Availability_pct', 'solarfarm01', 'availability', '%', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/SolarFarm01/Inverters/I01/AC/Power_kW', 'inv01', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/SolarFarm01/Inverters/I02/AC/Power_kW', 'inv02', 'power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/SolarFarm01/Inverters/I01/Availability', 'inv01', 'available', 'bool', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/SolarFarm01/Inverters/I02/Availability', 'inv02', 'available', 'bool', 1.0, 0.0, 'plant', true),

    -- bess
    ('[tilt]Tilt/Site01/BESS01/Power/NetPower_kW', 'bess01', 'net_power', 'kW', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/BESS01/SoC/StateOfCharge_pct', 'bess01', 'soc', '%', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/BESS01/Energy/Throughput_MWh', 'bess01', 'throughput', 'MWh', 1.0, 0.0, 'plant', true),
    ('[tilt]Tilt/Site01/BESS01/Energy/Cycles', 'bess01', 'cycles', 'count', 1.0, 0.0, 'plant', true),

    -- Grid ([grid]): dispatch + POI
    ('[grid]Tilt/Site01/Dispatch/TargetExport_kW', 'poi', 'dispatch_target', 'kW', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Dispatch/Curtailment_pct', 'poi', 'curtailment', '%', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Dispatch/ConstraintActive', 'poi', 'constraint_active', 'bool', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Market/RRP_AUD_per_MWh', 'poi', 'rrp', 'AUD/MWh', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Substation01/POI/ExportPower_kW', 'poi', 'export_power', 'kW', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Substation01/POI/ImportPower_kW', 'poi', 'import_power', 'kW', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Substation01/POI/NetPower_kW', 'poi', 'net_power', 'kW', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Substation01/POI/Frequency_Hz', 'poi', 'frequency', 'Hz', 1.0, 0.0, 'grid', true),
    ('[grid]Tilt/Site01/Substation01/POI/Voltage_kV', 'poi', 'voltage', 'kV', 1.0, 0.0, 'grid', true),

    -- CMMS ([cmms])
    ('[cmms]Tilt/Site01/WorkOrders/ActiveCount', 'site01', 'active_work_orders', 'count', 1.0, 0.0, 'cmms', true),
    ('[cmms]Tilt/Site01/WorkOrders/HighPriorityCount', 'site01', 'high_priority_work_orders', 'count', 1.0, 0.0, 'cmms', true),
    ('[cmms]Tilt/Site01/Assets/Windfarm01/T01/ForcedOutage', 't01', 'forced_outage', 'bool', 1.0, 0.0, 'cmms', true),
    ('[cmms]Tilt/Site01/Assets/Windfarm01/T02/ForcedOutage', 't02', 'forced_outage', 'bool', 1.0, 0.0, 'cmms', true),
    ('[cmms]Tilt/Site01/Assets/Windfarm01/T03/ForcedOutage', 't03', 'forced_outage', 'bool', 1.0, 0.0, 'cmms', true),
    ('[cmms]Tilt/Site01/Assets/BESS01/ForcedOutage', 'bess01', 'forced_outage', 'bool', 1.0, 0.0, 'cmms', true),

    -- Forecast ([forecast])
    ('[forecast]Tilt/Site01/Forecast/H01/NetPower_kW', 'site01', 'net_power_forecast_h01', 'kW', 1.0, 0.0, 'forecast', true),
    ('[forecast]Tilt/Site01/Forecast/H01/Confidence_pct', 'site01', 'forecast_confidence_h01', '%', 1.0, 0.0, 'forecast', true),
    ('[forecast]Tilt/Site01/Forecast/H01/ExpectedCurtailment_pct', 'site01', 'expected_curtailment_h01', '%', 1.0, 0.0, 'forecast', true)
) s(tag_path, asset_id, signal_name, unit, scale, offset, source_domain, active)
ON t.tag_path = s.tag_path
WHEN MATCHED THEN UPDATE SET
  t.asset_id = s.asset_id,
  t.signal_name = s.signal_name,
  t.unit = s.unit,
  t.scale = s.scale,
  t.offset = s.offset,
  t.source_domain = s.source_domain,
  t.active = s.active
WHEN NOT MATCHED THEN INSERT *;


