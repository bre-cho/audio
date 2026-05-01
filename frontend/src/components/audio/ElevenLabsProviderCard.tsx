import React, { useEffect, useState } from 'react';
import { getElevenLabsHealth, getElevenLabsUsage } from '../../api/elevenlabsProvider';

export function ElevenLabsProviderCard() {
  const [health, setHealth] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    Promise.all([getElevenLabsHealth(), getElevenLabsUsage()])
      .then(([h, u]) => { setHealth(h); setUsage(u); })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="rounded-2xl border p-4 shadow-sm">
      <h3 className="text-lg font-semibold">ElevenLabs Provider</h3>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {health && <p className="text-sm">Trạng thái: <b>{health.status}</b> — {health.message}</p>}
      {usage && <p className="text-sm">Quota: {usage.character_count ?? '?'} / {usage.character_limit ?? '?'}</p>}
      {health?.capabilities && (
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.entries(health.capabilities).map(([k, v]) => (
            <span key={k} className="rounded-full border px-2 py-1 text-xs">{k}: {v ? 'ready' : 'blocked'}</span>
          ))}
        </div>
      )}
    </div>
  );
}
