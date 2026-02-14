import { useCallback } from 'react';
import { usePolling } from '../hooks/usePolling';
import { api } from '../services/api';
import BigNumberCard from '../components/BigNumberCard';
import ScalingCalculator from '../components/ScalingCalculator';
import TunablesTable from '../components/TunablesTable';
import { formatNumber, latencyColor } from '../utils/format';

export default function Performance() {
  const throughputFetcher = useCallback(
    () => api.getThroughput().then((r) => r.data),
    [],
  );
  const latencyFetcher = useCallback(
    () => api.getLatency().then((r) => r.data),
    [],
  );

  const throughput = usePolling({
    fetcher: throughputFetcher,
    intervalMs: 5000,
  });
  const latency = usePolling({
    fetcher: latencyFetcher,
    intervalMs: 5000,
  });

  const latest = throughput.data?.at(-1);
  const latestLatency = latency.data?.at(-1);

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Performance</h2>

      {/* Section 1 - Platform specs */}
      <h3 className="text-lg font-medium text-gray-300 mb-3">
        Zerobus platform specifications
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <BigNumberCard
          label="Throughput per stream"
          value="15,000 rows/sec"
        />
        <BigNumberCard
          label="Bandwidth per stream"
          value="100 MB/sec"
        />
        <BigNumberCard
          label="Latency target"
          value={'\u22645s median e2e'}
        />
        <BigNumberCard
          label="SDT compression"
          value="4:1 to 10:1"
        />
        <BigNumberCard
          label="Scaling"
          value="Horizontal"
          subtitle="Multi-stream"
        />
      </div>

      {/* Section 2 - Live demo performance */}
      <h3 className="text-lg font-medium text-gray-300 mb-3">
        Live demo performance
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <BigNumberCard
          label="Throughput"
          value={
            latest
              ? `${formatNumber(latest.records_raw, 0)}/sec`
              : '-'
          }
          subtitle="Spec: 15,000/sec"
          colorClass={latest ? 'text-brand-green' : 'text-brand-blue'}
        />
        <BigNumberCard
          label="Compression"
          value={
            latest
              ? (Number(latest.sdt_compression_ratio) <= 1 ||
                 latest.sdt_compression_ratio == null
                  ? 'Off'
                  : `${formatNumber(Number(latest.sdt_compression_ratio), 1)}:1`)
              : '-'
          }
          subtitle="Target: 4-10:1 (Off when SDT disabled)"
          colorClass={
            latest &&
            latest.sdt_compression_ratio != null &&
            Number(latest.sdt_compression_ratio) > 1 &&
            Number(latest.sdt_compression_ratio) >= 4 &&
            Number(latest.sdt_compression_ratio) <= 10
              ? 'text-brand-green'
              : 'text-brand-blue'
          }
        />
        <BigNumberCard
          label="Avg latency"
          value={
            latestLatency
              ? `${formatNumber(latestLatency.avg_latency_ms, 0)}ms`
              : '-'
          }
          subtitle={'\u2264 5,000ms target'}
          colorClass={
            latestLatency
              ? latencyColor(latestLatency.avg_latency_ms)
              : 'text-brand-blue'
          }
        />
        <BigNumberCard
          label="P99 latency"
          value={
            latestLatency
              ? `${formatNumber(latestLatency.p99_latency_ms, 0)}ms`
              : '-'
          }
          colorClass={
            latestLatency
              ? latencyColor(latestLatency.p99_latency_ms)
              : 'text-brand-blue'
          }
        />
      </div>

      {/* Section 3 - Scaling calculator */}
      <h3 className="text-lg font-medium text-gray-300 mb-3">
        Scaling calculator
      </h3>
      <div className="mb-6">
        <ScalingCalculator />
      </div>

      {/* Section 4 - Connector tunables */}
      <h3 className="text-lg font-medium text-gray-300 mb-3">
        Connector configuration
      </h3>
      <TunablesTable />
    </div>
  );
}
