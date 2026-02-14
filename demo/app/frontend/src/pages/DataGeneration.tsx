/* ------------------------------------------------------------------ */
/*  Data Generation explainer — how the AGL Fleet Simulator works      */
/* ------------------------------------------------------------------ */

const sites = [
  { name: 'Tomago',     state: 'NSW', capacity: 100 },
  { name: 'Liddell',    state: 'NSW', capacity: 150 },
  { name: 'Broken Hill', state: 'NSW', capacity: 50 },
  { name: 'Callide',    state: 'QLD', capacity: 200 },
  { name: 'Gladstone',  state: 'QLD', capacity: 175 },
];

const generators = [
  {
    name: 'BESS Telemetry',
    provider: 'agl_bess',
    interval: '200 ms',
    color: 'text-blue-400',
    borderColor: 'border-blue-900',
    tagCount: '~25 tags per unit',
    signals: [
      { name: 'SoC%', model: 'Integrated from power draw: Δ = (-P / capacity) × (100/3600). Clamps 5-100%.' },
      { name: 'SoH%', model: 'Slow monotonic degradation — random(0, 0.0001) per tick. Never recovers.' },
      { name: 'Active power', model: 'Random walk ±0.5 MW/tick clamped to rated capacity, reduced by thermal derate factor.' },
      { name: 'DC voltage', model: '1100 + (SoC/100) × 300 + noise. Rises with charge, drops with discharge.' },
      { name: 'DC current', model: 'P × 1000 / V_dc. Derived from power and voltage.' },
      { name: 'Rack temperature', model: 'Thermal model: couples to ambient with |power|-driven heating + noise. Lag and drift.' },
      { name: 'Coolant temps', model: 'Follow ambient with lag. Inlet trails ambient; outlet trails inlet.' },
      { name: 'Thermal derate', model: 'Above 38°C: derate = max(0.4, 1.0 − (T − 38) × 0.06). Limits power output.' },
      { name: 'Alarms', model: '0.3% chance "Rack temp sensor noisy" per tick. Critical alarm if rack > 45°C.' },
    ],
    faultInjection: 'Every ~1500 ticks, rack temperature spikes to 42°C — triggering derate cascade, health score drop, and revenue-at-risk alerts. Configurable via --fault-every-ticks.',
  },
  {
    name: 'Grid / Dispatch',
    provider: 'agl_grid',
    interval: '200 ms',
    color: 'text-green-400',
    borderColor: 'border-green-900',
    tagCount: '~20 tags per site',
    signals: [
      { name: 'Dispatch target', model: 'Random walk ±35 MW/tick, clamped to ±450 MW. Represents AEMO dispatch instructions.' },
      { name: 'Network constraint', model: '1% chance to toggle on/off. When active: curtailment 5-40%, reason = NETWORK_LIMIT.' },
      { name: 'POI net power', model: 'target × (1 − curtailment/100) + noise. Splits into export/import based on sign.' },
      { name: 'Voltage / frequency', model: '330 kV ± 1.2 kV, 50 Hz ± 0.05 Hz. Gaussian noise around nominal.' },
      { name: 'Grid events', model: '0.2% chance each tick: under-frequency event or voltage sag event.' },
      { name: 'FCAS enablement', model: '0.5% chance to toggle contingency FCAS registration on/off.' },
    ],
  },
  {
    name: 'NEM Market',
    provider: 'agl_market',
    interval: '2 s',
    color: 'text-yellow-400',
    borderColor: 'border-yellow-900',
    tagCount: '~6 tags per site',
    signals: [
      { name: 'Regional Reference Price', model: 'Mean-reverting around $110/MWh: drift = (110 − price) × 0.05 + noise(-8, +8).' },
      { name: 'Price spike', model: '2% chance per tick: price += random(150, 400) AUD/MWh. Mimics NEM volatility.' },
      { name: 'FCAS prices', model: 'Random walk around $15-25/MWh for contingency/regulation raise/lower. Floor = $2.' },
    ],
  },
  {
    name: 'CMMS (Maintenance)',
    provider: 'agl_cmms',
    interval: '10 s',
    color: 'text-purple-400',
    borderColor: 'border-purple-900',
    tagCount: '~5 tags per site',
    signals: [
      { name: 'Open work orders', model: 'Random walk: +1, 0, 0, −1 (biased to stay flat). Clamp 0-20.' },
      { name: 'Planned outage', model: '1% toggle. When active, last WO = "PM-HVAC-Filter-Replace".' },
      { name: 'Forced outage', model: '0.5% toggle. When active, last WO = "CM-PCS-Inverter-Fault".' },
    ],
  },
];

const physicsDetails = [
  {
    title: 'Thermal model',
    detail: 'Each BESS unit maintains ambient, rack, and coolant temperatures as coupled state variables. Ambient drifts slowly (±0.2°C/tick). Rack temperature couples to ambient plus a power-proportional heating term. Coolant inlet/outlet trail with realistic lag. When rack temp exceeds 38°C, a derate factor kicks in that progressively limits power output — exactly like a real PCS thermal derating curve.',
  },
  {
    title: 'SoC integration',
    detail: 'State of Charge is computed via numeric integration of power draw against rated capacity. Charging adds energy; discharging removes it. The integration uses ΔSoC = (−P / capacity) × (100/3600) per tick, giving physically consistent charge/discharge curves with the correct time constants for a utility-scale BESS.',
  },
  {
    title: 'Market correlation',
    detail: 'NEM price follows a mean-reverting process around $110/MWh with occasional spikes (2% probability, +$150-400). This creates realistic windows where revenue-at-risk spikes — a battery trip during a price spike costs real money. The revenue-at-risk pipeline downstream multiplies health score × price forecast × capacity.',
  },
  {
    title: 'Fault injection',
    detail: 'Periodically (default every 1500 ticks ≈ 25 minutes at 1s intervals), the simulator injects a thermal anomaly: rack temperature jumps to 42°C. This triggers thermal derate, health score degradation, and revenue-at-risk alerts — creating a visible incident that flows through the entire pipeline from bronze to gold.',
  },
  {
    title: 'Grid dispatch realism',
    detail: 'Dispatch targets random-walk within AEMO-realistic bounds (±450 MW). Network constraints toggle stochastically (1%) and apply curtailment (5-40%) that decays when cleared. POI measurements add Gaussian noise to the constrained target, split into export/import components — matching real NEM metering patterns.',
  },
];

const configParams = [
  { flag: '--sites',     default: '3',    desc: 'Number of NEM sites (1-5 from the topology)' },
  { flag: '--units',     default: '2',    desc: 'BESS units per site (1-8)' },
  { flag: '--interval',  default: '1000', desc: 'Main tick interval in ms (BESS + Grid)' },
  { flag: '--ticks',     default: '0',    desc: 'Total ticks to generate (0 = run forever)' },
  { flag: '--fault-every-ticks', default: '1500', desc: 'Thermal anomaly injection interval (0 = off)' },
  { flag: '--dry-run',   default: 'off',  desc: 'Generate events without sending to gateway' },
];

export default function DataGeneration() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <section className="mb-10">
        <p className="text-sm font-semibold text-brand-green tracking-wider uppercase mb-2">
          Behind the demo
        </p>
        <h1 className="text-3xl font-bold text-gray-50 leading-tight mb-4">
          How we generate realistic fleet data
        </h1>
        <p className="text-lg text-gray-400 leading-relaxed max-w-2xl">
          The AGL Fleet Simulator produces physically-grounded synthetic data for
          5 NEM sites with battery storage, grid interconnection, market prices, and
          maintenance events. Every signal follows a model — no random noise generators.
        </p>
      </section>

      {/* Architecture overview */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Simulation architecture
        </h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <div className="font-mono text-sm text-gray-300 leading-relaxed whitespace-pre">
{`┌─────────────────────────────────────────────────────────┐
│                   AGL Fleet Simulator                    │
│  (Python · runs locally · hits Ignition HTTP ingest)     │
├──────────┬──────────┬──────────┬────────────────────────┤
│   BESS   │   Grid   │  Market  │         CMMS           │
│ Generator│ Generator│ Generator│       Generator         │
│  200ms   │  200ms   │   2s     │         10s             │
│ ~25 tags │ ~20 tags │  ~6 tags │        ~5 tags          │
│ per unit │ per site │ per site │       per site          │
├──────────┴──────────┴──────────┴────────────────────────┤
│  × 5 sites  × 4 BESS units each  = ~2,700 events/sec   │
├─────────────────────────────────────────────────────────┤
│              ↓ HTTP POST /system/zerobus/ingest/batch    │
│           Ignition Gateway (Zerobus module)              │
│              ↓ gRPC + protobuf                           │
│           Databricks Delta (raw_tags)                    │
└─────────────────────────────────────────────────────────┘`}
          </div>
        </div>
      </section>

      {/* Sites */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Simulated sites
        </h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="px-4 py-3 text-gray-400 font-medium">Site</th>
                <th className="px-4 py-3 text-gray-400 font-medium">State</th>
                <th className="px-4 py-3 text-gray-400 font-medium text-right">Capacity</th>
                <th className="px-4 py-3 text-gray-400 font-medium text-right">BESS units</th>
              </tr>
            </thead>
            <tbody>
              {sites.map((s) => (
                <tr key={s.name} className="border-b border-gray-800/50">
                  <td className="px-4 py-2 text-gray-200 font-medium">{s.name}</td>
                  <td className="px-4 py-2 text-gray-400">{s.state}</td>
                  <td className="px-4 py-2 text-gray-400 text-right">{s.capacity} MW</td>
                  <td className="px-4 py-2 text-gray-400 text-right">4</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="text-gray-500">
                <td className="px-4 py-2 font-medium" colSpan={2}>Total</td>
                <td className="px-4 py-2 text-right font-medium">675 MW</td>
                <td className="px-4 py-2 text-right font-medium">20 units</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Sites map to real AGL Energy locations in the Australian NEM (National Electricity Market).
          Tag paths follow Ignition conventions: <code className="text-gray-400">[agl_bess]AGL/Australia/NSW/Tomago/Site01/BESS01/Telemetry/SoC_pct</code>
        </p>
      </section>

      {/* Generators */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Four data generators
        </h2>
        <div className="space-y-6">
          {generators.map((gen) => (
            <div
              key={gen.provider}
              className={`bg-gray-900 border ${gen.borderColor} rounded-lg p-5`}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-lg font-semibold ${gen.color}`}>
                  {gen.name}
                </h3>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span className="bg-gray-800 px-2 py-1 rounded">{gen.provider}</span>
                  <span>every {gen.interval}</span>
                  <span>{gen.tagCount}</span>
                </div>
              </div>

              <div className="space-y-2">
                {gen.signals.map((sig) => (
                  <div key={sig.name} className="flex items-start gap-3 text-sm">
                    <span className="text-gray-300 font-medium w-44 flex-shrink-0">
                      {sig.name}
                    </span>
                    <span className="text-gray-500">{sig.model}</span>
                  </div>
                ))}
              </div>

              {gen.faultInjection && (
                <div className="mt-4 pt-3 border-t border-gray-800">
                  <div className="flex items-start gap-2 text-sm">
                    <span className="text-amber-400 font-medium flex-shrink-0">Fault injection</span>
                    <span className="text-gray-500">{gen.faultInjection}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Physics models */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          What makes it realistic
        </h2>
        <p className="text-gray-400 mb-4 text-sm leading-relaxed">
          Each generator maintains internal state and computes the next value from physical
          relationships — not random distributions. Temperatures couple thermally, SoC integrates
          power over time, market prices mean-revert with fat-tailed spikes, and grid dispatch
          follows NEM-realistic constraint patterns.
        </p>
        <div className="grid grid-cols-1 gap-4">
          {physicsDetails.map((p) => (
            <div
              key={p.title}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <h3 className="text-sm font-semibold text-brand-green mb-1">
                {p.title}
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                {p.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Configuration */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Simulator configuration
        </h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="px-4 py-3 text-gray-400 font-medium">Flag</th>
                <th className="px-4 py-3 text-gray-400 font-medium">Default</th>
                <th className="px-4 py-3 text-gray-400 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {configParams.map((p) => (
                <tr key={p.flag} className="border-b border-gray-800/50">
                  <td className="px-4 py-2 text-gray-200 font-mono text-xs">{p.flag}</td>
                  <td className="px-4 py-2 text-gray-400">{p.default}</td>
                  <td className="px-4 py-2 text-gray-500">{p.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-500 mb-2">Quick start:</p>
          <code className="text-sm text-gray-300 font-mono">
            make simulate-83
          </code>
          <p className="text-xs text-gray-500 mt-2">
            Override: <code className="text-gray-400">SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500 make simulate-83</code>
          </p>
        </div>
      </section>

      {/* How it flows */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          From simulator to dashboard
        </h2>
        <div className="space-y-3">
          {[
            { step: '1', label: 'Generators tick', detail: 'Each generator computes next state from physics models. One tick = one batch of TagEvents per generator.' },
            { step: '2', label: 'HTTP batch ingest', detail: 'Events POST to Ignition gateway at /system/zerobus/ingest/batch as JSON. Gateway maps to OTEvent protobuf.' },
            { step: '3', label: 'Zerobus gRPC stream', detail: 'Gateway streams protobuf to Databricks via Zerobus SDK. Events land in raw_tags Delta table within ~200ms.' },
            { step: '4', label: 'SDP pipeline', detail: 'Lakeflow streaming pipeline reads CDF from raw_tags → raw_throughput → aggregated_tags → enriched_tags. 1-minute windows.' },
            { step: '5', label: 'ML scoring', detail: 'Z-score anomaly detection on the live stream produces health_scores. Revenue-at-risk combines health × NEM price × capacity.' },
            { step: '6', label: 'This app', detail: 'Queries aggregated and enriched tables via SQL warehouse. Dashboard auto-refreshes to show live fleet state.' },
          ].map((s) => (
            <div
              key={s.step}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-start gap-4"
            >
              <span className="text-xl font-bold text-brand-blue opacity-50 select-none w-8 flex-shrink-0 text-center">
                {s.step}
              </span>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">{s.label}</h3>
                <p className="text-sm text-gray-400">{s.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
