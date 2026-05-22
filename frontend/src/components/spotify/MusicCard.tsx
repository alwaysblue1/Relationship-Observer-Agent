'use client';

import { useEffect, useState } from 'react';
import { api, SpotifyRecommendation, AnalysisResult } from '@/lib/api';

interface Props {
  sessionId: string;
  analysis: AnalysisResult;
}

export function MusicCard({ sessionId, analysis }: Props) {
  const [data, setData] = useState<SpotifyRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.integrations.spotify(sessionId)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleCreatePlaylist = async () => {
    setCreating(true);
    try {
      await api.integrations.createPlaylist(sessionId);
    } catch {
      // silent
    }
    setCreating(false);
  };

  const rec = analysis.spotify_recommendation || {};
  const playlistName = analysis.spotify_playlist_name || (rec as Record<string, unknown>).playlist_name as string || 'Observer Mix';
  const reason = (rec as Record<string, unknown>).recommendation_reason as string || '';
  const keywords = analysis.spotify_mood_keywords || '';

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="w-6 h-6 border-2 border-slate-600 border-t-accent-mint rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-accent-mint/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-accent-mint" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
          </svg>
        </div>
        <div>
          <p className="text-sm font-medium text-slate-300">{playlistName}</p>
          {keywords && <p className="text-xs text-slate-500">{keywords}</p>}
        </div>
      </div>

      {reason && (
        <p className="text-sm text-slate-400 leading-relaxed italic border-l-2 border-slate-700 pl-4">
          {reason}
        </p>
      )}

      {data?.tracks && data.tracks.length > 0 && (
        <div className="space-y-2">
          {data.tracks.slice(0, 5).map((track, i) => (
            <div key={i} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-slate-800/30">
              <span className="text-xs text-slate-600 w-4">{i + 1}</span>
              <div>
                <p className="text-sm text-slate-300">{track.name}</p>
                <p className="text-xs text-slate-500">{track.artist}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-3">
        <a
          href={data?.spotify_open_url || 'https://open.spotify.com'}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 py-2.5 rounded-xl bg-accent-mint/10 border border-accent-mint/20 text-accent-mint text-sm font-medium text-center hover:bg-accent-mint/20 transition-colors"
        >
          打开 Spotify
        </a>
        <button
          onClick={handleCreatePlaylist}
          disabled={creating}
          className="flex-1 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 text-sm font-medium hover:border-slate-600 transition-colors disabled:opacity-50"
        >
          {creating ? '生成中...' : '生成歌单'}
        </button>
      </div>
    </div>
  );
}
