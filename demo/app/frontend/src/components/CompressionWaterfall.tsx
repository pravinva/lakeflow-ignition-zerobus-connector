import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export interface CompressionLayer {
  layer_name: string;
  event_count: number;
  size_bytes: number;
  ratio_vs_raw: number;
}

interface CompressionWaterfallProps {
  layers: CompressionLayer[];
}

const LAYER_LABELS: Record<string, string> = {
  raw: 'Raw',
  after_sdt: 'After SDT',
  after_delta: 'Delta Lake (ZSTD)',
  combined: 'Combined',
};

const LAYER_COLORS = ['#6B7280', '#3B82F6', '#10B981', '#F59E0B'];

function formatBytes(bytes: number): string {
  const n = Number(bytes);
  if (n === 0 || !Number.isFinite(n)) return '0 B';
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)} GB`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)} MB`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(2)} KB`;
  return `${Math.round(n)} B`;
}

export default function CompressionWaterfall({ layers }: CompressionWaterfallProps) {
  const chartData = layers.map((l) => ({
    name: LAYER_LABELS[l.layer_name] ?? l.layer_name,
    size_bytes: l.size_bytes,
    event_count: l.event_count,
    ratio: l.ratio_vs_raw,
  }));

  const rawLayer = layers.find((l) => l.layer_name === 'raw');
  const deltaLayer = layers.find((l) => l.layer_name === 'after_delta') ?? layers.find((l) => l.layer_name === 'combined');

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Multi-layer compression breakdown
      </h3>

      {/* One-line summary: Incoming → On disk */}
      {rawLayer != null && deltaLayer != null && (
        <p className="text-xs text-gray-600 mb-3">
          Incoming: {rawLayer.event_count.toLocaleString()} rows, {formatBytes(rawLayer.size_bytes)} (est.) → On
          disk: {formatBytes(deltaLayer.size_bytes)} (ZSTD).
        </p>
      )}

      {/* Layer labels */}
      <div className="flex gap-4 mb-4 text-xs text-gray-600">
        {layers.map((l, i) => (
          <span key={l.layer_name} className="flex items-center gap-1">
            <span
              className="inline-block w-3 h-3 rounded"
              style={{ backgroundColor: LAYER_COLORS[i] }}
            />
            {LAYER_LABELS[l.layer_name] ?? l.layer_name}
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} />
          <YAxis stroke="#9CA3AF" fontSize={12} tickFormatter={(v: number) => formatBytes(v)} />
          <Tooltip
            contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb' }}
            labelStyle={{ color: '#374151' }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-gray-100 border border-gray-600 rounded px-3 py-2 text-sm">
                  <div className="font-medium text-gray-800">{d.name}</div>
                  <div className="text-gray-600">Rows: {d.event_count?.toLocaleString() ?? '—'}</div>
                  <div className="text-gray-600">Size: {formatBytes(d.size_bytes ?? 0)}</div>
                  {d.ratio != null && d.ratio !== 1 && (
                    <div className="text-gray-600">Ratio vs raw: {d.ratio.toFixed(2)}:1</div>
                  )}
                </div>
              );
            }}
          />
          <Bar dataKey="size_bytes" name="Size">
            {chartData.map((_entry, index) => (
              <Cell key={index} fill={LAYER_COLORS[index % LAYER_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Compression callout */}
      <div className="mt-4 p-3 bg-gray-100 border border-gray-200 rounded text-sm text-gray-700">
        Other platforms apply Swinging Door compression at the archive. We apply the{' '}
        <strong className="text-databricks-primary">same algorithm</strong> at the Zerobus connector
        - plus Delta columnar encoding on top. Same compression, open format, fewer moving
        parts.
      </div>
    </div>
  );
}
