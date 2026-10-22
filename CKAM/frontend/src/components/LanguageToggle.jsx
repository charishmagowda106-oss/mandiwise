import React from 'react';
import { useLanguage } from '../i18n';

// Small EN | ಕನ್ನಡ pill. Used in the app header and on the login/register screens.
export default function LanguageToggle() {
  const { lang, setLanguage } = useLanguage();

  const button = (code, label) => (
    <button
      type="button"
      onClick={() => setLanguage(code)}
      aria-pressed={lang === code}
      className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
        lang === code ? 'bg-[#197638] text-white shadow-sm' : 'text-gray-600 hover:bg-[#f4f2e8]'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div
      className="flex items-center rounded-xl border border-[#d8d8ca] bg-white p-0.5"
      aria-label="Language"
    >
      {button('en', 'EN')}
      {button('kn', 'ಕನ್ನಡ')}
    </div>
  );
}
