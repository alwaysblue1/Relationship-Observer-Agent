import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Slogan } from '../components/dashboard/Slogan';
import { ObserverReport } from '../components/observer/ObserverReport';
import { LabelCard } from '../components/personality/LabelCard';
import { AbstractPortrait } from '../components/personality/AbstractPortrait';
import { ScoreCard } from '../components/scoring/ScoreCard';
import { SuggestionCard } from '../components/suggestions/SuggestionCard';
import { MusicCard } from '../components/spotify/MusicCard';
import { TrendChart } from '../components/dashboard/TrendChart';
import { api, SessionDetail } from '../lib/api';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showScoring, setShowScoring] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showMusic, setShowMusic] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.sessions.get(id)
      .then(setSession)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-violet-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <p className="text-slate-400 mb-4">无法加载分析报告</p>
        <p className="text-sm text-slate-600">{error || 'Session not found'}</p>
      </div>
    );
  }

  const analysis = session.analysis;
  const metrics = analysis?.raw_metrics || {};
  const weeklyData = (metrics as Record<string, unknown>).weekly_trend as { week_start: string; message_count: number }[] || [];

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <Slogan />

      {!analysis ? (
        <div className="glass-card p-12 text-center">
          <p className="text-slate-400 mb-2">分析尚未完成</p>
          <p className="text-sm text-slate-600">请等待后刷新页面</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Observer Report — Core Section */}
          <ObserverReport
            trend={analysis.relationship_trend}
            communication={analysis.communication_change}
            rhythm={analysis.emotional_rhythm}
            summary={analysis.observer_summary}
          />

          {/* Trend Chart */}
          {weeklyData.length > 0 && <TrendChart data={weeklyData} />}

          {/* Personality Label — always visible */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <LabelCard
              label={analysis.personality_label}
              description={analysis.personality_description}
              traits={analysis.personality_traits}
            />
            <AbstractPortrait svg={analysis.personality_portrait_svg} />
          </div>

          {/* Scoring — hidden by default */}
          <div className="glass-card p-6">
            <button
              onClick={() => setShowScoring(!showScoring)}
              className="w-full flex items-center justify-between text-left"
            >
              <div>
                <h3 className="text-sm font-medium text-slate-400">量化分析</h3>
                <p className="text-xs text-slate-600 mt-1">查看关系健康度评分</p>
              </div>
              <svg
                className={`w-5 h-5 text-slate-500 transition-transform ${showScoring ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            {showScoring && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-6"
              >
                <ScoreCard
                  score={analysis.health_score}
                  trend={analysis.score_trend}
                  trendValue={analysis.score_trend_value}
                  reasons={analysis.score_reasons}
                />
              </motion.div>
            )}
          </div>

          {/* AI Suggestions — hidden by default */}
          <div className="glass-card p-6">
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="w-full flex items-center justify-between text-left"
            >
              <div>
                <h3 className="text-sm font-medium text-slate-400">获取建议</h3>
                <p className="text-xs text-slate-600 mt-1">温和的观察与思考</p>
              </div>
              <svg
                className={`w-5 h-5 text-slate-500 transition-transform ${showSuggestions ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            {showSuggestions && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-6"
              >
                <SuggestionCard suggestions={analysis.suggestions} />
              </motion.div>
            )}
          </div>

          {/* Spotify */}
          <div className="glass-card p-6">
            <button
              onClick={() => setShowMusic(!showMusic)}
              className="w-full flex items-center justify-between text-left"
            >
              <div>
                <h3 className="text-sm font-medium text-slate-400">Spotify 音乐推荐</h3>
                <p className="text-xs text-slate-600 mt-1">基于你的关系节律</p>
              </div>
              <svg
                className={`w-5 h-5 text-slate-500 transition-transform ${showMusic ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            {showMusic && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-6"
              >
                <MusicCard sessionId={id!} analysis={analysis} />
              </motion.div>
            )}
          </div>

          {/* Metrics Summary */}
          <div className="glass-card p-6">
            <h3 className="text-sm font-medium text-slate-400 mb-4">数据摘要</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-slate-600">总消息数</p>
                <p className="text-lg font-light text-slate-300">{(metrics as Record<string, unknown>).total_messages as number || 0}</p>
              </div>
              <div>
                <p className="text-xs text-slate-600">日均消息</p>
                <p className="text-lg font-light text-slate-300">{(metrics as Record<string, unknown>).messages_per_day as number || 0}</p>
              </div>
              <div>
                <p className="text-xs text-slate-600">平均回复 (分)</p>
                <p className="text-lg font-light text-slate-300">{(metrics as Record<string, unknown>).avg_response_minutes as number || 0}</p>
              </div>
              <div>
                <p className="text-xs text-slate-600">深夜互动比</p>
                <p className="text-lg font-light text-slate-300">{((metrics as Record<string, unknown>).night_interaction_ratio as number || 0) * 100}%</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
