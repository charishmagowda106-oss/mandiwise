import React, { useContext, useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { useLanguage } from '../i18n';
import LanguageToggle from './LanguageToggle';
import LocationPicker from './LocationPicker';
import { Sprout, LogOut, MapPin, TrendingUp, Home, Menu, X, BellRing } from 'lucide-react';
import NotificationBell from './NotificationBell';

export default function Layout() {
  const { user, logout } = useContext(AuthContext);
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const links = [
    ['/', Home, t('nav.dashboard')],
    ['/compare', MapPin, t('nav.compare')],
    ['/predict', TrendingUp, t('nav.predict')],
    ['/alerts', BellRing, t('nav.alerts')],
  ];

  return (
    <div className="min-h-screen bg-[#f8f6ec]">
      <header className="sticky top-0 z-20 border-b border-[#dedfce] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-6xl items-center justify-between px-5">
          <NavLink to="/" className="flex items-center gap-2.5">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-[#197638] to-[#0e5a29] text-white shadow-sm">
              <Sprout className="h-6 w-6" />
            </span>
            <span className="bg-gradient-to-r from-[#197638] to-[#2f9e4f] bg-clip-text text-2xl font-bold tracking-tight text-transparent">MandiWise</span>
          </NavLink>
          <nav className="hidden items-center gap-2 md:flex">
            {links.map(([to, Icon, label]) => (
              <NavLink key={to} to={to} end={to === '/'} className={({isActive}) => `flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${isActive ? 'bg-[#197638] text-white shadow-sm' : 'text-gray-600 hover:bg-[#f4f2e8]'}`}>
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
            <span className="ml-2 text-sm text-gray-500">{user?.name}</span>
            <LanguageToggle />
            <LocationPicker />
            <NotificationBell label={t('nav.notifications')} />
            <button onClick={handleLogout} className="ml-1 flex items-center gap-2 rounded-xl border border-[#d8d8ca] px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-[#f4f2e8]">
              <LogOut className="h-4 w-4" /> {t('nav.logout')}
            </button>
          </nav>
          <div className="flex items-center gap-2 md:hidden">
            <LanguageToggle />
            <LocationPicker />
            <NotificationBell label={t('nav.notifications')} />
            <button aria-label="Toggle navigation" onClick={() => setMenuOpen(v => !v)} className="rounded-xl border border-[#d8d8ca] p-2.5 text-[#1d3323]">
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
        {menuOpen && <nav className="space-y-1 border-t border-[#e5e5d8] bg-white px-5 py-4 md:hidden">
          {links.map(([to, Icon, label]) => (
            <NavLink key={to} to={to} onClick={() => setMenuOpen(false)} className={({isActive}) => `flex items-center gap-3 rounded-xl px-3 py-3 font-medium transition ${isActive ? 'bg-[#197638] text-white' : 'text-gray-700 hover:bg-[#f4f2e8]'}`}><Icon className="h-5 w-5" />{label}</NavLink>
          ))}
          <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 font-medium text-red-700 hover:bg-red-50"><LogOut className="h-5 w-5" />{t('nav.logout')}</button>
        </nav>}
        <div className="h-0.5 bg-gradient-to-r from-[#197638] via-emerald-400 to-amber-300" />
      </header>
      <div>
        <main className="mx-auto max-w-6xl px-5 py-8 md:py-12">
          <Outlet />
        </main>
        <footer className="border-t border-[#dedfce] px-5 py-8 text-center text-sm text-gray-500">{t('ui.footer')}</footer>
      </div>
    </div>
  );
}
