import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';
import { getApiErrorMessage } from '../services/api';
import { requestCurrentLocation } from '../services/location';
import { useLanguage } from '../i18n';
import LanguageToggle from '../components/LanguageToggle';

export default function Register() {
  const { t } = useLanguage();
  const [formData, setFormData] = useState({ name: '', email: '', password: '', location_lat: null, location_lng: null });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      // Capture the farmer's actual location at sign-up (best effort).
      let location = { location_lat: formData.location_lat, location_lng: formData.location_lng };
      try {
        const fresh = await requestCurrentLocation({ timeout: 6000 });
        location = { location_lat: fresh.lat, location_lng: fresh.lng };
      } catch {
        /* denied or unavailable — register without a location */
      }
      await register({ ...formData, ...location });
      navigate('/');
    } catch (err) {
      setError(getApiErrorMessage(err, t('reg.error')));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f4e7] px-5 py-12">
      <div className="mx-auto w-full max-w-lg">
        <div className="mb-4 flex justify-end">
          <LanguageToggle />
        </div>
        <div className="mb-8 flex items-center justify-center gap-3 text-[#197638]">
          <Sprout className="h-10 w-10" />
          <h1 className="text-3xl font-bold">MandiWise</h1>
        </div>
        <div className="mw-panel p-7 sm:p-9">
          <h2 className="text-2xl font-bold">{t('reg.title')}</h2>
          <p className="mt-2 text-gray-500">{t('login.sub')}</p>
          <div className="my-7 grid grid-cols-2 rounded-2xl bg-[#eeecdf] p-1 text-center">
            <Link to="/login" className="rounded-xl py-2 text-gray-600">{t('login.tab')}</Link>
            <span className="rounded-xl bg-white py-2 font-semibold shadow-sm">{t('signup.tab')}</span>
          </div>
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
          <div>
            <label htmlFor="register-name" className="mw-label">{t('reg.name')}</label>
            <input id="register-name" name="name" autoComplete="name" type="text" minLength="2" value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="register-email" className="mw-label">{t('login.email')}</label>
            <input id="register-email" name="email" autoComplete="email" type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="register-password" className="mw-label">{t('login.password')}</label>
            <input id="register-password" name="password" autoComplete="new-password" type="password" minLength="8" maxLength="72" value={formData.password} onChange={e=>setFormData({...formData, password: e.target.value})} required className="mw-input" />
            <p className="mt-1 text-xs text-gray-500">{t('reg.hint')}</p>
          </div>
          <button disabled={submitting} type="submit" className="mw-button w-full">{submitting ? t('reg.creating') : t('reg.button')}</button>
        </form>
        </div>
      </div>
    </div>
  );
}
