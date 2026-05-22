import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 glass-card border-t-0 border-x-0 rounded-none">
      <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-rose-500 opacity-80 group-hover:opacity-100 transition-opacity" />
          <span className="text-sm font-medium text-slate-400 tracking-wide">
            Relationship Observer
          </span>
        </Link>

        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <Link
                to="/"
                className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                to="/upload"
                className="text-sm px-4 py-1.5 rounded-full border border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-all"
              >
                新分析
              </Link>
              <span className="text-sm text-slate-500 ml-2">{user.username}</span>
              <button
                onClick={logout}
                className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
              >
                退出
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                登录
              </Link>
              <Link
                to="/register"
                className="text-sm px-4 py-1.5 rounded-full border border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-500 transition-all"
              >
                注册
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
