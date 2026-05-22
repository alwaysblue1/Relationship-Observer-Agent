import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './lib/auth';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Header } from './components/layout/Header';
import DashboardPage from './pages/Dashboard';
import UploadPage from './pages/Upload';
import ReportPage from './pages/Report';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-observer-950">
        <Header />
        <main className="pt-16">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
            <Route path="/report/:id" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
