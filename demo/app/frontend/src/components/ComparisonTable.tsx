const rows = [
  {
    dimension: 'Components',
    other: 'Interfaces, buffers, servers, proprietary archive, vision, SQL access',
    lakehouse: 'Ignition, Zerobus Connector (serverless), Delta Tables',
  },
  {
    dimension: 'Resolution / granularity',
    other: '5-min typical; 1s = per-tag cost explosion at scale',
    lakehouse: 'Sub-second to 1s same cost (Delta + SDT, no per-tag tax)',
  },
  {
    dimension: 'Compression',
    other: 'SDT at archive',
    lakehouse: 'SDT at connector + Delta columnar',
  },
  {
    dimension: 'New site onboarding',
    other: 'Weeks',
    lakehouse: 'Hours',
  },
  {
    dimension: 'Scaling',
    other: 'Vertical',
    lakehouse: 'Horizontal',
  },
  {
    dimension: 'Data format',
    other: 'Proprietary',
    lakehouse: 'Open (Delta/Parquet)',
  },
  {
    dimension: 'Query access',
    other: 'Proprietary SDK only',
    lakehouse: 'SQL, Python, Spark, REST',
  },
  {
    dimension: 'OT + IT in one place',
    other: 'OT in historian; market/weather in separate systems',
    lakehouse: 'OT and market/forecast in same catalog; one query, one model',
  },
  {
    dimension: 'Licensing',
    other: 'Per-tag, per-server',
    lakehouse: 'Platform-level',
  },
];

export default function ComparisonTable() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">
        Operational overhead comparison
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-2 px-3 text-gray-400 font-medium">Dimension</th>
              <th className="text-left py-2 px-3 text-red-400 font-medium">Other platforms</th>
              <th className="text-left py-2 px-3 text-databricks-primary font-medium">Databricks + Zerobus</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.dimension} className="border-b border-gray-800">
                <td className="py-2 px-3 text-gray-300 font-medium">{r.dimension}</td>
                <td className="py-2 px-3 text-gray-400">{r.other}</td>
                <td className="py-2 px-3 text-gray-300">{r.lakehouse}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
