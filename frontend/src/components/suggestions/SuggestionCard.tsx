'use client';

interface Props {
  suggestions: string[];
}

export function SuggestionCard({ suggestions }: Props) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">温和的观察与思考</p>
      {suggestions.map((suggestion, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/40"
        >
          <span className="w-6 h-6 rounded-full bg-accent-lavender/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-3 h-3 text-accent-lavender" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0" />
            </svg>
          </span>
          <p className="text-sm text-slate-300 leading-relaxed">{suggestion}</p>
        </div>
      ))}
      <p className="text-xs text-slate-600 mt-4">
        以上仅为温和的观察与思考，请根据自身情况判断。
      </p>
    </div>
  );
}
