import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

layout_jsx = """
import React, { useContext } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { Sprout, LogOut, Map, TrendingUp, Home } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-4 flex items-center gap-2 border-b">
          <Sprout className="text-agrigreen-600 w-8 h-8" />
          <span className="text-xl font-bold text-gray-800">MandiWise</span>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <Link to="/" className="flex items-center gap-2 p-2 rounded hover:bg-agrigreen-50 text-gray-700">
            <Home className="w-5 h-5" /> Dashboard
          </Link>
          <Link to="/compare" className="flex items-center gap-2 p-2 rounded hover:bg-agrigreen-50 text-gray-700">
            <Map className="w-5 h-5" /> Compare Mandis
          </Link>
          <Link to="/predict" className="flex items-center gap-2 p-2 rounded hover:bg-agrigreen-50 text-gray-700">
            <TrendingUp className="w-5 h-5" /> Price Prediction
          </Link>
        </nav>
        <div className="p-4 border-t">
          <p className="text-sm font-medium mb-2">Farmer: {user?.name}</p>
          <button onClick={handleLogout} className="flex items-center gap-2 text-red-600 hover:text-red-700">
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white shadow-sm p-4">
          <h1 className="text-xl font-semibold text-gray-800">Welcome to MandiWise</h1>
        </header>
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
"""
write_file('frontend/src/components/Layout.jsx', layout_jsx)

login_jsx = """
import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      alert("Login failed. Check credentials.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <div className="flex items-center justify-center gap-2 mb-6">
          <Sprout className="text-agrigreen-600 w-10 h-10" />
          <h1 className="text-2xl font-bold text-gray-800">MandiWise</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border focus:border-agrigreen-500 focus:ring-agrigreen-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border focus:border-agrigreen-500 focus:ring-agrigreen-500" />
          </div>
          <button type="submit" className="w-full bg-agrigreen-600 text-white p-2 rounded hover:bg-agrigreen-700">Log In</button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account? <Link to="/register" className="text-agrigreen-600 hover:underline">Register</Link>
        </p>
      </div>
    </div>
  );
}
"""
write_file('frontend/src/pages/Login.jsx', login_jsx)

register_jsx = """
import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', location_lat: 20.0, location_lng: 78.0 });
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(formData);
      navigate('/');
    } catch (err) {
      alert("Registration failed.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <div className="flex items-center justify-center gap-2 mb-6">
          <Sprout className="text-agrigreen-600 w-10 h-10" />
          <h1 className="text-2xl font-bold text-gray-800">MandiWise</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input type="text" value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input type="password" value={formData.password} onChange={e=>setFormData({...formData, password: e.target.value})} required className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" />
          </div>
          <button type="submit" className="w-full bg-agrigreen-600 text-white p-2 rounded hover:bg-agrigreen-700">Register</button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account? <Link to="/login" className="text-agrigreen-600 hover:underline">Log In</Link>
        </p>
      </div>
    </div>
  );
}
"""
write_file('frontend/src/pages/Register.jsx', register_jsx)
