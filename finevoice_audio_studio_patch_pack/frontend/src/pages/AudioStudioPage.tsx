import { useEffect, useState } from 'react';
import { getAudioStudioCapabilities } from '../api/audioStudio';
import { CapabilityBadge } from '../components/CapabilityBadge';

export default function AudioStudioPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    getAudioStudioCapabilities().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div>Lỗi: {error}</div>;
  if (!data) return <div>Đang tải Audio Studio...</div>;

  const modules = data.modules || {};
  return (
    <main className="audio-studio-page">
      <h1>AI Voice Studio</h1>
      <p>Trung tâm sản xuất giọng nói, clone voice, voice changer, SFX, podcast, enhancer và subtitle.</p>
      <section className="module-grid">
        {Object.entries(modules).map(([name, info]: any) => (
          <article key={name} className="module-card">
            <h3>{name}</h3>
            <CapabilityBadge status={info.status} />
            <p>Provider: {(info.providers || []).join(', ') || 'chưa có'}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
