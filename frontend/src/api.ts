import type { BillingBalanceOut, JobStatusOut, ProjectOut, ProviderOut, VoiceOut } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init
  });

  if (!res.ok) {
    const message = await res.text().catch(() => res.statusText);
    throw new Error(message || `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  providers: () => request<ProviderOut[]>('/providers'),
  voices: (params?: { provider?: string; source_type?: string; language_code?: string }) => {
    const qs = new URLSearchParams();
    if (params?.source_type) qs.set('source_type', params.source_type);
    if (params?.language_code) qs.set('language_code', params.language_code);
    return request<VoiceOut[]>(`/voices${qs.toString() ? `?${qs.toString()}` : ''}`);
  },
  balance: () => request<BillingBalanceOut>('/billing/balance'),
  jobs: () => request<JobStatusOut[]>('/jobs'),
  projects: () => request<ProjectOut[]>('/projects'),
  createProject: (title: string) => request<ProjectOut>('/projects', {
    method: 'POST',
    body: JSON.stringify({ title, project_type: 'audio', status: 'draft', settings_json: {} })
  }),
  ttsGenerate: (payload: Record<string, unknown>) => request<JobStatusOut>('/tts/generate', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  ttsPreview: (payload: Record<string, unknown>) => request<JobStatusOut>('/tts/preview', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  parseConversation: (raw_script: string) => request<{ lines: { speaker: string; text: string }[] }>('/conversation/parse', {
    method: 'POST',
    body: JSON.stringify({ raw_script })
  }),
  generateConversation: (payload: Record<string, unknown>) => request<JobStatusOut>('/conversation/generate', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  uploadCloneSample: () => request<{ file_id: string; upload_url?: string | null }>('/voice-clone/upload', { method: 'POST' }),
  createClone: (payload: Record<string, unknown>) => request<JobStatusOut>('/voice-clone/create', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  clonePreview: (voiceId: string, text: string) => request<JobStatusOut>(`/voice-clone/${voiceId}/preview`, {
    method: 'POST',
    body: JSON.stringify({ text })
  })
};
