import type { TagEvent } from '../services/api';
import { qualityLabel, formatTimestamp, formatNumber } from '../utils/format';

interface EventStreamProps {
  events: TagEvent[];
}

export default function EventStream({ events }: EventStreamProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">
        Live event stream
      </h3>
      <div className="overflow-auto max-h-96">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-800">
              <th className="text-left py-2 px-2">Timestamp</th>
              <th className="text-left py-2 px-2">Asset</th>
              <th className="text-left py-2 px-2">Tag</th>
              <th className="text-right py-2 px-2">Value</th>
              <th className="text-left py-2 px-2">Quality</th>
              <th className="text-right py-2 px-2">Latency</th>
              <th className="text-center py-2 px-2">SDT</th>
            </tr>
          </thead>
          <tbody>
            {events.map((evt, i) => {
              const latencyMs =
                new Date(evt.ingest_timestamp).getTime() -
                new Date(evt.event_timestamp).getTime();
              return (
                <tr
                  key={`${evt.event_timestamp}-${evt.asset_id}-${evt.tag_name}-${i}`}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="py-1.5 px-2 text-gray-300">
                    {formatTimestamp(evt.event_timestamp)}
                  </td>
                  <td className="py-1.5 px-2 text-gray-300">{evt.asset_id}</td>
                  <td className="py-1.5 px-2 text-gray-400">{evt.tag_name}</td>
                  <td className="py-1.5 px-2 text-right text-gray-100">
                    {formatNumber(evt.tag_value)}
                  </td>
                  <td className="py-1.5 px-2 text-gray-400">
                    {qualityLabel(evt.quality)}
                  </td>
                  <td className="py-1.5 px-2 text-right text-gray-400">
                    {formatNumber(latencyMs, 0)}ms
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    {evt.sdt_compressed ? (
                      <span className="text-brand-green" title="Survived SDT">Post-SDT</span>
                    ) : (
                      <span className="text-gray-500" title="Pass-through (SDT off or non-numeric)">Raw</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
