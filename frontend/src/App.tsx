import { useEffect, useMemo, useState } from 'react';
import {
  Bell,
  Check,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  History,
  Library,
  Loader2,
  Mic,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  SlidersHorizontal,
  Sparkles,
  Upload,
  User,
  Volume2,
  WalletCards,
  Wand2,
  X,
  FolderOpen,
  MessageSquare,
  Grid2X2,
  Repeat2,
  Copy,
  Filter
} from 'lucide-react';
import { api } from './api';
import type { JobStatusOut, ProjectOut, ProviderCode, SettingsState, VoiceOut, Screen } from './types';

const fallbackVoices: VoiceOut[] = [
  { id: 'bella', name: 'Bella – Professional, Bright, Warm', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'deep-storyteller', name: 'Deep Storyteller – Magnetic, Smooth, Sophisticated', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'academic-lecturer', name: 'Academic Lecturer – Instructional, Clear', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'articulate-commentator', name: 'Articulate Commentator – Resonant, Sharp', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'calm-woman', name: 'Calm Woman – Sophisticated, Serene', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'casual-narrator', name: 'Casual Narrator – Natural, Fluid, Grounded', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'casual-podcaster', name: 'Casual Podcaster – Textured, Relatable', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'crisp-news', name: 'Crisp News Anchor – Clear, Elegant, Fast', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'energetic-commentator', name: 'Energetic Commentator – Engaging, Bright', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'friendly-girl', name: 'Friendly Girl – Sweet, Approachable, Warm', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'cloned-empty', name: 'Giọng MiniMax của tôi', source_type: 'cloned', language_code: 'vi', gender: 'male', is_active: true }
];

const minimaxModels = [
  'Speech 2.8 HD',
  'Speech 2.8 Turbo',
  'Speech 2.6 HD',
  'Speech 2.6 Turbo',
  'Speech 2.5 HD Preview',
  'Speech 2.5 Turbo Preview',
  'Speech 02 HD',
  'Speech 02 Turbo',
  'Speech 01 HD',
  'Speech 01 Turbo'
];

const elevenModels = ['Eleven Multilingual v2', 'Eleven Turbo v2.5', 'Eleven English v1'];

const languages = [
  { label: 'English', value: 'en', flag: '🇺🇸' },
  { label: 'Vietnamese', value: 'vi', flag: '🇻🇳' },
  { label: 'Chinese (Mandarin)', value: 'zh', flag: '🇨🇳' },
  { label: 'Cantonese', value: 'yue', flag: '🇭🇰' },
  { label: 'Japanese', value: 'ja', flag: '🇯🇵' },
  { label: 'Korean', value: 'ko', flag: '🇰🇷' }
];

function cx(...items: Array<string | false | undefined>) {
  return items.filter(Boolean).join(' ');
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('tts');
  const [provider, setProvider] = useState<ProviderCode>('elevenlabs');
  const [settings, setSettings] = useState<SettingsState>({
    provider: 'elevenlabs',
    model: 'Eleven Multilingual v2',
    voiceId: 'bella',
    speed: 1,
    stability: 50,
    similarity: 75,
    style: 0,
    speakerBoost: true,
    language: 'en',
    gender: 'Nam'
  });
  const [voices, setVoices] = useState<VoiceOut[]>(fallbackVoices);
  const [jobs, setJobs] = useState<JobStatusOut[]>([]);
  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [credits, setCredits] = useState(10000);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [cloneOpen, setCloneOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const accent = provider === 'minimax' ? 'purple' : 'teal';

  useEffect(() => {
    setSettings((prev) => ({
      ...prev,
      provider,
      model: provider === 'minimax' ? 'Speech 2.8 Turbo' : 'Eleven Multilingual v2',
      voiceId: provider === 'minimax' ? 'deep-storyteller' : 'bella'
    }));
  }, [provider]);

  useEffect(() => {
    api.voices().then((data) => data.length && setVoices(data)).catch(() => undefined);
    api.jobs().then(setJobs).catch(() => undefined);
    api.projects().then(setProjects).catch(() => undefined);
    api.balance().then((data) => setCredits(data.balance_credits)).catch(() => undefined);
  }, []);

  const selectedVoice = useMemo(() => {
    return voices.find((v) => v.id === settings.voiceId) || voices[0] || fallbackVoices[0];
  }, [voices, settings.voiceId]);

  function updateSettings(patch: Partial<SettingsState>) {
    setSettings((prev) => ({ ...prev, ...patch }));
  }

  async function submitText(text: string, mode: 'tts' | 'conversation') {
    if (!text.trim()) {
      setToast('Vui lòng nhập nội dung trước khi tạo giọng nói.');
      return;
    }
    setBusy(true);
    try {
      let job: JobStatusOut;
      if (mode === 'conversation') {
        const parsed = await api.parseConversation(text);
        const speakerMap: Record<string, string | null> = {};
        parsed.lines.forEach((line) => { speakerMap[line.speaker] = selectedVoice?.id || null; });
        job = await api.generateConversation({
          script: parsed.lines,
          speaker_voice_map: speakerMap,
          provider_strategy: 'per_voice',
          merge_output: true
        });
      } else {
        job = await api.ttsGenerate({
          text,
          provider,
          model: settings.model,
          voice_id: isUuid(settings.voiceId) ? settings.voiceId : undefined,
          speed: settings.speed,
          stability: settings.stability,
          similarity_boost: settings.similarity,
          style: settings.style,
          speaker_boost: settings.speakerBoost,
          format: 'mp3'
        });
      }
      setJobs((prev) => [job, ...prev]);
      setToast(`Đã tạo job ${job.job_id || job.id}. Trạng thái: ${job.status}`);
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể tạo job audio.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={cx('app-shell', `theme-${accent}`)}>
      <Sidebar screen={screen} setScreen={setScreen} />
      <main className="main-area">
        <TopBar screen={screen} />
        {screen === 'tts' && <TextWorkspace busy={busy} credits={credits} onSubmit={(text) => submitText(text, 'tts')} />}
        {screen === 'conversation' && <ConversationWorkspace busy={busy} credits={credits} onSubmit={(text) => submitText(text, 'conversation')} />}
        {screen === 'voiceChanger' && <VoiceChangerWorkspace />}
        {screen === 'studio' && <StudioWorkspace projects={projects} onCreate={async () => {
          const title = `Dự án audio ${projects.length + 1}`;
          const p = await api.createProject(title);
          setProjects((prev) => [p, ...prev]);
        }} />}
        {screen === 'history' && <HistoryWorkspace jobs={jobs} />}
      </main>
      <ConfigPanel
        provider={provider}
        setProvider={setProvider}
        settings={settings}
        updateSettings={updateSettings}
        selectedVoice={selectedVoice}
        onOpenLibrary={() => setLibraryOpen(true)}
        onOpenClone={() => setCloneOpen(true)}
        jobs={jobs}
      />
      {libraryOpen && (
        <VoiceLibraryModal
          voices={voices}
          selectedVoiceId={settings.voiceId}
          onClose={() => setLibraryOpen(false)}
          onSelect={(voice) => {
            updateSettings({ voiceId: voice.id });
            setLibraryOpen(false);
          }}
          onOpenClone={() => setCloneOpen(true)}
        />
      )}
      {cloneOpen && <CloneVoiceModal onClose={() => setCloneOpen(false)} />}
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}

function isUuid(value?: string) {
  return Boolean(value && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value));
}

function Sidebar({ screen, setScreen }: { screen: Screen; setScreen: (screen: Screen) => void }) {
  const items = [
    { group: 'Khu thử nghiệm', rows: [
      { id: 'tts' as Screen, label: 'Văn bản thành giọng nói', icon: Mic },
      { id: 'conversation' as Screen, label: 'Hội thoại', icon: MessageSquare },
      { id: 'voiceChanger' as Screen, label: 'Thay đổi giọng nói', icon: Repeat2, badge: 'NEW' }
    ] },
    { group: 'Tài nguyên', rows: [
      { id: 'library' as Screen, label: 'Thư viện giọng nói', icon: Library },
      { id: 'history' as Screen, label: 'Lịch sử', icon: History }
    ] },
    { group: 'Công cụ', rows: [
      { id: 'affiliate' as Screen, label: 'Tiếp thị liên kết', icon: WalletCards },
      { id: 'studio' as Screen, label: 'Studio âm thanh', icon: Grid2X2, badge: 'NEW' },
      { id: 'aiEffects' as Screen, label: 'Hiệu ứng AI', icon: Sparkles, badge: 'Coming soon', disabled: true }
    ] }
  ];

  return (
    <aside className="sidebar">
      <div className="brand"><span>GENSUITE</span><strong>AUDIO</strong></div>
      <div className="sidebar-groups">
        {items.map((group) => (
          <section key={group.group}>
            <p className="group-title">{group.group}</p>
            {group.rows.map((item) => {
              const Icon = item.icon;
              const active = screen === item.id || (item.id === 'library' && false);
              return (
                <button
                  key={item.id}
                  className={cx('nav-item', active && 'active', item.disabled && 'disabled')}
                  onClick={() => !item.disabled && (item.id === 'library' ? undefined : setScreen(item.id))}
                  type="button"
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {item.badge && <em>{item.badge}</em>}
                </button>
              );
            })}
          </section>
        ))}
      </div>
      <button className="buy-credits" type="button"><ShoppingCart size={17} /> MUA CREDITS</button>
    </aside>
  );
}

function TopBar({ screen }: { screen: Screen }) {
  const titles: Record<Screen, string> = {
    tts: 'Text to Speech',
    conversation: 'Conversation',
    voiceChanger: 'Voice Changer',
    studio: 'Studio',
    library: 'Thư viện giọng nói',
    history: 'Lịch sử',
    affiliate: 'Tiếp thị liên kết',
    aiEffects: 'Hiệu ứng AI'
  };
  return (
    <header className="topbar">
      <div className="top-title"><span className="title-dot" />{titles[screen]}</div>
      <div className="top-actions">
        <button>VN</button>
        <HelpCircle size={18} />
        <Bell size={18} />
        <div className="avatar">K</div>
      </div>
    </header>
  );
}

function TextWorkspace({ busy, credits, onSubmit }: { busy: boolean; credits: number; onSubmit: (text: string) => void }) {
  const [text, setText] = useState('');
  return (
    <section className="workspace">
      <div className="big-watermark">ElevenLabs</div>
      <textarea className="hero-editor" value={text} onChange={(e) => setText(e.target.value)} placeholder="Nhập văn bản của bạn vào đây để bắt đầu tổng hợp giọng nói..." />
      <BottomComposer credits={credits} countLabel="Ký tự" count={text.length} busy={busy} button="TẠO GIỌNG NÓI" onClick={() => onSubmit(text)} />
    </section>
  );
}

function ConversationWorkspace({ busy, credits, onSubmit }: { busy: boolean; credits: number; onSubmit: (text: string) => void }) {
  const [text, setText] = useState('');
  const speakers = new Set(text.split('\n').map((line) => line.split(':')[0]?.trim()).filter(Boolean));
  return (
    <section className="workspace">
      <div className="big-watermark">ElevenLabs</div>
      <textarea
        className="hero-editor conversation"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={'Dán kịch bản hội thoại của bạn vào đây...\n\nVí dụ:\nAn: Xin chào, bạn khỏe không?\nBình: Mình khỏe, cảm ơn bạn!'}
      />
      <div className="conversation-metrics"><span>ĐOẠN<br />{text.trim() ? text.split('\n').filter(Boolean).length : 0}</span><span>NGƯỜI NÓI<br />{speakers.size}</span></div>
      <BottomComposer credits={credits} countLabel="Ký tự" count={text.length} busy={busy} button="TẠO GIỌNG NÓI" onClick={() => onSubmit(text)} />
    </section>
  );
}

function VoiceChangerWorkspace() {
  return (
    <section className="workspace voice-change">
      <label className="dropzone">
        <Upload size={34} />
        <strong>Thả file âm thanh vào đây hoặc bấm để chọn</strong>
        <span>MP3, M4A, WAV | Max 50MB | Up to 5 minutes</span>
        <input type="file" accept="audio/*" />
      </label>
      <div className="fixed-action"><button className="primary-pill disabled" type="button"><Repeat2 size={18} /> ĐỔI GIỌNG</button></div>
    </section>
  );
}

function StudioWorkspace({ projects, onCreate }: { projects: ProjectOut[]; onCreate: () => void }) {
  return (
    <section className="workspace studio-page">
      <div className="studio-head">
        <div><h1>Danh sách dự án</h1><p><span /> {projects.length}/50 dự án</p></div>
        <button className="new-project" onClick={onCreate} type="button"><Plus size={18} /> Dự án mới</button>
      </div>
      {projects.length === 0 ? (
        <div className="empty-state"><FolderOpen size={46} /><h2>Chưa có dự án nào</h2><p>Tạo dự án đầu tiên để bắt đầu tạo audio hàng loạt.</p></div>
      ) : (
        <div className="project-grid">{projects.map((p) => <article key={p.id} className="project-card"><h3>{p.title}</h3><p>{p.status}</p></article>)}</div>
      )}
    </section>
  );
}

function HistoryWorkspace({ jobs }: { jobs: JobStatusOut[] }) {
  return (
    <section className="workspace history-page">
      <h1>Lịch sử job</h1>
      <div className="history-list">
        {jobs.length === 0 ? <div className="empty-state small"><History size={42} /><h2>Chưa có job nào</h2></div> : jobs.map((job) => (
          <article key={job.id} className="history-card"><span>{job.job_type}</span><strong>{job.status}</strong><small>{job.error_message || job.id}</small></article>
        ))}
      </div>
    </section>
  );
}

function BottomComposer({ credits, countLabel, count, busy, button, onClick }: { credits: number; countLabel: string; count: number; busy: boolean; button: string; onClick: () => void }) {
  return (
    <footer className="bottom-composer">
      <div className="credits-dot" /><span>{credits.toLocaleString()} Credits còn lại</span>
      <div className="composer-spacer" />
      <span>{countLabel}: {count}</span>
      <button className="round-upload" type="button"><Upload size={18} /></button>
      <button className="primary-pill" disabled={busy} type="button" onClick={onClick}>{busy ? <Loader2 className="spin" size={18} /> : <Play size={18} />} {button}</button>
    </footer>
  );
}

function ConfigPanel({ provider, setProvider, settings, updateSettings, selectedVoice, onOpenLibrary, onOpenClone, jobs }: {
  provider: ProviderCode;
  setProvider: (p: ProviderCode) => void;
  settings: SettingsState;
  updateSettings: (patch: Partial<SettingsState>) => void;
  selectedVoice: VoiceOut;
  onOpenLibrary: () => void;
  onOpenClone: () => void;
  jobs: JobStatusOut[];
}) {
  const [tab, setTab] = useState<'config' | 'history'>('config');
  const models = provider === 'minimax' ? minimaxModels : elevenModels;

  return (
    <aside className="config-panel">
      <div className="panel-tabs"><button className={tab === 'config' ? 'active' : ''} onClick={() => setTab('config')}>Cấu hình</button><button className={tab === 'history' ? 'active' : ''} onClick={() => setTab('history')}>Lịch sử</button></div>
      {tab === 'history' ? <PanelHistory jobs={jobs} /> : (
        <div className="config-scroll">
          <PanelLabel>Nhà cung cấp</PanelLabel>
          <div className="provider-switch">
            <button className="provider disabled"><span>G</span><strong>GENVOICE</strong><small>ĐANG BẢO TRÌ</small></button>
            <button className={cx('provider', provider === 'elevenlabs' && 'selected')} onClick={() => setProvider('elevenlabs')}><Volume2 size={22} /><strong>ELEVENLABS</strong></button>
            <button className={cx('provider', provider === 'minimax' && 'selected')} onClick={() => setProvider('minimax')}><SlidersHorizontal size={22} /><strong>MINIMAX</strong></button>
          </div>

          <PanelLabel action="ĐỒNG BỘ GIỌNG NÓI">Giọng nói</PanelLabel>
          <button className="voice-select" onClick={onOpenLibrary} type="button"><span className="voice-icon"><User size={22} /></span><span><strong>{selectedVoice?.name || 'Chọn giọng nói'}</strong><small>{provider === 'minimax' ? 'MINIMAX SYSTEM' : 'DEFAULT'}</small></span><ChevronDown size={18} /></button>

          {provider === 'minimax' && <button className="clone-cta" onClick={onOpenClone} type="button"><Copy size={22} /> SAO CHÉP GIỌNG NÓI <ChevronRight size={18} /></button>}

          <PanelLabel>Mô hình</PanelLabel>
          <SelectBox value={settings.model} options={models} onChange={(value) => updateSettings({ model: value })} />

          {provider === 'minimax' && <><PanelLabel>Ngôn ngữ *</PanelLabel><LanguageSelect value={settings.language} onChange={(language) => updateSettings({ language })} /></>}

          <Slider label="Tốc độ" value={settings.speed} min={0.5} max={2} step={0.1} suffix="x" onChange={(speed) => updateSettings({ speed })} />
          {provider === 'minimax' && <Slider label="Cao độ" value={0} min={-12} max={12} step={1} onChange={() => undefined} />}
          <Slider label="Độ ổn định" value={settings.stability} min={0} max={100} step={1} suffix="%" onChange={(stability) => updateSettings({ stability })} />
          <Slider label="Độ tương đồng" value={settings.similarity} min={0} max={100} step={1} suffix="%" onChange={(similarity) => updateSettings({ similarity })} />
          <Slider label="Phóng đại phong cách" value={settings.style} min={0} max={100} step={1} suffix="%" onChange={(style) => updateSettings({ style })} />
          <div className="toggle-row"><strong>Tăng cường loa</strong><button className={cx('switch', settings.speakerBoost && 'on')} onClick={() => updateSettings({ speakerBoost: !settings.speakerBoost })}><span /></button></div>
        </div>
      )}
    </aside>
  );
}

function PanelLabel({ children, action }: { children: string; action?: string }) {
  return <div className="panel-label"><span>{children}</span>{action && <button>{action}</button>}</div>;
}

function SelectBox({ value, options, onChange }: { value: string; options: string[]; onChange: (value: string) => void }) {
  return <select className="select-box" value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o}>{o}</option>)}</select>;
}

function LanguageSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return <select className="select-box language-select" value={value} onChange={(e) => onChange(e.target.value)}>{languages.map((l) => <option key={l.value} value={l.value}>{l.flag} {l.label}</option>)}</select>;
}

function Slider({ label, value, min, max, step, suffix = '', onChange }: { label: string; value: number; min: number; max: number; step: number; suffix?: string; onChange: (value: number) => void }) {
  return (
    <div className="slider-row"><div><span>{label}</span><strong>{value}{suffix}</strong></div><input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} /></div>
  );
}

function PanelHistory({ jobs }: { jobs: JobStatusOut[] }) {
  return <div className="panel-history">{jobs.length === 0 ? <p>Chưa có lịch sử tạo audio.</p> : jobs.slice(0, 12).map((job) => <div key={job.id} className="panel-job"><strong>{job.job_type}</strong><span>{job.status}</span></div>)}</div>;
}

function VoiceLibraryModal({ voices, selectedVoiceId, onClose, onSelect, onOpenClone }: { voices: VoiceOut[]; selectedVoiceId?: string; onClose: () => void; onSelect: (voice: VoiceOut) => void; onOpenClone: () => void }) {
  const [tab, setTab] = useState<'all' | 'cloned'>('all');
  const [query, setQuery] = useState('');
  const filtered = voices.filter((v) => (tab === 'all' ? true : v.source_type === 'cloned')).filter((v) => v.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="modal-backdrop"><div className="voice-modal">
      <header className="modal-head"><div className="segmented"><button className={tab === 'all' ? 'active' : ''} onClick={() => setTab('all')}>TẤT CẢ VOICE</button><button className={tab === 'cloned' ? 'active' : ''} onClick={() => setTab('cloned')}>NHÂN BẢN</button></div><div className="modal-search"><Search size={18} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm kiếm giọng nói..." /></div><button className="modal-close" onClick={onClose}><X size={28} /></button></header>
      {tab === 'cloned' && filtered.length === 0 ? <div className="empty-voice"><Search size={46} /><p>Không tìm thấy giọng nói nào</p><button className="clone-cta wide" onClick={onOpenClone}><Copy size={20} /> TẠO GIỌNG NHÂN BẢN</button></div> : (
        <div className="modal-body"><aside className="filter-side"><h4><Filter size={15} /> Bộ lọc</h4>{['ALL', 'SYSTEM', 'CLONED'].map((x) => <button key={x} className={(x.toLowerCase() === tab || (tab === 'all' && x === 'ALL')) ? 'active' : ''} onClick={() => setTab(x === 'CLONED' ? 'cloned' : 'all')}>{x}</button>)}</aside><section className="voice-grid">{filtered.map((voice) => <button key={voice.id} className={cx('voice-card', selectedVoiceId === voice.id && 'selected')} onClick={() => onSelect(voice)}><span className="play-box"><Play size={15} /></span><span><strong>{voice.name}</strong><small>{voice.source_type === 'cloned' ? 'CLONED' : 'SYSTEM'}</small></span>{selectedVoiceId === voice.id && <Check size={18} />}</button>)}</section></div>
      )}
      <footer className="modal-foot"><span>● {voices.length} TỔNG SỐ GIỌNG NÓI ĐÃ ĐĂNG KÝ</span><span>■ ĐÃ CHỌN &nbsp;&nbsp; ■ CÓ SẴN</span></footer>
    </div></div>
  );
}

function CloneVoiceModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('Giọng MiniMax của tôi');
  const [gender, setGender] = useState<'Nam' | 'Nữ'>('Nam');
  const [language, setLanguage] = useState('en');
  const [consent, setConsent] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function createClone() {
    if (!consent) { setStatus('Bạn cần xác nhận có quyền sử dụng mẫu giọng nói này.'); return; }
    try {
      const upload = await api.uploadCloneSample();
      const job = await api.createClone({ name, provider: 'minimax', language_code: language, gender, sample_file_id: upload.file_id, denoise, consent_confirmed: consent });
      setStatus(`Đã tạo job nhân bản: ${job.status}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Không thể tạo job nhân bản.');
    }
  }

  return (
    <div className="modal-backdrop"><div className="clone-modal">
      <header className="modal-head"><div className="segmented"><button disabled>TẤT CẢ VOICE</button><button className="active">NHÂN BẢN</button></div><div className="modal-search"><Search size={18} /><input placeholder="Tìm kiếm giọng nói..." /></div><button className="modal-close" onClick={onClose}><X size={28} /></button></header>
      <div className="clone-form"><button className="refresh"><RefreshCw size={18} /></button><h2>Tạo giọng mới</h2><div className="form-line"><input value={name} onChange={(e) => setName(e.target.value)} /><select value={gender} onChange={(e) => setGender(e.target.value as 'Nam' | 'Nữ')}><option>Nam</option><option>Nữ</option></select></div><select value={language} onChange={(e) => setLanguage(e.target.value)}>{languages.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}</select><textarea defaultValue="Xin chào. Đây là bản xem thử giọng MiniMax của tôi." /><div className="sample-row"><span>Mẫu âm thanh</span><div><button>Tải lên</button><button>Thu âm</button></div></div><label className="upload-zone">Tải lên hoặc thu âm một mẫu giọng (tối đa 20MB)</label><div className="check-row"><label><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> Tôi xác nhận có quyền sử dụng mẫu giọng nói này. <b>BẮT BUỘC</b></label><label><input type="checkbox" checked={denoise} onChange={(e) => setDenoise(e.target.checked)} /> Khử tiếng ồn</label></div><button className="clone-submit" onClick={createClone}><Copy size={24} /> BẮT ĐẦU NHÂN BẢN <span>-1,000 CREDITS</span><ChevronRight /></button>{status && <p className="form-status">{status}</p>}</div>
      <footer className="modal-foot"><span>● 0 TỔNG SỐ GIỌNG NÓI ĐÃ ĐĂNG KÝ</span><span>■ ĐÃ CHỌN &nbsp;&nbsp; ■ CÓ SẴN</span></footer>
    </div></div>
  );
}

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  return <div className="toast"><span>{message}</span><button onClick={onClose}><X size={16} /></button></div>;
}
