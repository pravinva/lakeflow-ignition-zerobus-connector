interface BigNumberCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  colorClass?: string;
}

export default function BigNumberCard({
  label,
  value,
  subtitle,
  colorClass = 'text-databricks-primary',
}: BigNumberCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}
