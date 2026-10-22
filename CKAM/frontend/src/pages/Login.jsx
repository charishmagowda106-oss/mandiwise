import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';
import { getApiErrorMessage } from '../services/api';
import { useLanguage } from '../i18n';
import LanguageToggle from '../components/LanguageToggle';

export default function Login() {
  const { t } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(getApiErrorMessage(err, t('login.error')));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f4e7] px-5 py-14">
      <div className="mx-auto w-full max-w-lg">
        <div className="mb-4 flex justify-end">
          <LanguageToggle />
        </div>
        <div className="mb-10 flex items-center justify-center gap-3 text-[#197638]">
          <Sprout className="h-10 w-10" />
          <h1 className="text-3xl font-bold">MandiWise</h1>
        </div>
        <div className="mw-panel p-7 sm:p-9">
          <h2 className="text-2xl font-bold">{t('login.title')}</h2>
          <p className="mt-2 text-gray-500">{t('login.sub')}</p>
          <div className="my-7 grid grid-cols-2 rounded-2xl bg-[#eeecdf] p-1 text-center">
            <span className="rounded-xl bg-white py-2 font-semibold shadow-sm">{t('login.tab')}</span>
            <Link to="/register" className="rounded-xl py-2 text-gray-600">{t('signup.tab')}</Link>
          </div>
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
          <div>
            <label htmlFor="login-email" className="mw-label">{t('login.email')}</label>
            <input id="login-email" name="email" autoComplete="email" type="email" value={email} onChange={e=>setEmail(e.target.value)} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="login-password" className="mw-label">{t('login.password')}</label>
            <input id="login-password" name="password" autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required className="mw-input" />
          </div>
          <button disabled={submitting} type="submit" className="mw-button w-full">{submitting ? t('login.loading') : t('login.button')}</button>
        </form>
        </div>
      </div>
    </div>
  );
}
