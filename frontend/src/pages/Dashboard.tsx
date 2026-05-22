import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Slogan } from '../components/dashboard/Slogan';
import { Overview } from '../components/dashboard/Overview';
import { api, SessionListItem } from '../lib/api';

export default function DashboardPage() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = () => {
    api.sessions.list()
      .then(setSessions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.sessions.delete(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      // silent
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <Slogan />

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-violet-500 rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="glass-card p-8 text-center mt-12">
          <p className="text-slate-400 mb-4">无法连接后端服务</p>
          <p className="text-sm text-slate-600">请确保后端服务运行在 localhost:8000</p>
        </div>
      )}

      {!loading && !error && sessions.length === 0 && (
        <div className="text-center py-20 animate-fade-in">
          <div className="glass-card p-12 max-w-lg mx-auto">
            <Link to="/upload" className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-6 hover:bg-slate-700 transition-colors cursor-pointer">
              <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </Link>
            <h2 className="text-xl font-medium text-slate-300 mb-3">开始观察一段关系</h2>
            <p className="text-slate-500 mb-8 leading-relaxed">
              上传你的微信或QQ聊天记录导出文件，Observer 会帮你看见那些没说出口的变化。
            </p>
            <Link
              to="/upload"
              className="inline-block px-8 py-3 rounded-full bg-gradient-to-r from-violet-500 to-rose-500 text-white text-sm font-medium hover:opacity-90 transition-opacity"
            >
              开始分析
            </Link>
          </div>
        </div>
      )}

      {!loading && !error && sessions.length > 0 && (
        <>
          <Overview sessions={sessions} />

          <div className="mt-12">
            <h2 className="text-lg font-medium text-slate-300 mb-6">分析历史</h2>
            <div className="grid gap-4">
              {sessions.map((session, i) => (
                <div
                  key={session.id}
                  className="glass-card p-6 flex items-center justify-between hover:border-slate-500 transition-all animate-slide-up"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <Link to={`/report/${session.id}`} className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-sm text-slate-400 shrink-0">
                      QQ
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-slate-200">{session.title}</h3>
                      <p className="text-xs text-slate-500 mt-1">
                        {session.total_messages} 条消息
                        {session.date_range_start && ` · ${session.date_range_start.split('T')[0]}`}
                      </p>
                    </div>
                  </Link>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-slate-500">
                      {new Date(session.created_at).toLocaleDateString('zh-CN')}
                    </span>
                    <button
                      onClick={() => handleDelete(session.id)}
                      className="p-1.5 rounded-lg text-slate-600 hover:text-rose-500 hover:bg-rose-500/10 transition-all"
                      title="删除分析"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                    <Link to={`/report/${session.id}`} className="text-slate-600 hover:text-slate-300 transition-colors">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
