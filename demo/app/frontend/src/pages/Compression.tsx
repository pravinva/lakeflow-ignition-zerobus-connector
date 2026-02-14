import { useCallback } from 'react';
import { usePolling } from '../hooks/usePolling';
import { api } from '../services/api';
import CompressionWaterfall from '../components/CompressionWaterfall';
import type { CompressionLayer } from '../components/CompressionWaterfall';
import SdtTuningPanel from '../components/SdtTuningPanel';

export default function Compression() {
  const comparisonFetcher = useCallback(
    () =>
      api.getCompressionComparison().then((r) => {
        const data = r?.data;
        return Array.isArray(data) ? data : [];
      }) as Promise<CompressionLayer[]>,
    [],
  );

  const comparison = usePolling({
    fetcher: comparisonFetcher,
    intervalMs: 10000,
  });

  const handleApply = useCallback(
    async (config: { comp_dev_percent: number; comp_max_seconds: number }) => {
      await api.updateSdtConfig({ tag_pattern: '*', ...config });
    },
    [],
  );

  const layers = Array.isArray(comparison.data) ? comparison.data : [];
  const rawLayer = layers.find((l) => l.layer_name === 'raw');
  const deltaLayer =
    layers.find((l) => l.layer_name === 'after_delta') ?? layers.find((l) => l.layer_name === 'combined');
  const formatBytes = (b: number) => {
    const n = Number(b);
    if (n === 0 || !Number.isFinite(n)) return '0 B';
    if (n >= 1e9) return `${(n / 1e9).toFixed(2)} GB`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(2)} MB`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(2)} KB`;
    return `${Math.round(n)} B`;
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Compression</h2>

      {/* Data volume summary */}
      {rawLayer != null && deltaLayer != null && (
        <p className="text-sm text-gray-400 mb-4">
          Last 30 min: {rawLayer.event_count.toLocaleString()} rows ingested → {formatBytes(rawLayer.size_bytes)}{' '}
          (est.) → {formatBytes(deltaLayer.size_bytes)} on disk (Delta Lake, ZSTD).
        </p>
      )}

      {/* Waterfall section */}
      <div className="mb-6">
        <CompressionWaterfall layers={layers} />
      </div>

      {/* SDT tuning panel */}
      <div>
        <SdtTuningPanel
          compDevPercent={1.0}
          compMaxSeconds={600}
          onApply={handleApply}
        />
      </div>
    </div>
  );
}
