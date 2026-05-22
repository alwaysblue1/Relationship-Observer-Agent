'use client';

import { motion } from 'framer-motion';

interface Props {
  svg: string;
}

export function AbstractPortrait({ svg }: Props) {
  if (!svg) return null;

  const isUrl = svg.startsWith('http');

  const handleDownload = async () => {
    try {
      if (isUrl) {
        const a = document.createElement('a');
        a.href = svg;
        a.download = 'relationship-observer-portrait.png';
        a.target = '_blank';
        a.click();
      } else {
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'relationship-observer-portrait.svg';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      // Fallback silently
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="glass-card p-6 flex flex-col items-center justify-center gap-4"
    >
      <div className="w-48 h-48 flex items-center justify-center overflow-hidden rounded-xl">
        {isUrl ? (
          <img src={svg} alt="人格画像" className="w-full h-full object-cover" />
        ) : (
          <div dangerouslySetInnerHTML={{ __html: svg }} />
        )}
      </div>
      <button
        onClick={handleDownload}
        className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1.5"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        导出图片
      </button>
    </motion.div>
  );
}
