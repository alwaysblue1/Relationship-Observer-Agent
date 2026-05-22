'use client';

interface Props {
  score: number | null;
  trend: string;
  trendValue: number;
  reasons: string[];
}

export function ScoreCard({ score, trend, trendValue, reasons }: Props) {
  if (score === null || score === undefined) return null;

  const scoreColor = score >= 70 ? 'text-accent-mint' : score >= 40 ? 'text-accent-warm' : 'text-accent-rose';
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';
  const trendColor = trend === 'up' ? 'text-accent-mint' : trend === 'down' ? 'text-accent-rose' : 'text-slate-400';

  return (
    <div>
      <div className="flex items-end gap-4 mb-6">
        <div>
          <p className="text-xs text-slate-500 mb-1">关系健康度</p>
          <p className={`text-5xl font-light ${scoreColor}`}>{score}</p>
        </div>
        <div className="pb-1">
          <p className={`text-lg ${trendColor}`}>
            {trendIcon} {trendValue}%
          </p>
          <p className="text-xs text-slate-500">趋势</p>
        </div>
      </div>

      {reasons && reasons.length > 0 && (
        <div className="space-y-2 mb-4">
          <p className="text-xs text-slate-500 mb-2">原因</p>
          {reasons.map((reason, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="text-xs text-slate-600 mt-0.5">{i + 1}.</span>
              <p className="text-sm text-slate-400">{reason}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-600 leading-relaxed">
          评分仅代表沟通模式趋势，不代表真实情感。
        </p>
      </div>
    </div>
  );
}
