import { Link } from 'react-router-dom';

/* ------------------------------------------------------------------ */
/*  Data: what's actually running in this demo                        */
/* ------------------------------------------------------------------ */

const sites = [
  { name: 'Tomago', state: 'NSW', capacity: '100 MW' },
  { name: 'Liddell', state: 'NSW', capacity: '150 MW' },
  { name: 'Broken Hill', state: 'NSW', capacity: '50 MW' },
  { name: 'Callide', state: 'QLD', capacity: '200 MW' },
  { name: 'Gladstone', state: 'QLD', capacity: '175 MW' },
];

const dataStreams = [
  {
    domain: 'BESS telemetry',
    tags: 'SoC%, SoH%, active power, rack temps, alarms',
    interval: '200ms',
  },
  {
    domain: 'Grid / POI',
    tags: 'Export/import power, voltage, frequency, dispatch targets',
    interval: '200ms',
  },
  {
    domain: 'NEM market',
    tags: 'Regional reference price (AUD/MWh), FCAS prices',
    interval: '2s',
  },
  {
    domain: 'CMMS',
    tags: 'Work orders, outage status, maintenance flags',
    interval: '10s',
  },
];

const pipelineSteps = [
  {
    layer: 'Bronze',
    table: 'raw_tags',
    description: 'Every tag-change event as-is. Protobuf decoded, microsecond timestamps, full fidelity.',
  },
  {
    layer: 'Silver',
    table: 'aggregated_tags',
    description: '1-minute tumbling windows with min/max/avg/stddev per tag. SDT compression ratio tracked.',
  },
  {
    layer: 'Silver',
    table: 'enriched_tags',
    description: 'Aggregated tags joined with signal mappings - asset_id, signal name, engineering units, source domain.',
  },
  {
    layer: 'Gold',
    table: 'health_scores',
    description: 'Z-score anomaly detection on the live stream. Per-asset health 0-1 when tags deviate from recent behaviour; primary risk tag and anomaly list.',
  },
  {
    layer: 'Gold',
    table: 'revenue_at_risk',
    description: 'Capacity x forecast price x trip probability for upcoming high-price NEM windows. Recommended actions from "Monitor" to "Critical shutdown".',
  },
];

const demoStops = [
  {
    to: '/dashboard',
    number: '01',
    title: 'Live ingest dashboard',
    talk: 'Show ~2,700 events/sec streaming from 5 sites into Delta tables. Point out the SDT compression ratio, latency numbers, and active asset count. All of this is flowing directly from Ignition via Zerobus gRPC - no Kafka, no batch ETL.',
    cta: 'Open dashboard',
    color: 'blue',
  },
  {
    to: '/analytics',
    number: '02',
    title: 'Fleet health & revenue risk',
    talk: 'The pipeline end result: which assets are at risk, and how much revenue we could lose if they trip during the next high-price NEM window. Health scores (z-score anomaly detection on the live stream) and revenue at risk (capacity × forecast price × trip probability) with actionable recommendations.',
    cta: 'See fleet health and revenue at risk',
    color: 'green',
  },
  {
    to: '/assets',
    number: '03',
    title: 'Fleet visibility',
    talk: 'Browse the full fleet - 20 BESS units across 5 NEM sites, plus grid interconnection and market data for each. Click into any asset to see tag-level trends: SoC%, active power, rack temperatures, dispatch targets.',
    cta: 'Browse assets',
    color: 'blue',
  },
  {
    to: '/compression',
    number: '04',
    title: 'Compression deep dive',
    talk: 'Walk through the compression waterfall: raw events, after SDT (Swinging Door Trending) at the connector, then Delta columnar on top. Show the tuning panel - adjust deviation thresholds for battery SoC vs temperature tags and see the impact on data volume.',
    cta: 'See compression',
    color: 'green',
  },
  {
    to: '/performance',
    number: '05',
    title: 'Performance and scaling',
    talk: 'The simulator is running 5 sites at 200ms intervals. Use the scaling calculator to show what happens at 20, 50, 100 sites. Zerobus scales horizontally with multi-stream — no single-server bottleneck. Each site onboards in hours, not weeks.',
    cta: 'Check performance',
    color: 'blue',
  },
  {
    to: '/architecture',
    number: '06',
    title: 'Architecture comparison',
    talk: 'The money slide. 8+ traditional components collapse into 5 Lakehouse components. Walk the comparison table: weeks to hours onboarding, proprietary to open Delta, proprietary SDK to SQL/Python/Spark/REST. Emphasise: same data that ingests is the data you query and train ML on.',
    cta: 'Compare architectures',
    color: 'green',
  },
];

const keyMessages = [
  {
    heading: 'No Kafka required',
    detail: 'Zerobus streams directly from Ignition to Delta tables using gRPC + protobuf. No message broker to manage, scale, or pay for.',
  },
  {
    heading: 'Hours to onboard, not weeks',
    detail: 'Install the module, configure the Databricks endpoint, and data flows. No interface nodes, no buffer servers, no archive tuning.',
  },
  {
    heading: 'Open format, not locked in',
    detail: 'Data lands in Delta Lake (Parquet). Query with SQL, Python, Spark, or REST. No proprietary SDK, no SQL DAS licence.',
  },
  {
    heading: 'Compression at every layer',
    detail: 'SDT at the connector reduces data 4-10x before it leaves site. Delta columnar adds another 3-5x. Tunable per-tag.',
  },
  {
    heading: 'ML on live OT data',
    detail: 'Anomaly detection on the same Delta tables that receive the live stream. No 6-month ETL project to get to analytics.',
  },
  {
    heading: 'Revenue risk in real time',
    detail: 'Health scores x NEM price forecasts x asset capacity = dollars at risk per window. Actionable recommendations from "Monitor" to "Critical".',
  },
];

/* ------------------------------------------------------------------ */
/*  Styling helpers                                                    */
/* ------------------------------------------------------------------ */

const colorMap: Record<string, { border: string; number: string; cta: string }> = {
  blue: {
    border: 'border-databricks-teal hover:border-databricks-primary',
    number: 'text-databricks-primary',
    cta: 'text-databricks-primary',
  },
  green: {
    border: 'border-green-900 hover:border-green-700',
    number: 'text-green-500',
    cta: 'text-green-400',
  },
};

const layerColor: Record<string, string> = {
  Bronze: 'text-amber-400',
  Silver: 'text-gray-300',
  Gold: 'text-yellow-400',
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function Landing() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <section className="mb-12">
        <div className="flex items-center gap-4 mb-4">
          <img src="/logos/AGL_Energy_logo.svg" alt="AGL Energy" className="h-10 w-auto object-contain" />
          <img src="/logos/databricks-full.svg" alt="Databricks" className="h-8 w-auto object-contain" />
        </div>
        <p className="text-sm font-semibold text-databricks-primary tracking-wider uppercase mb-2">
          Lakeflow Ignition Zerobus Connector
        </p>
        <h1 className="text-4xl font-bold text-gray-50 leading-tight mb-4">
          From SCADA to Lakehouse
          <br />
          <span className="text-databricks-primary">in one module</span>
        </h1>
        <p className="text-lg text-gray-400 leading-relaxed max-w-2xl">
          Stream OT tag data from Ignition directly into Databricks Delta tables.
          No Kafka. No batch ETL. No proprietary lock-in. Then run anomaly
          detection and revenue-at-risk analytics on the same live data. Built for{' '}
          <span className="text-agl-blue font-medium">AGL</span> fleet and NEM visibility.
        </p>
      </section>

      {/* What's running */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          What's running right now
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sites */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              5 NEM sites &middot; 675 MW total
            </h3>
            <div className="space-y-2">
              {sites.map((s) => (
                <div key={s.name} className="flex items-center justify-between text-sm">
                  <span className="text-gray-300">{s.name}</span>
                  <span className="text-gray-500">
                    {s.state} &middot; {s.capacity}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">
              4 BESS units per site &middot; 20 batteries + 15 grid/market/CMMS assets
            </p>
          </div>

          {/* Data streams */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              4 data domains &middot; ~2,700 events/sec
            </h3>
            <div className="space-y-2">
              {dataStreams.map((d) => (
                <div key={d.domain} className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 font-medium">{d.domain}</span>
                    <span className="text-xs text-gray-500">every {d.interval}</span>
                  </div>
                  <p className="text-xs text-gray-500">{d.tags}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* The problem */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          The problem
        </h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <p className="text-gray-300 leading-relaxed mb-4">
            Today, getting OT data from the plant floor to analytics often requires 8+
            components: interfaces, buffer subsystems, archive servers,
            asset framework, vision, SQL access, and a separate BI platform. Each one is a
            failure point, a licence cost, and weeks of configuration per site.
          </p>
          <p className="text-gray-300 leading-relaxed">
            Data ends up in a proprietary format that only proprietary SDKs can read. When
            the business asks "can we run ML on our battery telemetry?" the
            answer is "maybe, after a 6-month ETL project." Meanwhile, revenue
            is at risk during every NEM price spike.
          </p>
        </div>
      </section>

      {/* Pipeline */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Data pipeline (Lakeflow SDP)
        </h2>
        <div className="space-y-3">
          {pipelineSteps.map((step) => (
            <div
              key={step.table}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-start gap-4"
            >
              <span
                className={`text-xs font-bold uppercase tracking-wider mt-0.5 w-14 flex-shrink-0 ${layerColor[step.layer]}`}
              >
                {step.layer}
              </span>
              <div>
                <h3 className="text-sm font-semibold text-gray-200">
                  {step.table}
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Demo walkthrough */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Demo walkthrough
        </h2>
        <div className="space-y-4">
          {demoStops.map((stop) => {
            const c = colorMap[stop.color];
            return (
              <Link
                key={stop.number}
                to={stop.to}
                className={`block bg-gray-900 border ${c.border} rounded-lg p-5 transition-colors`}
              >
                <div className="flex items-start gap-4">
                  <span className={`text-2xl font-bold ${c.number} opacity-60 select-none`}>
                    {stop.number}
                  </span>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-100 mb-2">
                      {stop.title}
                    </h3>
                    <p className="text-sm text-gray-400 leading-relaxed mb-3">
                      {stop.talk}
                    </p>
                    <span className={`text-sm font-medium ${c.cta}`}>
                      {stop.cta} &rarr;
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Key messages */}
      <section className="mb-12">
        <h2 className="text-sm font-semibold text-gray-500 tracking-wider uppercase mb-4">
          Key messages
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {keyMessages.map((msg) => (
            <div
              key={msg.heading}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <h3 className="text-sm font-semibold text-brand-green mb-1">
                {msg.heading}
              </h3>
              <p className="text-sm text-gray-400 leading-relaxed">
                {msg.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Closing */}
      <section className="mb-8">
        <div className="bg-gray-900 border border-databricks-teal rounded-lg p-6 text-center">
          <h2 className="text-xl font-semibold text-gray-100 mb-2">
            Ready to walk through it?
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            Start with the live dashboard, then follow the stops above in order.
          </p>
          <Link
            to="/dashboard"
            className="inline-block px-6 py-2 bg-databricks-primary text-white text-sm font-semibold rounded hover:bg-databricks-primary/90 transition-colors"
          >
            Start the demo
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="pt-8 pb-4 border-t border-gray-800 flex items-center justify-center gap-2 text-sm text-gray-500">
        <img src="/logos/AGL_Energy_logo.svg" alt="" className="h-5 w-auto object-contain" aria-hidden />
        <span className="text-agl-blue font-medium">AGL OT Lakehouse</span>
        <span>·</span>
        <span>Powered by</span>
        <img src="/logos/databricks-full.svg" alt="" className="h-4 w-auto object-contain" aria-hidden />
        <span className="text-databricks-primary font-medium">Databricks</span>
      </footer>
    </div>
  );
}
