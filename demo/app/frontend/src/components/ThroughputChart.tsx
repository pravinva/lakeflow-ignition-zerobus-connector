import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { ThroughputMetric } from '../services/api';
import { formatTimestamp } from '../utils/format';

/** Backend aggregates in 5-second windows; divide by this to get events/sec. */
const WINDOW_SECONDS = 5;

interface ChartDatum {
  time: string;
  raw: number;
  postSdt: number;
  rawPerSec: number;
  postSdtPerSec: number;
  sdtRatio: number | null;
}

interface ThroughputChartProps {
  data: ThroughputMetric[];
}

function formatSdtRatio(ratio: number | null | undefined): string {
  const r = ratio != null ? Number(ratio) : null;
  if (r == null || r < 1) return 'Off';
  return `${Number(r.toFixed(1))}:1`;
}

export default function ThroughputChart({ data }: ThroughputChartProps) {
  const chartData: ChartDatum[] = data.map((d) => {
    const raw = Number(d.records_raw) || 0;
    const postSdt = Number(d.records_after_sdt) || 0;
    return {
      time: formatTimestamp(d.window_start),
      raw,
      postSdt,
      rawPerSec: raw / WINDOW_SECONDS,
      postSdtPerSec: postSdt / WINDOW_SECONDS,
      sdtRatio:
        d.sdt_compression_ratio != null
          ? Number(d.sdt_compression_ratio)
          : null,
    };
  });

  const hasSdtCompression = chartData.some((d) => d.raw > d.postSdt);

  const gridStroke = '#e5e7eb';
  const axisStroke = '#9ca3af';
  const tooltipBg = '#ffffff';
  const tooltipBorder = '#e5e7eb';
  const primaryColor = '#FF3621';
  const secondaryColor = '#10B981';

  return (
    <div className="bg-surface-card border border-gray-200 rounded-card p-4 shadow-card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-heading font-semibold text-gray-700">
          Throughput (events/sec)
        </h3>
        <span className="text-xs text-gray-500">
          {hasSdtCompression
            ? 'Raw estimated from compression ratio (suppressed events not stored)'
            : 'Two lines when SDT compresses (ratio > 1)'}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
          <XAxis dataKey="time" stroke={axisStroke} fontSize={12} />
          <YAxis stroke={axisStroke} fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: tooltipBg,
              border: `1px solid ${tooltipBorder}`,
              borderRadius: '0.5rem',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)',
            }}
            labelStyle={{ color: '#374151' }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length || !label) return null;
              const d = payload[0].payload as ChartDatum;
              return (
                <div className="rounded px-3 py-2 min-w-[160px]">
                  <div className="text-gray-700 font-medium border-b border-gray-200 pb-1 mb-2">
                    {label}
                  </div>
                  <div className="text-gray-600 text-sm space-y-0.5">
                    {hasSdtCompression ? (
                      <>
                        <div>
                          Raw: <span className="text-gray-900 font-semibold">{d.raw.toLocaleString()}</span> ({d.rawPerSec.toLocaleString(undefined, { maximumFractionDigits: 0 })}/sec)
                        </div>
                        <div>
                          Post-SDT: <span className="text-gray-900 font-semibold">{d.postSdt.toLocaleString()}</span> ({d.postSdtPerSec.toLocaleString(undefined, { maximumFractionDigits: 0 })}/sec)
                        </div>
                      </>
                    ) : (
                      <div>
                        Events: <span className="text-gray-900 font-semibold">{d.postSdt.toLocaleString()}</span> ({d.postSdtPerSec.toLocaleString(undefined, { maximumFractionDigits: 0 })}/sec)
                      </div>
                    )}
                    <div className="pt-1 border-t border-gray-200 mt-1">
                      SDT:{' '}
                      <span className="text-gray-900 font-medium">
                        {formatSdtRatio(d.sdtRatio)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            }}
          />
          <Legend />
          {hasSdtCompression ? (
            <>
              <Area
                type="monotone"
                dataKey="rawPerSec"
                name="Raw events/sec"
                stroke={primaryColor}
                fill={primaryColor}
                fillOpacity={0.15}
              />
              <Area
                type="monotone"
                dataKey="postSdtPerSec"
                name="Post-SDT events/sec"
                stroke={secondaryColor}
                fill={secondaryColor}
                fillOpacity={0.3}
              />
            </>
          ) : (
            <Area
              type="monotone"
              dataKey="postSdtPerSec"
              name="Events/sec"
              stroke={secondaryColor}
              fill={secondaryColor}
              fillOpacity={0.3}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
