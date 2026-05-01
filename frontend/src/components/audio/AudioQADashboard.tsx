import React, { useState } from 'react';

export function AudioQADashboard() {
  const [path, setPath] = useState('');
  const [result, setResult] = useState<any>(null);

  async function analyze() {
    const res = await fetch('/api/v1/audio-quality-v2/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    setResult(await res.json());
  }

  return (
    <div className="rounded-2xl border p-4 shadow-sm">
      <h2 className="text-xl font-semibold">Audio QA Dashboard</h2>
      <div className="mt-3 flex gap-2">
        <input className="flex-1 rounded-lg border px-3 py-2" value={path} onChange={(e) => setPath(e.target.value)} placeholder="artifacts/audio/output.wav" />
        <button className="rounded-lg border px-4 py-2" onClick={analyze}>Phân tích</button>
      </div>
      {result && <pre className="mt-4 overflow-auto rounded-lg bg-gray-100 p-3 text-xs">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
