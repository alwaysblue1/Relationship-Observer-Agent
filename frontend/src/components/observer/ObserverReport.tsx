'use client';

import { motion } from 'framer-motion';

interface Props {
  trend: string;
  communication: string;
  rhythm: string;
  summary: string;
}

export function ObserverReport({ trend, communication, rhythm, summary }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="glass-card p-8"
    >
      <div className="flex items-center gap-3 mb-8">
        <div className="w-2 h-2 rounded-full bg-accent-lavender animate-pulse-soft" />
        <h2 className="text-sm font-medium text-slate-400 tracking-wider uppercase">Relationship Reflection</h2>
      </div>

      <div className="space-y-8">
        <Section title="关系趋势" content={trend} />
        <Section title="沟通变化" content={communication} />
        <Section title="情绪节律" content={rhythm} />
        <Section title="观察总结" content={summary} isLast />
      </div>
    </motion.div>
  );
}

function Section({ title, content, isLast }: { title: string; content: string; isLast?: boolean }) {
  if (!content) return null;

  return (
    <div className={`${!isLast ? 'border-b border-slate-800 pb-6' : ''}`}>
      <h3 className="text-xs text-slate-500 uppercase tracking-wider mb-3">{title}</h3>
      <p className="text-sm text-slate-300 leading-relaxed">{content}</p>
    </div>
  );
}
