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
          <NavLink to="/" className="flex items-center gap-2 text-[#197638]">
            <Sprout className="h-8 w-8" />
            <span className="text-2xl font-bold tracking-tight">MandiWise</span>
          </NavLink>
          <nav className="hidden items-center gap-2 md:flex">
            {links.map(([to, Icon, label]) => (
              <NavLink key={to} to={to} end={to === '/'} className={({isActive}) => `flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold ${isActive ? 'bg-[#e9ecd7] text-[#174d27]' : 'text-gray-600 hover:bg-[#f4f2e8]'}`}>
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
            <NavLink key={to} to={to} onClick={() => setMenuOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 font-medium text-gray-700 hover:bg-[#f4f2e8]"><Icon className="h-5 w-5" />{label}</NavLink>
          ))}
          <button onClick={handleLogout} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 font-medium text-red-700 hover:bg-red-50"><LogOut className="h-5 w-5" />{t('nav.logout')}</button>
        </nav>}
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
