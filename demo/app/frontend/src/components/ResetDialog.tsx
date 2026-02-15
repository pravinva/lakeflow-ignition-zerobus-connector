import { useState } from 'react';
import { api } from '../services/api';

export default function ResetDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    setLoading(true);
    try {
      await api.resetDemo();
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="px-3 py-1.5 rounded text-sm bg-brand-red/20 text-brand-red hover:bg-brand-red/30 transition-colors"
      >
        Reset Demo
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-white border border-gray-200 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Reset demo?</h3>
            <p className="text-gray-600 text-sm mb-6">
              Are you sure? This will truncate all demo tables and restart the simulator.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setOpen(false)}
                className="px-4 py-2 rounded text-sm bg-gray-100 text-gray-700 hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleReset}
                disabled={loading}
                className="px-4 py-2 rounded text-sm bg-brand-red text-white hover:bg-brand-red/80 disabled:opacity-50"
              >
                {loading ? 'Resetting...' : 'Confirm Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
