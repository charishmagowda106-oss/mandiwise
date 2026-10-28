import React, { useState, useContext, useEffect, useRef } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout, Smartphone, KeyRound, ChevronLeft } from 'lucide-react';
import { getApiErrorMessage } from '../services/api';
import { useLanguage } from '../i18n';
import LanguageToggle from '../components/LanguageToggle';

export default function Login() {
  const { t } = useLanguage();
  const [method, setMethod] = useState('password'); // 'password' | 'otp'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login, requestOtp, loginWithOtp } = useContext(AuthContext);
  const navigate = useNavigate();

  // OTP flow state
  const [phone, setPhone] = useState('');
  const [step, setStep] = useState('phone'); // 'phone' | 'code'
  const [code, setCode] = useState('');
  const [sent, setSent] = useState(null); // response from request-otp
  const [cooldown, setCooldown] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => () => clearInterval(timerRef.current), []);

  const startCooldown = (seconds) => {
    setCooldown(seconds);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCooldown(value => {
        if (value <= 1) {
          clearInterval(timerRef.current);
          return 0;
        }
        return value - 1;
      });
    }, 1000);
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
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

  const handleSendCode = async (event) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const data = await requestOtp(phone.trim());
      setSent(data);
      setStep('code');
      startCooldown(data.resend_after || 60);
      // Dev mode (no SMS/email provider): prefill so local testing is one click.
      if (data.dev_code) setCode(data.dev_code);
    } catch (err) {
      setError(getApiErrorMessage(err, t('login.error')));
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (event) => {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await loginWithOtp(phone.trim(), code.trim());
      navigate('/');
    } catch (err) {
      setError(getApiErrorMessage(err, t('login.error')));
    } finally {
      setSubmitting(false);
    }
  };

  const resetOtp = () => {
    setStep('phone');
    setCode('');
    setSent(null);
    setError('');
    clearInterval(timerRef.current);
    setCooldown(0);
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

          {/* Login method: password or phone OTP */}
          <div className="mb-6 grid grid-cols-2 rounded-2xl border border-[#e3e2d3] bg-[#faf9f1] p-1 text-center text-sm">
            <button
              type="button"
              onClick={() => { setMethod('password'); resetOtp(); }}
              className={`flex items-center justify-center gap-2 rounded-xl py-2 font-semibold ${method === 'password' ? 'bg-white text-[#174d27] shadow-sm' : 'text-gray-500'}`}
            >
              <KeyRound className="h-4 w-4" /> {t('login.methodPassword')}
            </button>
            <button
              type="button"
              onClick={() => { setMethod('otp'); setError(''); }}
              className={`flex items-center justify-center gap-2 rounded-xl py-2 font-semibold ${method === 'otp' ? 'bg-white text-[#174d27] shadow-sm' : 'text-gray-500'}`}
            >
              <Smartphone className="h-4 w-4" /> {t('login.methodOtp')}
            </button>
          </div>

          {method === 'password' ? (
          <form onSubmit={handlePasswordSubmit} className="space-y-5">
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
          ) : step === 'phone' ? (
          <form onSubmit={handleSendCode} className="space-y-5">
            {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
            <div>
              <label htmlFor="login-phone" className="mw-label">{t('login.phone')}</label>
              <input
                id="login-phone"
                name="phone"
                autoComplete="tel-national"
                inputMode="tel"
                type="tel"
                placeholder="98765 43210"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                required
                className="mw-input"
              />
              <p className="mt-1 text-xs text-gray-500">{t('otp.hint')}</p>
            </div>
            <button disabled={submitting} type="submit" className="mw-button w-full">
              {submitting ? t('otp.sending') : t('otp.send')}
            </button>
          </form>
          ) : (
          <form onSubmit={handleVerify} className="space-y-5">
            {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
            <div className="rounded-2xl bg-[#eef5ee] px-4 py-3 text-sm text-[#174d27]">
              {sent?.message ? `${sent.message}` : t('otp.sent')}
              {sent?.masked_phone && <span className="font-semibold"> · {sent.masked_phone}</span>}
            </div>
            {sent?.dev_code && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
                {t('otp.devHint', { code: sent.dev_code })}
              </div>
            )}
            <div>
              <label htmlFor="login-code" className="mw-label">{t('otp.enter')}</label>
              <input
                id="login-code"
                name="code"
                autoComplete="one-time-code"
                inputMode="numeric"
                maxLength={6}
                pattern="\d{6}"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))}
                required
                autoFocus
                className="mw-input tracking-[0.5em]"
                placeholder="••••••"
              />
            </div>
            <button disabled={submitting || code.length !== 6} type="submit" className="mw-button w-full">
              {submitting ? t('otp.verifying') : t('otp.verify')}
            </button>
            <div className="flex items-center justify-between text-sm">
              <button type="button" onClick={resetOtp} className="flex items-center gap-1 font-semibold text-gray-600 hover:text-[#197638]">
                <ChevronLeft className="h-4 w-4" /> {t('otp.changeNumber')}
              </button>
              <button
                type="button"
                disabled={cooldown > 0 || submitting}
                onClick={handleSendCode}
                className="font-semibold text-[#197638] disabled:text-gray-400"
              >
                {cooldown > 0 ? t('otp.resendIn', { seconds: cooldown }) : t('otp.resend')}
              </button>
            </div>
          </form>
          )}
        </div>
      </div>
    </div>
  );
}
