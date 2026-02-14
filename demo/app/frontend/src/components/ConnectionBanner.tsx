interface ConnectionBannerProps {
  connected: boolean;
}

export default function ConnectionBanner({ connected }: ConnectionBannerProps) {
  if (connected) return null;

  return (
    <div className="bg-brand-red/20 border border-brand-red text-brand-red px-4 py-2 text-center text-sm rounded-lg mb-4">
      Connection Lost - Unable to reach the Databricks backend
    </div>
  );
}
