interface BigNumberCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  colorClass?: string;
  /** When set, shows a left accent border in the semantic color (good / warning / bad). */
  accent?: 'success' | 'warning' | 'error';
}

const accentBorderClass: Record<NonNullable<BigNumberCardProps['accent']>, string> = {
  success: 'border-l-4 border-l-semantic-success',
  warning: 'border-l-4 border-l-semantic-warning',
  error: 'border-l-4 border-l-semantic-error',
};

export default function BigNumberCard({
  label,
  value,
  subtitle,
  colorClass = 'text-databricks-primary',
  accent,
}: BigNumberCardProps) {
  return (
    <div
      className={`bg-surface-card border border-gray-200 rounded-card p-4 shadow-card transition-shadow duration-200 ${
        accent ? accentBorderClass[accent] : ''
      }`}
    >
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className={`text-4xl font-bold tabular-nums ${colorClass}`}>{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}
