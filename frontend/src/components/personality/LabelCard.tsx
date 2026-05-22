'use client';

import { motion } from 'framer-motion';

interface Props {
  label: string;
  description: string;
  traits: string[];
}

export function LabelCard({ label, description, traits }: Props) {
  if (!label) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-card p-6 flex flex-col justify-between"
    >
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-4">人格标签</p>
        <h2 className="text-3xl font-bold text-gradient-warm mb-3">{label}</h2>
        <p className="text-sm text-slate-400 leading-relaxed">{description}</p>
      </div>

      {traits && traits.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-6">
          {traits.map((trait, i) => (
            <span
              key={i}
              className="px-3 py-1 rounded-full text-xs border border-slate-700 text-slate-400"
            >
              {trait}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
