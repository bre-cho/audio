import type { BillingBalanceOut, JobStatusOut, ProjectOut, ProviderOut, VoiceOut } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
    headers: isFormData ? init?.headers : { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init
  });

  if (!res.ok) {
    const message = await res.text().catch(() => res.statusText);
    throw new Error(message || `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  jobsStreamUrl: () => `${API_BASE}/jobs/stream`,
  providers: () => request<ProviderOut[]>('/providers'),
  libraryVoices: (params?: { source_type?: string; language_code?: string; gender?: string; quality_tier?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.source_type) qs.set('source_type', params.source_type);
    if (params?.language_code) qs.set('language_code', params.language_code);
    if (params?.gender) qs.set('gender', params.gender);
    if (params?.quality_tier) qs.set('quality_tier', params.quality_tier);
    if (params?.limit != null) qs.set('limit', String(params.limit));
    return request<VoiceOut[]>(`/library/voices${qs.toString() ? `?${qs.toString()}` : ''}`);
  },
  voices: (params?: { provider?: string; source_type?: string; language_code?: string }) => {
    const qs = new URLSearchParams();
    if (params?.source_type) qs.set('source_type', params.source_type);
    if (params?.language_code) qs.set('language_code', params.language_code);
    return request<VoiceOut[]>(`/voices${qs.toString() ? `?${qs.toString()}` : ''}`);
  },
  balance: () => request<BillingBalanceOut>('/billing/balance'),
  jobs: () => request<JobStatusOut[]>('/jobs'),
  projects: () => request<ProjectOut[]>('/projects'),
  project: (projectId: string) => request<ProjectOut>(`/projects/${projectId}`),
  createProject: (title: string) => request<ProjectOut>('/projects', {
    method: 'POST',
    body: JSON.stringify({ title, project_type: 'audio', status: 'draft', settings_json: {} })
  }),
  addProjectScript: (projectId: string, payload: Record<string, unknown>) => request<{ script_asset_id: string }>(`/projects/${projectId}/scripts`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  batchGenerateProject: (projectId: string) => request<JobStatusOut>(`/projects/${projectId}/batch-generate`, {
    method: 'POST'
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
  uploadCloneSample: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<{ file_id: string; upload_url?: string | null }>('/voice-clone/upload', { method: 'POST', body: formData });
  },
  createClone: (payload: Record<string, unknown>) => request<JobStatusOut>('/voice-clone/create', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  clonePreview: (voiceId: string, text: string) => request<JobStatusOut>(`/voice-clone/${voiceId}/preview`, {
    method: 'POST',
    body: JSON.stringify({ text })
  }),
  shiftVoice: (file: File, pitchSemitones: number = 0) => {
    const formData = new FormData();
    formData.append('file', file);
    const param = new URLSearchParams();
    param.set('pitch_semitones', String(pitchSemitones));
    return request<JobStatusOut>(`/voice-clone/shift?${param.toString()}`, { method: 'POST', body: formData });
  },
  affiliateEnroll: () => request<{ id: string; user_id: string; referral_code: string; name: string }>('/affiliate/enroll', { method: 'POST' }),
  affiliateProfile: () => request<{ id: string; user_id: string; referral_code: string; name: string }>('/affiliate/me'),
  affiliateEarnings: () => request<{ total_earnings_usd: number; pending_balance_usd: number }>('/affiliate/earnings'),
  affiliatePayouts: () => request<Array<{ id: string; amount_cents: number; status: string; payout_method: string }>>('/affiliate/payouts'),
  requestPayout: (amountUsd: number, method: string, destination: string) => request<{ id: string; status: string }>('/affiliate/payout', {
    method: 'POST',
    body: JSON.stringify({ amount_cents: Math.round(amountUsd * 100), payout_method: method, payout_destination: destination })
  })
};
