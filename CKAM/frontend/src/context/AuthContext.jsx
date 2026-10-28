import React, { createContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
        } catch (error) {
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    fetchUser();
  }, []);

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const res = await api.post('/auth/login', formData);
    localStorage.setItem('token', res.data.access_token);
    const userRes = await api.get('/auth/me');
    setUser(userRes.data);
  };

  // Phone + OTP login (alternative to email/password).
  const requestOtp = async (phone) => {
    const res = await api.post('/auth/request-otp', { phone });
    return res.data; // { message, masked_phone, expires_in, resend_after, dev_code? }
  };

  const loginWithOtp = async (phone, code) => {
    const res = await api.post('/auth/verify-otp', { phone, code });
    localStorage.setItem('token', res.data.access_token);
    const userRes = await api.get('/auth/me');
    setUser(userRes.data);
  };

  const register = async (userData) => {
    await api.post('/auth/register', userData);
    await login(userData.email, userData.password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const updateProfile = useCallback(async (patch) => {
    const res = await api.patch('/auth/me', patch);
    setUser(res.data);
    return res.data;
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, requestOtp, loginWithOtp, register, logout, updateProfile, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
