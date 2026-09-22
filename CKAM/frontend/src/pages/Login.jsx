import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';
import { getApiErrorMessage } from '../services/api';

export default function Login() {
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
      setError(getApiErrorMessage(err, 'Login failed. Check your connection and try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f4e7] px-5 py-14">
      <div className="mx-auto w-full max-w-lg">
        <div className="mb-10 flex items-center justify-center gap-3 text-[#197638]">
          <Sprout className="h-10 w-10" />
          <h1 className="text-3xl font-bold">MandiWise</h1>
        </div>
        <div className="mw-panel p-7 sm:p-9">
          <h2 className="text-2xl font-bold">Welcome</h2>
          <p className="mt-2 text-gray-500">Know where and when to sell your crop.</p>
          <div className="my-7 grid grid-cols-2 rounded-2xl bg-[#eeecdf] p-1 text-center">
            <span className="rounded-xl bg-white py-2 font-semibold shadow-sm">Log in</span>
            <Link to="/register" className="rounded-xl py-2 text-gray-600">Sign up</Link>
          </div>
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
          <div>
            <label htmlFor="login-email" className="mw-label">Email</label>
            <input id="login-email" name="email" autoComplete="email" type="email" value={email} onChange={e=>setEmail(e.target.value)} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="login-password" className="mw-label">Password</label>
            <input id="login-password" name="password" autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required className="mw-input" />
          </div>
          <button disabled={submitting} type="submit" className="mw-button w-full">{submitting ? 'Logging in…' : 'Log in'}</button>
        </form>
        </div>
      </div>
    </div>
  );
}
