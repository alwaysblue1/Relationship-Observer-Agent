import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../lib/auth';
import { Slogan } from '../components/dashboard/Slogan';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-20">
      <Slogan />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <div className="glass-card p-8">
          <h2 className="text-lg font-medium text-slate-300 mb-6">登录</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="输入用户名"
                className="w-full px-4 py-3 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-violet-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入密码"
                className="w-full px-4 py-3 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-violet-500 transition-colors"
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !username.trim() || !password}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-500 to-rose-500 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? '登录中...' : '登录'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            还没有账号？{' '}
            <Link to="/register" className="text-violet-400 hover:text-violet-300 transition-colors">
              注册
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
