'use client';

import { motion } from 'framer-motion';

export function Slogan() {
  return (
    <div className="text-center py-16 mb-8">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: 'easeOut' }}
      >
        <p className="text-sm text-slate-500 tracking-widest uppercase mb-6">
          Relationship Observer
        </p>
        <h1 className="text-4xl md:text-5xl font-light text-slate-200 leading-relaxed tracking-wide mb-4">
          看见那些，
          <br />
          你们都没说出口的
          <span className="text-gradient-warm font-normal">变化</span>
        </h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="text-slate-500 text-sm mt-8 max-w-md mx-auto leading-relaxed"
        >
          一个不会替你定义关系，只帮助你看见变化的 AI Observer
        </motion.p>
      </motion.div>
    </div>
  );
}
