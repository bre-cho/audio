export type ProviderCode = 'elevenlabs' | 'minimax' | 'internal_genvoice';
export type Screen = 'tts' | 'conversation' | 'voiceChanger' | 'studio' | 'library' | 'history' | 'affiliate' | 'aiEffects';

export interface ProviderOut {
  code: ProviderCode | string;
  name: string;
  status: string;
}

export interface VoiceOut {
  id: string;
  name: string;
  source_type: 'system' | 'cloned' | string;
  language_code?: string | null;
  gender?: string | null;
  preview_url?: string | null;
  is_active: boolean;
  created_at?: string;
}

export interface JobStatusOut {
  id: string;
  job_id?: string;
  job_type: string;
  status: 'queued' | 'processing' | 'retrying' | 'succeeded' | 'failed';
  error_code?: string | null;
  error_message?: string | null;
  runtime_json?: Record<string, unknown>;
  preview_url?: string | null;
  output_url?: string | null;
  voice_profile_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectOut {
  id: string;
  title: string;
  description?: string | null;
  project_type: string;
  status: string;
  settings_json: Record<string, unknown>;
  created_at: string;
}

export interface BillingBalanceOut {
  balance_credits: number;
}

export interface SettingsState {
  provider: ProviderCode;
  model: string;
  voiceId?: string;
  speed: number;
  stability: number;
  similarity: number;
  style: number;
  speakerBoost: boolean;
  language: string;
  gender: 'Nam' | 'Nữ';
}
