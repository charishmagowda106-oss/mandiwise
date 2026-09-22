import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// FastAPI returns `detail` as a string for plain HTTP errors, but as an ARRAY
// of field errors for 422 validation failures (e.g. password too short).
// Passing that array into React state makes React throw while rendering, which
// used to blank the whole page instead of showing the message.
export const getApiErrorMessage = (err, fallback) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === 'string' ? item : item?.msg))
      .filter(Boolean);
    if (messages.length) return messages.join(' ');
  }
  if (err?.message && !err?.response) return `${fallback} (${err.message})`;
  return fallback;
};

export default api;
