'use client';

import { motion } from 'framer-motion';

interface Props {
  progress: number;
  statusText: string;
}

export function ParseProgress({ progress, statusText }: Props) {
  return (
    <div className="py-8">
      <div className="flex items-center justify-center mb-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 rounded-full border-2 border-slate-600 border-t-accent-lavender"
        />
      </div>

      <div className="w-full bg-slate-800 rounded-full h-1.5 mb-4 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-accent-lavender to-accent-rose"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(progress, 100)}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <p className="text-center text-sm text-slate-400">{statusText}</p>
      <p className="text-center text-xs text-slate-600 mt-1">{Math.round(progress)}%</p>
    </div>
  );
}
