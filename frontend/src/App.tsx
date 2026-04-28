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
  { id: 'bella', name: 'Bella – Chuyên nghiệp, tươi sáng, ấm áp', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'deep-storyteller', name: 'Người kể chuyện trầm ấm – Cuốn hút, mượt mà, tinh tế', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'academic-lecturer', name: 'Diễn giả học thuật – Rõ ràng, dễ theo dõi', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'articulate-commentator', name: 'Bình luận viên mạch lạc – Vang, sắc nét', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'calm-woman', name: 'Nữ giọng điềm tĩnh – Thanh lịch, nhẹ nhàng', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'casual-narrator', name: 'Người dẫn chuyện tự nhiên – Linh hoạt, gần gũi', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'casual-podcaster', name: 'Podcaster tự nhiên – Có chiều sâu, thân thiện', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'crisp-news', name: 'MC bản tin rõ nét – Rõ ràng, thanh lịch, nhanh', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
  { id: 'energetic-commentator', name: 'Bình luận viên năng lượng – Sinh động, sáng rõ', source_type: 'system', language_code: 'en', gender: 'male', is_active: true },
  { id: 'friendly-girl', name: 'Giọng nữ thân thiện – Ngọt ngào, gần gũi, ấm áp', source_type: 'system', language_code: 'en', gender: 'female', is_active: true },
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
  { label: 'Tiếng Anh', value: 'en', flag: '🇺🇸' },
  { label: 'Tiếng Việt', value: 'vi', flag: '🇻🇳' },
  { label: 'Tiếng Trung (Quan Thoại)', value: 'zh', flag: '🇨🇳' },
  { label: 'Tiếng Quảng Đông', value: 'yue', flag: '🇭🇰' },
  { label: 'Tiếng Nhật', value: 'ja', flag: '🇯🇵' },
  { label: 'Tiếng Hàn', value: 'ko', flag: '🇰🇷' }
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
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [credits, setCredits] = useState(10000);
  const [cloneOpen, setCloneOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [studioBusy, setStudioBusy] = useState(false);
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
    api.libraryVoices({ limit: 200 }).then((data) => data.length && setVoices(data)).catch(() => undefined);
    api.jobs().then(setJobs).catch(() => undefined);
    api.projects().then((data) => {
      setProjects(data);
      setSelectedProjectId((current) => current || data[0]?.id || null);
    }).catch(() => undefined);
    api.balance().then((data) => setCredits(data.balance_credits)).catch(() => undefined);
  }, []);

  useEffect(() => {
    let destroyed = false;
    let stream: EventSource | null = null;
    let reconnectTimer: number | null = null;
    let pollingTimer: number | null = null;
    let reconnectAttempt = 0;
    let pollingActive = false;

    const clearReconnectTimer = () => {
      if (reconnectTimer != null) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    const clearPollingTimer = () => {
      if (pollingTimer != null) {
        window.clearTimeout(pollingTimer);
        pollingTimer = null;
      }
    };

    const pollJobs = async () => {
      try {
        const nextJobs = await api.jobs();
        if (!destroyed) {
          setJobs(nextJobs);
        }
      } catch {
        // Keep last known jobs while backend is unavailable.
      } finally {
        if (!destroyed && pollingActive) {
          pollingTimer = window.setTimeout(() => {
            void pollJobs();
          }, 5000);
        }
      }
    };

    const startPollingFallback = () => {
      if (pollingActive || destroyed) {
        return;
      }
      pollingActive = true;
      void pollJobs();
    };

    const stopPollingFallback = () => {
      pollingActive = false;
      clearPollingTimer();
    };

    const connectStream = () => {
      if (destroyed) {
        return;
      }

      const nextStream = new EventSource(api.jobsStreamUrl());
      stream = nextStream;

      const onJobs = (event: MessageEvent<string>) => {
        try {
          const nextJobs = JSON.parse(event.data) as JobStatusOut[];
          setJobs(nextJobs);
        } catch {
          // Ignore malformed stream events and keep the last known job list.
        }
      };

      nextStream.onopen = () => {
        reconnectAttempt = 0;
        stopPollingFallback();
      };

      nextStream.addEventListener('jobs', onJobs as EventListener);
      nextStream.onerror = () => {
        nextStream.removeEventListener('jobs', onJobs as EventListener);
        nextStream.close();
        stream = null;

        startPollingFallback();
        clearReconnectTimer();
        const delayMs = Math.min(30000, 1000 * (2 ** Math.min(reconnectAttempt, 5)));
        reconnectAttempt += 1;
        reconnectTimer = window.setTimeout(connectStream, delayMs);
      };
    };

    connectStream();

    return () => {
      destroyed = true;
      clearReconnectTimer();
      clearPollingTimer();
      if (stream) {
        stream.close();
        stream = null;
      }
    };
  }, []);

  const selectedVoice = useMemo(() => {
    return voices.find((v) => v.id === settings.voiceId) || voices[0] || fallbackVoices[0];
  }, [voices, settings.voiceId]);

  function updateSettings(patch: Partial<SettingsState>) {
    setSettings((prev) => ({ ...prev, ...patch }));
  }

  async function handleCreateProject() {
    const title = `Dự án audio ${projects.length + 1}`;
    const project = await api.createProject(title);
    setProjects((prev) => [project, ...prev]);
    setSelectedProjectId(project.id);
    setScreen('studio');
  }

  async function handleSaveProjectScript(projectId: string, rawText: string) {
    setStudioBusy(true);
    try {
      await api.addProjectScript(projectId, {
        asset_type: 'script',
        title: 'Narration script',
        raw_text: rawText,
        language_code: settings.language,
        metadata_json: { source: 'frontend-studio' }
      });
      setToast('Đã lưu script cho dự án.');
      const refreshed = await api.project(projectId);
      setProjects((prev) => prev.map((item) => item.id === refreshed.id ? refreshed : item));
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể lưu script dự án.');
    } finally {
      setStudioBusy(false);
    }
  }

  async function handleRenderProject(projectId: string) {
    setStudioBusy(true);
    try {
      const job = await api.batchGenerateProject(projectId);
      setJobs((prev) => [job, ...prev.filter((item) => item.id !== job.id)]);
      setToast(`Đã tạo job render dự án ${job.job_id || job.id}.`);
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể render dự án.');
    } finally {
      setStudioBusy(false);
    }
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
        {screen === 'library' && <VoiceLibraryWorkspace voices={voices} selectedVoiceId={settings.voiceId} onSelect={(voice) => updateSettings({ voiceId: voice.id })} onOpenClone={() => setCloneOpen(true)} />}
        {screen === 'studio' && <StudioWorkspace projects={projects} selectedProjectId={selectedProjectId} onCreate={handleCreateProject} onSelectProject={setSelectedProjectId} onSaveScript={handleSaveProjectScript} onRenderProject={handleRenderProject} busy={studioBusy} />}
        {screen === 'history' && <HistoryWorkspace jobs={jobs} />}
        {screen === 'affiliate' && <AffiliateWorkspace />}
        {screen === 'aiEffects' && <AiEffectsWorkspace />}
        {screen === 'governance' && <GovernanceWorkspace />}
      </main>
      <ConfigPanel
        provider={provider}
        setProvider={setProvider}
        settings={settings}
        updateSettings={updateSettings}
        selectedVoice={selectedVoice}
        onOpenLibrary={() => setScreen('library')}
        onOpenClone={() => setCloneOpen(true)}
        jobs={jobs}
      />
      {cloneOpen && <CloneVoiceModal onClose={() => setCloneOpen(false)} onJobCreated={(job) => setJobs((prev) => [job, ...prev.filter((item) => item.id !== job.id)])} onUploaded={(voiceFileName) => setToast(`Đã tải mẫu giọng ${voiceFileName}.`)} />}
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
      { id: 'voiceChanger' as Screen, label: 'Thay đổi giọng nói', icon: Repeat2, badge: 'MỚI' }
    ] },
    { group: 'Tài nguyên', rows: [
      { id: 'library' as Screen, label: 'Thư viện giọng nói', icon: Library },
      { id: 'history' as Screen, label: 'Lịch sử', icon: History }
    ] },
    { group: 'Công cụ', rows: [
      { id: 'affiliate' as Screen, label: 'Tiếp thị liên kết', icon: WalletCards },
      { id: 'studio' as Screen, label: 'Xưởng âm thanh', icon: Grid2X2, badge: 'MỚI' },
      { id: 'aiEffects' as Screen, label: 'Hiệu ứng AI', icon: Sparkles },
      { id: 'governance' as Screen, label: 'Governance', icon: SlidersHorizontal, badge: 'OPS' }
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
              const active = screen === item.id;
              return (
                <button
                  key={item.id}
                  className={cx('nav-item', active && 'active', (item as { disabled?: boolean }).disabled && 'disabled')}
                  onClick={() => !(item as { disabled?: boolean }).disabled && setScreen(item.id)}
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
      <button className="buy-credits" type="button"><ShoppingCart size={17} /> MUA TÍN DỤNG</button>
    </aside>
  );
}

function TopBar({ screen }: { screen: Screen }) {
  const titles: Record<Screen, string> = {
    tts: 'Văn bản thành giọng nói',
    conversation: 'Hội thoại',
    voiceChanger: 'Thay đổi giọng nói',
    studio: 'Xưởng âm thanh',
    library: 'Thư viện giọng nói',
    history: 'Lịch sử',
    affiliate: 'Tiếp thị liên kết',
    aiEffects: 'Hiệu ứng AI',
    governance: 'Governance Dashboard'
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
  const [file, setFile] = useState<File | null>(null);
  const [pitch, setPitch] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  async function handleShiftVoice() {
    if (!file) {
      setToast('Hãy chọn file âm thanh trước khi đổi giọng.');
      return;
    }
    setProcessing(true);
    try {
      const job = await api.shiftVoice(file, pitch);
      setToast(`Đã tạo job shift giọng ${job.job_id || job.id}. Trạng thái: ${job.status}`);
      setFile(null);
      setPitch(0);
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể xử lý file âm thanh.');
    } finally {
      setProcessing(false);
    }
  }

  return (
    <section className="workspace voice-change">
      <label className="dropzone">
        <Upload size={34} />
        <strong>Thả file âm thanh vào đây hoặc bấm để chọn</strong>
        <span>MP3, M4A, WAV | Tối đa 50MB</span>
        <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      </label>
      {file && (
        <div className="voice-change-controls">
          <p>Chọn file: <strong>{file.name}</strong></p>
          <div className="pitch-slider">
            <span>Cao độ (semitone)</span>
            <input type="range" min={-12} max={12} step={1} value={pitch} onChange={(e) => setPitch(Number(e.target.value))} />
            <strong>{pitch > 0 ? '+' : ''}{pitch}</strong>
          </div>
          <button className="primary-pill" disabled={processing} onClick={handleShiftVoice} type="button">
            {processing ? <Loader2 className="spin" size={18} /> : <Repeat2 size={18} />} XỬ LÝ GIỌNG NÓI
          </button>
        </div>
      )}
      {!file && <p className="feature-note">Tải lên file âm thanh để bắt đầu biến đổi cao độ hoặc tone giọng.</p>}
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </section>
  );
}

function StudioWorkspace({ projects, selectedProjectId, onCreate, onSelectProject, onSaveScript, onRenderProject, busy }: {
  projects: ProjectOut[];
  selectedProjectId: string | null;
  onCreate: () => void;
  onSelectProject: (projectId: string) => void;
  onSaveScript: (projectId: string, rawText: string) => Promise<void>;
  onRenderProject: (projectId: string) => Promise<void>;
  busy: boolean;
}) {
  const selectedProject = projects.find((project) => project.id === selectedProjectId) || projects[0] || null;
  const [scriptText, setScriptText] = useState('');

  useEffect(() => {
    if (!selectedProject) {
      setScriptText('');
      return;
    }
    setScriptText(`# ${selectedProject.title}\n\nMở đầu:\n- Giới thiệu nội dung\n\nThân bài:\n- Điểm chính 1\n- Điểm chính 2\n\nKết:\n- Lời kêu gọi hành động`);
  }, [selectedProjectId, selectedProject?.title]);

  return (
    <section className="workspace studio-page">
      <div className="studio-head">
        <div><h1>Danh sách dự án</h1><p><span /> {projects.length}/50 dự án</p></div>
        <button className="new-project" onClick={onCreate} type="button"><Plus size={18} /> Dự án mới</button>
      </div>
      {projects.length === 0 ? (
        <div className="empty-state"><FolderOpen size={46} /><h2>Chưa có dự án nào</h2><p>Tạo dự án đầu tiên để bắt đầu tạo audio hàng loạt.</p></div>
      ) : (
        <div className="studio-layout">
          <div className="project-grid selectable">{projects.map((p) => <button key={p.id} className={cx('project-card', selectedProject?.id === p.id && 'selected')} onClick={() => onSelectProject(p.id)} type="button"><h3>{p.title}</h3><p>{p.status}</p><small>{new Date(p.created_at).toLocaleString('vi-VN')}</small></button>)}</div>
          {selectedProject && <article className="project-detail-card"><div className="project-detail-head"><div><span className="project-chip">{selectedProject.status}</span><h2>{selectedProject.title}</h2><p>{selectedProject.description || 'Dự án này chưa có mô tả. Hãy thêm script và chạy render để tạo job narration.'}</p></div><button className="primary-pill" disabled={busy} onClick={() => onRenderProject(selectedProject.id)} type="button">{busy ? <Loader2 className="spin" size={18} /> : <Wand2 size={18} />} RENDER PROJECT</button></div><label className="script-editor"><span>Script / outline</span><textarea value={scriptText} onChange={(event) => setScriptText(event.target.value)} placeholder="Nhập script để lưu vào dự án..." /></label><div className="project-detail-actions"><button className="round-action" disabled={busy || !scriptText.trim()} onClick={() => onSaveScript(selectedProject.id, scriptText)} type="button">Lưu script</button><button className="round-action ghost" onClick={() => onSelectProject(selectedProject.id)} type="button">Đang chọn</button></div></article>}
        </div>
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
      <div className="credits-dot" /><span>{credits.toLocaleString()} Tín dụng còn lại</span>
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
          <button className="voice-select" onClick={onOpenLibrary} type="button"><span className="voice-icon"><User size={22} /></span><span><strong>{selectedVoice?.name || 'Chọn giọng nói'}</strong><small>{provider === 'minimax' ? 'GIỌNG HỆ THỐNG MINIMAX' : 'MẶC ĐỊNH'}</small></span><ChevronDown size={18} /></button>

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

function VoiceLibraryWorkspace({ voices, selectedVoiceId, onSelect, onOpenClone }: { voices: VoiceOut[]; selectedVoiceId?: string; onSelect: (voice: VoiceOut) => void; onOpenClone: () => void }) {
  const [tab, setTab] = useState<'all' | 'cloned'>('all');
  const [query, setQuery] = useState('');
  const filtered = voices.filter((v) => (tab === 'all' ? true : v.source_type === 'cloned')).filter((v) => v.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <section className="workspace library-page"><div className="voice-browser">
      <header className="modal-head library-head"><div className="segmented"><button className={tab === 'all' ? 'active' : ''} onClick={() => setTab('all')}>TẤT CẢ GIỌNG NÓI</button><button className={tab === 'cloned' ? 'active' : ''} onClick={() => setTab('cloned')}>NHÂN BẢN</button></div><div className="modal-search"><Search size={18} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm kiếm giọng nói..." /></div><button className="modal-close" onClick={onOpenClone}><Copy size={22} /></button></header>
      {tab === 'cloned' && filtered.length === 0 ? <div className="empty-voice"><Search size={46} /><p>Không tìm thấy giọng nói nào</p><button className="clone-cta wide" onClick={onOpenClone}><Copy size={20} /> TẠO GIỌNG NHÂN BẢN</button></div> : (
        <div className="modal-body"><aside className="filter-side"><h4><Filter size={15} /> Bộ lọc</h4>{[{ key: 'all', label: 'TẤT CẢ' }, { key: 'all', label: 'HỆ THỐNG' }, { key: 'cloned', label: 'NHÂN BẢN' }].map((item) => <button key={item.label} className={tab === item.key ? 'active' : ''} onClick={() => setTab(item.key as 'all' | 'cloned')}>{item.label}</button>)}</aside><section className="voice-grid">{filtered.map((voice) => <button key={voice.id} className={cx('voice-card', selectedVoiceId === voice.id && 'selected')} onClick={() => onSelect(voice)}><span className="play-box"><Play size={15} /></span><span><strong>{voice.name}</strong><small>{voice.source_type === 'cloned' ? 'NHÂN BẢN' : 'HỆ THỐNG'}</small></span>{selectedVoiceId === voice.id && <Check size={18} />}</button>)}</section></div>
      )}
      <footer className="modal-foot"><span>● {voices.length} TỔNG SỐ GIỌNG NÓI ĐÃ ĐĂNG KÝ</span><span>■ ĐÃ CHỌN &nbsp;&nbsp; ■ CÓ SẴN</span></footer>
    </div></section>
  );
}

function CloneVoiceModal({ onClose, onJobCreated, onUploaded }: { onClose: () => void; onJobCreated: (job: JobStatusOut) => void; onUploaded: (fileName: string) => void }) {
  const [name, setName] = useState('Giọng MiniMax của tôi');
  const [gender, setGender] = useState<'Nam' | 'Nữ'>('Nam');
  const [language, setLanguage] = useState('en');
  const [consent, setConsent] = useState(false);
  const [denoise, setDenoise] = useState(false);
  const [sampleFile, setSampleFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function createClone() {
    if (!consent) { setStatus('Bạn cần xác nhận có quyền sử dụng mẫu giọng nói này.'); return; }
    if (!sampleFile) { setStatus('Hãy chọn một file audio mẫu trước khi nhân bản.'); return; }
    setSubmitting(true);
    try {
      setStatus('Đang tải mẫu giọng lên hệ thống...');
      const upload = await api.uploadCloneSample(sampleFile);
      onUploaded(sampleFile.name);
      setStatus('Đã tải mẫu. Đang tạo job nhân bản...');
      const job = await api.createClone({ name, provider: 'minimax', language_code: language, gender, sample_file_id: upload.file_id, denoise, consent_confirmed: consent });
      onJobCreated(job);
      setStatus(`Đã tạo job nhân bản: ${job.status}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Không thể tạo job nhân bản.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop"><div className="clone-modal">
      <header className="modal-head"><div className="segmented"><button disabled>TẤT CẢ GIỌNG NÓI</button><button className="active">NHÂN BẢN</button></div><div className="modal-search"><Search size={18} /><input placeholder="Tìm kiếm giọng nói..." /></div><button className="modal-close" onClick={onClose}><X size={28} /></button></header>
      <div className="clone-form"><button className="refresh" type="button"><RefreshCw size={18} /></button><h2>Tạo giọng mới</h2><div className="form-line"><input value={name} onChange={(e) => setName(e.target.value)} /><select value={gender} onChange={(e) => setGender(e.target.value as 'Nam' | 'Nữ')}><option>Nam</option><option>Nữ</option></select></div><select value={language} onChange={(e) => setLanguage(e.target.value)}>{languages.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}</select><textarea defaultValue="Xin chào. Đây là bản xem thử giọng MiniMax của tôi." /><div className="sample-row"><span>Mẫu âm thanh</span><div><button type="button">Tải lên</button><button type="button" disabled>Thu âm</button></div></div><label className="upload-zone interactive-upload"><input type="file" accept="audio/*" onChange={(event) => setSampleFile(event.target.files?.[0] || null)} />{sampleFile ? `${sampleFile.name} • ${(sampleFile.size / 1024 / 1024).toFixed(2)} MB` : 'Tải lên một mẫu giọng thực tế (tối đa 20MB)'}</label><div className="check-row"><label><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> Tôi xác nhận có quyền sử dụng mẫu giọng nói này. <b>BẮT BUỘC</b></label><label><input type="checkbox" checked={denoise} onChange={(e) => setDenoise(e.target.checked)} /> Khử tiếng ồn</label></div><button className="clone-submit" disabled={submitting} onClick={createClone} type="button">{submitting ? <Loader2 className="spin" size={24} /> : <Copy size={24} />} BẮT ĐẦU NHÂN BẢN <span>-1,000 TÍN DỤNG</span><ChevronRight /></button>{status && <p className="form-status">{status}</p>}</div>
      <footer className="modal-foot"><span>● 0 TỔNG SỐ GIỌNG NÓI ĐÃ ĐĂNG KÝ</span><span>■ ĐÃ CHỌN &nbsp;&nbsp; ■ CÓ SẴN</span></footer>
    </div></div>
  );
}

function AffiliateWorkspace() {
  const [enrolled, setEnrolled] = useState(false);
  const [affiliateCode, setAffiliateCode] = useState('');
  const [earnings, setEarnings] = useState({ total_earnings_usd: 0, pending_balance_usd: 0 });
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutMethod, setPayoutMethod] = useState('bank_transfer');
  const [payoutDest, setPayoutDest] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    api.affiliateProfile().then((profile) => {
      setEnrolled(true);
      setAffiliateCode(profile.referral_code);
      api.affiliateEarnings().then(setEarnings).catch(() => undefined);
    }).catch(() => setEnrolled(false));
  }, []);

  async function handleEnroll() {
    setLoading(true);
    try {
      const profile = await api.affiliateEnroll();
      setEnrolled(true);
      setAffiliateCode(profile.referral_code);
      setToast('Đã đăng ký chương trình tiếp thị liên kết!');
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể đăng ký.');
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestPayout() {
    if (!payoutAmount || !payoutDest) {
      setToast('Điền đủ số tiền và địa chỉ thanh toán.');
      return;
    }
    setLoading(true);
    try {
      const payout = await api.requestPayout(parseFloat(payoutAmount), payoutMethod, payoutDest);
      setToast(`Đã yêu cầu rút tiền ${payoutAmount} USD. Trạng thái: ${payout.status}`);
      setPayoutAmount('');
      setPayoutDest('');
      api.affiliateEarnings().then(setEarnings).catch(() => undefined);
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Không thể yêu cầu rút tiền.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="workspace affiliate-page">
      {!enrolled ? (
        <div className="affiliate-card">
          <span className="project-chip">Affiliate</span>
          <h1>Tiếp thị liên kết</h1>
          <p>Tham gia chương trình tiếp thị liên kết để kiếm hoa hồng từ mỗi khách hàng mà bạn giới thiệu.</p>
          <button className="primary-pill" disabled={loading} onClick={handleEnroll} type="button">{loading ? <Loader2 className="spin" size={18} /> : <WalletCards size={18} />} Đăng ký ngay</button>
        </div>
      ) : (
        <div className="affiliate-dashboard">
          <div className="affiliate-header">
            <div><h1>Chương trình tiếp thị liên kết</h1><p>Mã giới thiệu: <code>{affiliateCode}</code></p></div>
          </div>
          <div className="affiliate-stats">
            <article><strong>{earnings.total_earnings_usd.toFixed(2)}</strong><span>Tổng hoa hồng (USD)</span></article>
            <article><strong>{earnings.pending_balance_usd.toFixed(2)}</strong><span>Sẵn sàng rút (USD)</span></article>
          </div>
          <article className="payout-form">
            <h2>Yêu cầu rút tiền</h2>
            <div className="payout-inputs">
              <input type="number" placeholder="Số tiền (USD)" value={payoutAmount} onChange={(e) => setPayoutAmount(e.target.value)} step="0.01" />
              <select value={payoutMethod} onChange={(e) => setPayoutMethod(e.target.value)}>
                <option value="bank_transfer">Chuyển khoản ngân hàng</option>
                <option value="paypal">PayPal</option>
                <option value="crypto_usdc">USDC (Crypto)</option>
              </select>
              <input type="text" placeholder="Địa chỉ PayPal / Tài khoản ngân hàng" value={payoutDest} onChange={(e) => setPayoutDest(e.target.value)} />
            </div>
            <button className="primary-pill" disabled={loading || earnings.pending_balance_usd <= 0} onClick={handleRequestPayout} type="button">{loading ? <Loader2 className="spin" size={18} /> : <ShoppingCart size={18} />} Yêu cầu rút tiền</button>
          </article>
        </div>
      )}
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </section>
  );
}

function AiEffectsWorkspace() {
  type Effect = { id: string; name: string; effect_type: string; description: string; default_params: Record<string, number> };
  const [effects, setEffects] = useState<Effect[]>([]);
  const [selected, setSelected] = useState<Effect | null>(null);
  const [params, setParams] = useState<Record<string, number>>({});
  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<JobStatusOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.aiEffects().then(setEffects).catch(() => {});
  }, []);

  function selectEffect(e: Effect) {
    setSelected(e);
    setParams({ ...e.default_params });
    setJob(null);
    setErr(null);
  }

  async function applyEffect() {
    if (!file || !selected) return;
    setBusy(true);
    setErr(null);
    try {
      const j = await api.applyEffect(file, selected.effect_type, params);
      setJob(j);
    } catch (error: unknown) {
      setErr(String(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="workspace">
      <h1>Hiệu ứng AI</h1>
      <p style={{ color: 'var(--muted)', marginBottom: '1.5rem' }}>Áp dụng hiệu ứng âm thanh lên file audio của bạn.</p>
      <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '0 0 240px' }}>
          <h3 style={{ marginBottom: '.75rem' }}>Chọn hiệu ứng</h3>
          {effects.length === 0 && <p style={{ color: 'var(--muted)' }}>Đang tải...</p>}
          {effects.map((e) => (
            <button
              key={e.id}
              onClick={() => selectEffect(e)}
              style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '.6rem .9rem',
                marginBottom: '.4rem', borderRadius: '8px', border: '1.5px solid',
                borderColor: selected?.id === e.id ? 'var(--accent)' : 'var(--border)',
                background: selected?.id === e.id ? 'var(--accent-soft, rgba(99,102,241,.1))' : 'transparent',
                cursor: 'pointer', color: 'var(--fg)'
              }}
              type="button"
            >
              <strong>{e.name}</strong><br />
              <small style={{ color: 'var(--muted)' }}>{e.description}</small>
            </button>
          ))}
        </div>
        <div style={{ flex: '1 1 320px' }}>
          {!selected && <p style={{ color: 'var(--muted)', marginTop: '3rem' }}>Chọn một hiệu ứng để bắt đầu.</p>}
          {selected && (
            <>
              <h3 style={{ marginBottom: '.75rem' }}>Tham số: {selected.name}</h3>
              {Object.entries(params).map(([k, v]) => (
                <label key={k} style={{ display: 'block', marginBottom: '.75rem' }}>
                  <span style={{ fontSize: '.85rem', color: 'var(--muted)' }}>{k}: <strong>{v}</strong></span>
                  <input
                    type="range"
                    min={-30}
                    max={3000}
                    step={0.01}
                    value={v}
                    onChange={(ev) => setParams((p) => ({ ...p, [k]: parseFloat(ev.target.value) }))}
                    style={{ display: 'block', width: '100%', marginTop: '.25rem' }}
                  />
                </label>
              ))}
              <label className="upload-zone interactive-upload" style={{ marginTop: '1rem' }}>
                <input type="file" accept="audio/*" onChange={(ev) => setFile(ev.target.files?.[0] || null)} />
                {file ? `${file.name} • ${(file.size / 1024).toFixed(1)} KB` : 'Tải lên file audio'}
              </label>
              <button className="primary-pill" disabled={busy || !file} onClick={applyEffect} style={{ marginTop: '1rem' }} type="button">
                {busy ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />} Áp dụng hiệu ứng
              </button>
              {err && <p style={{ color: 'var(--danger, #ef4444)', marginTop: '.5rem' }}>{err}</p>}
              {job && <p style={{ marginTop: '.75rem' }}>Job đã tạo: <strong>{job.id}</strong> ({job.status})</p>}
            </>
          )}
        </div>
      </div>
    </section>
  );
}

function GovernanceWorkspace() {
  const [providerHealth, setProviderHealth] = useState<Record<string, { status: string; detail: string }> | null>(null);
  const [baselines, setBaselines] = useState<Array<{ baseline_id: string; baseline_type: string; lifecycle_state: string; created_at: string }>>([]);
  const [decisions, setDecisions] = useState<Array<{ decision_id: string; title: string; outcome: string; created_at: string }>>([]);
  const [remediations, setRemediations] = useState<Array<{ remediation_id: string; title: string; status: string; created_at: string }>>([]);

  useEffect(() => {
    api.providerHealth().then((x) => setProviderHealth(x.providers)).catch(() => setProviderHealth(null));
    api.governanceBaselines().then(setBaselines).catch(() => setBaselines([]));
    api.governanceDecisions().then(setDecisions).catch(() => setDecisions([]));
    api.governanceRemediations().then(setRemediations).catch(() => setRemediations([]));
  }, []);

  return (
    <section className="workspace history-page">
      <h1>Governance Dashboard</h1>
      <div className="history-list">
        <article className="history-card">
          <span>Provider Health</span>
          <small>
            {providerHealth ? Object.entries(providerHealth).map(([k, v]) => `${k}: ${v.status}`).join(' | ') : 'Chưa có dữ liệu'}
          </small>
        </article>
        <article className="history-card"><span>Baselines</span><strong>{baselines.length}</strong><small>{baselines[0]?.baseline_type || 'N/A'}</small></article>
        <article className="history-card"><span>Decisions</span><strong>{decisions.length}</strong><small>{decisions[0]?.outcome || 'N/A'}</small></article>
        <article className="history-card"><span>Remediations</span><strong>{remediations.length}</strong><small>{remediations[0]?.status || 'N/A'}</small></article>
      </div>
    </section>
  );
}

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  return <div className="toast"><span>{message}</span><button onClick={onClose}><X size={16} /></button></div>;
}
