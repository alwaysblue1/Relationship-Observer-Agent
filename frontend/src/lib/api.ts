const BASE_URL = '/api';

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface SessionListItem {
  id: string;
  title: string;
  platform: string;
  total_messages: number;
  date_range_start: string | null;
  date_range_end: string | null;
  created_at: string;
}

export interface SessionDetail extends SessionListItem {
  analysis: AnalysisResult | null;
}

export interface AnalysisResult {
  id: string;
  relationship_trend: string;
  communication_change: string;
  emotional_rhythm: string;
  observer_summary: string;
  health_score: number;
  score_trend: string;
  score_trend_value: number;
  score_reasons: string[];
  personality_label: string;
  personality_description: string;
  personality_traits: string[];
  personality_portrait_svg: string;
  suggestions: string[];
  spotify_mood_keywords: string;
  spotify_playlist_name: string;
  spotify_recommendation: Record<string, unknown>;
  raw_metrics: Record<string, unknown>;
  created_at: string;
}

export interface UploadResult {
  session_id: string;
  title: string;
  platform: string;
  total_messages: number;
  date_range_start: string | null;
  date_range_end: string | null;
  participants: { anon_id: string; is_self: boolean }[];
  event_summary: {
    total_events: number;
    event_types: string[];
    total_score: number;
  };
  analysis_id: string;
}

export interface SpotifyRecommendation {
  playlist_name: string;
  mood_keywords: string[];
  recommendation_reason: string;
  tracks: { name: string; artist: string; uri: string }[];
  spotify_open_url: string;
}

export const api = {
  upload: {
    chat: async (file: File, platform: string, selfName: string): Promise<UploadResult> => {
      const form = new FormData();
      form.append('file', file);
      form.append('platform', platform);
      form.append('self_name', selfName);
      const res = await fetch(`${BASE_URL}/upload/chat`, {
        method: 'POST',
        body: form,
        headers: { ...getAuthHeaders() },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Upload failed');
      }
      return res.json();
    },
  },

  sessions: {
    list: () => fetchJSON<SessionListItem[]>('/analysis/sessions'),
    get: (id: string) => fetchJSON<SessionDetail>(`/analysis/sessions/${id}`),
    delete: (id: string) => fetchJSON<{ ok: boolean }>(`/analysis/sessions/${id}`, { method: 'DELETE' }),
  },

  analysis: {
    report: (id: string) => fetchJSON<Record<string, unknown>>(`/analysis/report/${id}`),
    scoring: (id: string) => fetchJSON<Record<string, unknown>>(`/analysis/scoring/${id}`),
    personality: (id: string) => fetchJSON<Record<string, unknown>>(`/analysis/personality/${id}`),
    suggestions: (id: string) => fetchJSON<Record<string, unknown>>(`/analysis/suggestions/${id}`),
    metrics: (id: string) => fetchJSON<Record<string, unknown>>(`/analysis/metrics/${id}`),
  },

  integrations: {
    spotify: (id: string) => fetchJSON<SpotifyRecommendation>(`/integrations/spotify/${id}`),
    createPlaylist: (id: string) => fetchJSON<Record<string, unknown>>(`/integrations/spotify/create-playlist/${id}`, { method: 'POST' }),
  },

  auth: {
    me: () => fetchJSON<{ id: string; username: string }>('/auth/me'),
    login: (username: string, password: string) =>
      fetchJSON<{ user: { id: string; username: string }; token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    register: (username: string, password: string) =>
      fetchJSON<{ user: { id: string; username: string }; token: string }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
  },
};
