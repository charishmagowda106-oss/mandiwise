import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', location_lat: 20.0, location_lng: 78.0 });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await register(formData);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f4e7] px-5 py-12">
      <div className="mx-auto w-full max-w-lg">
        <div className="mb-8 flex items-center justify-center gap-3 text-[#197638]">
          <Sprout className="h-10 w-10" />
          <h1 className="text-3xl font-bold">MandiWise</h1>
        </div>
        <div className="mw-panel p-7 sm:p-9">
          <h2 className="text-2xl font-bold">Create your account</h2>
          <p className="mt-2 text-gray-500">Know where and when to sell your crop.</p>
          <div className="my-7 grid grid-cols-2 rounded-2xl bg-[#eeecdf] p-1 text-center">
            <Link to="/login" className="rounded-xl py-2 text-gray-600">Log in</Link>
            <span className="rounded-xl bg-white py-2 font-semibold shadow-sm">Sign up</span>
          </div>
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
          <div>
            <label htmlFor="register-name" className="mw-label">Your name</label>
            <input id="register-name" name="name" autoComplete="name" type="text" value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="register-email" className="mw-label">Email</label>
            <input id="register-email" name="email" autoComplete="email" type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} required className="mw-input" />
          </div>
          <div>
            <label htmlFor="register-password" className="mw-label">Password</label>
            <input id="register-password" name="password" autoComplete="new-password" type="password" minLength="6" value={formData.password} onChange={e=>setFormData({...formData, password: e.target.value})} required className="mw-input" />
          </div>
          <button disabled={submitting} type="submit" className="mw-button w-full">{submitting ? 'Creating account…' : 'Create account'}</button>
        </form>
        </div>
      </div>
    </div>
  );
}
