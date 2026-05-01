import React, { useEffect, useState } from 'react';

type Capability = {
  capability: string;
  status: 'ready' | 'partial' | 'disabled' | 'blocked' | 'planned';
  provider?: string | null;
  reason: string;
};

export function CapabilityMatrix() {
  const [items, setItems] = useState<Capability[]>([]);

  useEffect(() => {
    fetch('/api/v1/system-capabilities-v2')
      .then((r) => r.json())
      .then((data) => setItems(Object.values(data.capabilities || {})))
      .catch(() => setItems([]));
  }, []);

  return (
    <div className="rounded-2xl border p-4 shadow-sm">
      <h2 className="text-xl font-semibold">Ma trận năng lực hệ thống</h2>
      <p className="text-sm opacity-70">Nút tính năng chỉ nên bật khi trạng thái là ready.</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div key={item.capability} className="rounded-xl border p-3">
            <div className="font-medium">{item.capability}</div>
            <div className="text-sm">Trạng thái: <b>{item.status}</b></div>
            <div className="text-sm">Provider: {item.provider || '-'}</div>
            <div className="text-xs opacity-70">{item.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
