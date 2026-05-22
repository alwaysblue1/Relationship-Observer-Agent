import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Slogan } from '../components/dashboard/Slogan';
import { FileUploader } from '../components/upload/FileUploader';
import { ParseProgress } from '../components/upload/ParseProgress';
import { api, UploadResult } from '../lib/api';

export default function UploadPage() {
  const navigate = useNavigate();
  const [selfName, setSelfName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setStatusText('正在解析文件...');

    const progressInterval = setInterval(() => {
      setProgress((p) => {
        if (p >= 90) return p;
        const next = p + Math.random() * 10;
        if (next > 50 && p <= 50) setStatusText('正在脱敏处理...');
        if (next > 70 && p <= 70) setStatusText('正在分析关系事件...');
        if (next > 85 && p <= 85) setStatusText('正在生成 Observer 报告...');
        return next;
      });
    }, 600);

    try {
      const res = await api.upload.chat(file, 'auto', selfName);
      setProgress(100);
      setStatusText('分析完成');
      setResult(res);
      clearInterval(progressInterval);
    } catch (e: unknown) {
      clearInterval(progressInterval);
      setError(e instanceof Error ? e.message : 'Upload failed');
      setStatusText('');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <Slogan />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="glass-card p-8">
          <h2 className="text-lg font-medium text-slate-300 mb-6">上传聊天记录</h2>

          {!uploading && !result && (
            <>
              <div className="mb-6">
                <label className="block text-sm text-slate-400 mb-2">你在聊天中的昵称</label>
                <input
                  type="text"
                  value={selfName}
                  onChange={(e) => setSelfName(e.target.value)}
                  placeholder="输入你的QQ昵称，用于区分你和聊天对象"
                  className="w-full px-4 py-3 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-violet-500 transition-colors"
                />
              </div>
              <FileUploader onUpload={handleUpload} disabled={uploading || !selfName.trim()} />
            </>
          )}

          {uploading && (
            <ParseProgress progress={progress} statusText={statusText} />
          )}

          {error && (
            <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-400">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-3 text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                重试
              </button>
            </div>
          )}

          {result && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200">分析完成</p>
                  <p className="text-xs text-slate-500">{result.total_messages} 条消息 · {result.event_summary.total_events} 个关系事件</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-slate-800/50 rounded-xl p-4">
                  <p className="text-xs text-slate-500 mb-1">关系事件总分</p>
                  <p className={`text-2xl font-light ${result.event_summary.total_score >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                    {result.event_summary.total_score > 0 ? '+' : ''}{result.event_summary.total_score}
                  </p>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-4">
                  <p className="text-xs text-slate-500 mb-1">事件类型</p>
                  <p className="text-2xl font-light text-slate-200">{result.event_summary.event_types.length}</p>
                </div>
              </div>

              <button
                onClick={() => navigate(`/report/${result.session_id}`)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-500 to-rose-500 text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                查看 Observer 报告
              </button>
            </motion.div>
          )}
        </div>

        <div className="mt-8 glass-card p-6">
          <h3 className="text-sm font-medium text-slate-400 mb-4">如何获取 QQ 聊天记录</h3>
          <p className="text-sm text-slate-500 leading-relaxed">
            在你想开始的对话气泡处按住鼠标左键，拖动到你想结束的对话处，随后点击右键选择复制，再粘贴到文本文档，最后上传这个文档吧
          </p>
        </div>
      </motion.div>
    </div>
  );
}
