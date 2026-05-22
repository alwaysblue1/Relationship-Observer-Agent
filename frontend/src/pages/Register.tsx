import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../lib/auth';
import { Slogan } from '../components/dashboard/Slogan';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }
    if (password.length < 4) {
      setError('密码至少需要4位');
      return;
    }

    setLoading(true);
    try {
      await register(username, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败');
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
          <h2 className="text-lg font-medium text-slate-300 mb-6">注册</h2>

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
                placeholder="输入密码（至少4位）"
                className="w-full px-4 py-3 rounded-xl bg-slate-800/50 border border-slate-700 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-violet-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">确认密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
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
              disabled={loading || !username.trim() || !password || !confirmPassword}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-500 to-rose-500 text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {loading ? '注册中...' : '注册'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            已有账号？{' '}
            <Link to="/login" className="text-violet-400 hover:text-violet-300 transition-colors">
              登录
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
