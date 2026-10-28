import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getApiErrorMessage } from '../services/api';
import { Bell, CheckCheck } from 'lucide-react';

const POLL_MS = 30000;

const formatStamp = value => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value ?? '');
  const diff = (Date.now() - date.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};

/** Header bell: unread badge + dropdown of recent notifications, polled
 *  while the farmer is logged in. Marks items read as they are opened. */
export default function NotificationBell({ label }) {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const wrapRef = useRef(null);

  const refresh = async () => {
    try {
      const res = await api.get('/notifications', { params: { limit: 15 } });
      setItems(res.data.items || []);
      setUnread(res.data.unread || 0);
      setError('');
    } catch (err) {
      // Silent unless the very first load failed (backend down).
      setError(prev => prev || getApiErrorMessage(err, ''));
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, []);

  // Close the dropdown on any outside click.
  useEffect(() => {
    if (!open) return undefined;
    const onDown = event => {
      if (wrapRef.current && !wrapRef.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  const openItem = async item => {
    if (item.is_read) return;
    try {
      await api.post(`/notifications/${item.id}/read`);
      setItems(prev => prev.map(n => (n.id === item.id ? { ...n, is_read: true } : n)));
      setUnread(value => Math.max(0, value - 1));
    } catch { /* next poll will reconcile */ }
  };

  const markAll = async () => {
    try {
      await api.post('/notifications/read-all');
      setItems(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnread(0);
    } catch { /* next poll will reconcile */ }
  };

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        aria-label={`${label || 'Notifications'} (${unread} unread)`}
        onClick={() => setOpen(value => !value)}
        className="relative rounded-xl border border-[#d8d8ca] p-2.5 text-[#1d3323] hover:bg-[#f4f2e8]"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-[#c62828] px-1 text-[11px] font-bold text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-[min(22rem,calc(100vw-2.5rem))] overflow-hidden rounded-2xl border border-[#dedfce] bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-[#eeecdf] px-4 py-3">
            <p className="text-sm font-bold text-[#1c2b20]">{label || 'Notifications'}</p>
            {unread > 0 && (
              <button type="button" onClick={markAll} className="flex items-center gap-1 text-xs font-semibold text-[#197638] hover:underline">
                <CheckCheck className="h-3.5 w-3.5" /> Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-gray-500">
                {error || 'No notifications yet. Create a price alert and we will watch the market for you.'}
              </p>
            ) : (
              items.map(item => (
                <Link
                  key={item.id}
                  to={item.link || '/alerts'}
                  onClick={() => { openItem(item); setOpen(false); }}
                  className={`block border-b border-[#f1f0e4] px-4 py-3 hover:bg-[#f8f7ee] ${item.is_read ? 'opacity-70' : 'bg-[#fbfdf9]'}`}
                >
                  <div className="flex items-start gap-2">
                    {!item.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#197638]" />}
                    <div className={!item.is_read ? '' : 'pl-4'}>
                      <p className="text-sm font-semibold text-[#1c2b20]">{item.title}</p>
                      <p className="mt-0.5 text-xs text-gray-600">{item.body}</p>
                      <p className="mt-1 text-[11px] text-gray-400">{formatStamp(item.created_at)}</p>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
