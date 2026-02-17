import { useCallback, useState, useEffect } from 'react';
import { usePolling } from '../hooks/usePolling';
import { api } from '../services/api';
import type { DiagnosticData } from '../services/api';
import ThroughputChart from '../components/ThroughputChart';
import BigNumberCard from '../components/BigNumberCard';
import EventStream from '../components/EventStream';
import { formatNumber, latencyColor } from '../utils/format';

type MetricsSource = 'raw_tags' | 'raw_throughput';
type WindowMinutes = 5 | 15 | 30 | 60;

export default function Dashboard() {
  const [metricsSource, setMetricsSource] = useState<MetricsSource>('raw_tags');
  const [windowMinutes, setWindowMinutes] = useState<WindowMinutes>(5);
  const [diagnostic, setDiagnostic] = useState<DiagnosticData | null>(null);
  const [diagnosticError, setDiagnosticError] = useState<string | null>(null);

  // Track backend errors from meta.error
  const [throughputError, setThroughputError] = useState<string | null>(null);
  const [latencyError, setLatencyError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);

  const throughputFetcher = useCallback(
    () =>
      api.getThroughput(metricsSource, windowMinutes).then((r) => {
        setThroughputError(r.meta?.error ?? null);
        return r.data;
      }),
    [metricsSource, windowMinutes],
  );
  const latencyFetcher = useCallback(
    () =>
      api.getLatency(metricsSource, windowMinutes).then((r) => {
        setLatencyError(r.meta?.error ?? null);
        return r.data;
      }),
    [metricsSource, windowMinutes],
  );
  const eventsFetcher = useCallback(
    () =>
      api.getEventsLatest(50).then((r) => {
        setEventsError(r.meta?.error ?? null);
        return r.data;
      }),
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
  const events = usePolling({
    fetcher: eventsFetcher,
    intervalMs: 2000,
  });

  // Fetch diagnostic when throughput data is empty (to explain why)
  const isEmpty =
    !throughput.loading && (!throughput.data || throughput.data.length === 0);
  useEffect(() => {
    if (!isEmpty) {
      setDiagnostic(null);
      setDiagnosticError(null);
      return;
    }
    let cancelled = false;
    api
      .getDiagnostic()
      .then((r) => {
        if (!cancelled) {
          setDiagnostic(r.data ?? null);
          setDiagnosticError(r.meta?.error ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDiagnostic(null);
          setDiagnosticError('Could not fetch diagnostic');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [isEmpty]);

  const latest = throughput.data?.at(-1);
  const latestLatency = latency.data?.at(-1);
  const windowSeconds = 5;
  const recordsPerSec =
    latest != null
      ? (Number(latest.records_after_sdt) || 0) / windowSeconds
      : null;

  // Compose empty-state / error message
  const backendError = throughputError || latencyError || eventsError;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h2 className="font-heading text-2xl font-semibold text-gray-900">Dashboard</h2>
        <div className="flex items-center gap-4">
          {/* Metrics source toggle — segmented control */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Metrics source:</span>
            <div className="flex rounded-card border border-gray-200 overflow-hidden bg-surface-card shadow-card">
              <button
                type="button"
                onClick={() => setMetricsSource('raw_tags')}
                className={`px-3 py-2 text-sm font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-databricks-primary focus-visible:ring-inset ${
                  metricsSource === 'raw_tags'
                    ? 'bg-databricks-primary text-white'
                    : 'bg-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                raw_tags
              </button>
              <button
                type="button"
                onClick={() => setMetricsSource('raw_throughput')}
                className={`px-3 py-2 text-sm font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-databricks-primary focus-visible:ring-inset ${
                  metricsSource === 'raw_throughput'
                    ? 'bg-databricks-primary text-white'
                    : 'bg-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                raw_throughput
              </button>
            </div>
            <span className="text-xs text-gray-500">
              {metricsSource === 'raw_tags' ? 'Zerobus landing' : 'Deduped (CDF)'}
            </span>
          </div>
          {/* Time window selector — segmented control */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Window:</span>
            <div className="flex rounded-card border border-gray-200 overflow-hidden bg-surface-card shadow-card">
              {([5, 15, 30, 60] as WindowMinutes[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setWindowMinutes(m)}
                  className={`px-2.5 py-2 text-xs font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-databricks-primary focus-visible:ring-inset ${
                    windowMinutes === m
                      ? 'bg-databricks-primary text-white'
                      : 'bg-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  {m}m
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Error / empty-state banner */}
      {backendError && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-card p-4 mb-6 text-sm text-red-800">
          <span className="flex h-5 w-5 flex-shrink-0 rounded-full bg-red-400 mt-0.5" aria-hidden />
          <div>
            <strong>Query error:</strong> {backendError}
          </div>
        </div>
      )}
      {isEmpty && !backendError && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-card p-4 mb-6 text-sm text-amber-800">
          <span className="flex h-5 w-5 flex-shrink-0 rounded-full bg-amber-300 mt-0.5" aria-hidden />
          <div>
            <strong>No events in the last {windowMinutes} minutes.</strong>{' '}
            Try a longer window or generate new events (e.g.{' '}
            <code className="text-xs bg-amber-100 px-1.5 py-0.5 rounded">make simulate-83</code>).
            {diagnostic && (
              <span className="block mt-1 text-amber-700">
                Table has <strong>{diagnostic.total_rows}</strong> total rows;{' '}
                <strong>{diagnostic.rows_last_10_min}</strong> in the last 10 min.
                {diagnostic.newest_event && (
                  <> Newest event: <code className="text-xs">{diagnostic.newest_event}</code></>
                )}
              </span>
            )}
            {diagnosticError && (
              <span className="block mt-1 text-amber-700">
                Diagnostic failed: {diagnosticError}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Big number cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <BigNumberCard
          label="Records/sec"
          value={
            recordsPerSec != null
              ? formatNumber(recordsPerSec, 0)
              : '-'
          }
          subtitle="Ingested (post-SDT)"
        />
        <BigNumberCard
          label="Active tags"
          value={latest ? formatNumber(latest.tags_active, 0) : '-'}
        />
        <BigNumberCard
          label="Active assets"
          value={
            events.data
              ? formatNumber(
                  new Set(events.data.map((e) => e.asset_id)).size,
                  0,
                )
              : '-'
          }
        />
        <BigNumberCard
          label="SDT compression ratio"
          value={
            latest
              ? (latest.sdt_enabled === true
                  ? (Number(latest.sdt_compression_ratio) <= 1 || latest.sdt_compression_ratio == null
                      ? 'On (no ratio yet)'
                      : `${formatNumber(Number(latest.sdt_compression_ratio), 1)}:1`)
                  : latest.sdt_enabled === false
                    ? 'Off'
                    : (Number(latest.sdt_compression_ratio) <= 1 || latest.sdt_compression_ratio == null
                        ? 'Off'
                        : `${formatNumber(Number(latest.sdt_compression_ratio), 1)}:1`))
              : '-'
          }
          subtitle={latest?.sdt_enabled != null ? (latest.sdt_enabled ? 'Gateway: SDT on' : 'Gateway: SDT off') : undefined}
          colorClass="text-brand-green"
        />
        {/* Primary: Time to insight (Ignition → Delta) when E2E available */}
        {latestLatency?.avg_e2e_latency_ms != null ? (
          <>
            <BigNumberCard
              label="Avg time to insight"
              value={`${formatNumber(latestLatency.avg_e2e_latency_ms, 0)}ms`}
              subtitle="Ignition → Delta"
              colorClass={latencyColor(latestLatency.avg_e2e_latency_ms)}
            />
            <BigNumberCard
              label="P99 time to insight"
              value={`${formatNumber(latestLatency.p99_e2e_latency_ms ?? 0, 0)}ms`}
              subtitle="Ignition → Delta"
            />
          </>
        ) : (
          <>
            <BigNumberCard
              label="Avg time to insight"
              value="-"
              subtitle="E2E when pipeline has CDF"
            />
            <BigNumberCard
              label="P99 time to insight"
              value="-"
              subtitle="E2E when pipeline has CDF"
            />
          </>
        )}
        <BigNumberCard
          label="Tag → connector"
          value={
            latestLatency
              ? `${formatNumber(latestLatency.avg_latency_ms, 0)}ms`
              : '-'
          }
          subtitle="In-process only"
          colorClass={
            latestLatency
              ? latencyColor(latestLatency.avg_latency_ms)
              : 'text-databricks-primary'
          }
        />
      </div>
      <p className="text-gray-500 text-sm mb-6">
        <strong>Time to insight</strong> = full path from tag event in Ignition to row committed in Delta
        (from <code>raw_throughput</code> CDF <code>_commit_timestamp</code>). Use <strong>raw_throughput</strong> for
        deduped metrics. "Tag → connector" is in-process only (no network/Zerobus/Delta).
      </p>

      {/* Throughput chart */}
      <div className="mb-6">
        <ThroughputChart data={throughput.data ?? []} />
      </div>

      {/* Live event stream */}
      <EventStream events={events.data ?? []} />
    </div>
  );
}
