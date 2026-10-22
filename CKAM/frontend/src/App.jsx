import React, { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthContext } from './context/AuthContext';
import { useLanguage } from './i18n';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import MandiCompare from './pages/MandiCompare';
import PricePrediction from './pages/PricePrediction';
import AppErrorBoundary from './components/AppErrorBoundary';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const { t } = useLanguage();
  if (loading) return <div className="min-h-screen grid place-items-center bg-[#f8f6ec] text-[#197638] font-semibold">{t('ui.loading')}</div>;
  if (!user) return <Navigate to="/login" />;
  return children;
};

function App() {
  return (
    <AppErrorBoundary>
      <BrowserRouter>
        <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="compare" element={<MandiCompare />} />
          <Route path="predict" element={<PricePrediction />} />
        </Route>
        </Routes>
      </BrowserRouter>
    </AppErrorBoundary>
  );
}

export default App;
