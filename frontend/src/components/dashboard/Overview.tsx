'use client';

import { motion } from 'framer-motion';
import { SessionListItem } from '@/lib/api';

interface Props {
  sessions: SessionListItem[];
}

export function Overview({ sessions }: Props) {
  const totalMessages = sessions.reduce((sum, s) => sum + s.total_messages, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
    >
      <div className="glass-card p-6">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">分析次数</p>
        <p className="text-3xl font-light text-slate-200">{sessions.length}</p>
      </div>
      <div className="glass-card p-6">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">消息总数</p>
        <p className="text-3xl font-light text-slate-200">{totalMessages.toLocaleString()}</p>
      </div>
    </motion.div>
  );
}
