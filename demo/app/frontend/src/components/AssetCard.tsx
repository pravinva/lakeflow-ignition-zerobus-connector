import { useNavigate } from 'react-router-dom';
import type { Asset } from '../services/api';
import { formatNumber } from '../utils/format';

interface AssetCardProps {
  asset: Asset;
}

function statusFromAlarmCode(code?: number): { label: string; color: string } {
  if (code === undefined || code === null || code === 0)
    return { label: 'OK', color: 'text-brand-green' };
  if (code < 100) return { label: 'Warning', color: 'text-brand-amber' };
  return { label: 'Alarm', color: 'text-brand-red' };
}

function typeIcon(type: string): string {
  return type === 'wind_turbine' ? '\u{1F32C}\uFE0F' : '\u{1F50B}';
}

export default function AssetCard({ asset }: AssetCardProps) {
  const navigate = useNavigate();
  const status = statusFromAlarmCode(asset.alarm_code);

  return (
    <button
      onClick={() => navigate(`/assets/${asset.asset_id}`)}
      className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-left
                 hover:border-databricks-primary/50 transition-colors w-full"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{typeIcon(asset.asset_type)}</span>
        <h3 className="font-semibold text-gray-100">{asset.asset_name}</h3>
      </div>
      <div className="space-y-1 text-sm">
        <p className="text-gray-400">
          {asset.site_name} &middot; {asset.tag_count} tags
        </p>
        <p>
          Status: <span className={status.color}>{status.label}</span>
        </p>
        {asset.compression_ratio && (
          <p className="text-gray-400">
            Compression: {formatNumber(asset.compression_ratio, 1)}:1
          </p>
        )}
        {asset.last_update && (
          <p className="text-gray-500 text-xs">
            Last update: {new Date(asset.last_update).toLocaleTimeString()}
          </p>
        )}
      </div>
    </button>
  );
}
