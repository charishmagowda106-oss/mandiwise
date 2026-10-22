import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { AuthContext } from './context/AuthContext';

// Every user-visible string in the app lives here, in English and Kannada.
// Use a key once with t('key.name', { vars }) — add new strings here only.
const translations = {
  en: {
    'ui.loading': 'Loading MandiWise…',
    'ui.language': 'Language',
    'ui.footer': 'MandiWise — price guidance from market data. Predictions are estimates, not guaranteed prices.',

    'nav.dashboard': 'Dashboard',
    'nav.compare': 'Find Mandi',
    'nav.predict': 'Predict Price',
    'nav.logout': 'Logout',

    'dash.kicker': 'Your market overview',
    'dash.namaste': 'Namaste, {name} 🌾',
    'dash.sub': 'Check official Karnataka mandi rates, then use the demo forecast tools to explore selling decisions.',
    'dash.crops': 'Available crops',
    'dash.mandis': 'Real Karnataka mandis',
    'dash.card1Title': 'Live Karnataka Rates',
    'dash.card1Sub': 'View official market prices for a selected crop.',
    'dash.card2Title': 'Predict Crop Price',
    'dash.card2Sub': 'Forecast with the trained ML model.',

    'loc.title': 'Your current location',
    'loc.saved': 'Saved: {coords}',
    'loc.notsetFull': 'Not set yet — allow location when your browser asks.',
    'loc.notsetCompare': 'Not set — allow location to see distances and the nearest mandis.',
    'loc.notsetShort': 'Not set',
    'loc.locating': 'Locating…',
    'loc.update': 'Update location',
    'loc.use': 'Use my current location',
    'loc.find': 'Find mandis near me',

    'cmp.kicker': 'Official live rates',
    'cmp.title': 'Karnataka mandi prices',
    'cmp.sub': 'Live wholesale modal prices from the Government of India’s AGMARKNET dataset, matched to the real APMC markets nearest to you.',
    'cmp.nearby': 'Mandis near you',
    'cmp.crop': 'Crop',
    'cmp.load': 'Load (quintals)',
    'cmp.live': 'Show live rates',
    'cmp.liveLoading': 'Loading live rates…',
    'cmp.rank': 'Rank by profit',
    'cmp.rankLoading': 'Ranking mandis…',
    'cmp.rankNoLoc': 'Allow your location first (button above) so distances to each mandi can be calculated.',
    'cmp.liveTitle': 'Live rates — {crop}',
    'cmp.synced': 'synced {when}',
    'cmp.reports': '{n} market reports',
    'cmp.reportsOne': '1 market report',
    'cmp.sortedByDistance': ', sorted by distance from you.',
    'cmp.noLive': 'No live reports for this crop right now — try another crop.',
    'cmp.range': 'Range {min}–{max}',
    'cmp.reported': 'Reported {date}',
    'cmp.rankTitle': 'Best mandi{crop} · {qty} quintal',
    'cmp.rankFor': ' for {crop}',
    'cmp.rankSub': 'Distances from your current location. Ranking prices come from the bundled sample history — compare with the live rates above before deciding.',
    'cmp.best': 'BEST MANDI',
    'cmp.rowMeta': '{km} km · price ₹{price}/qtl · transport ₹{transport}',
    'cmp.estProfit': 'Est. profit ₹{amount}',
    'cmp.revenue': 'revenue ₹{amount}',
    'cmp.share': 'Share on WhatsApp',
    'cmp.mapTitle': 'Mandi map',
    'cmp.mapSub': 'You and the nearest mandis on OpenStreetMap — free, no API key.',
    'cmp.mapYou': 'You',
    'cmp.trendTitle': 'Price trend',
    'cmp.trendSub': 'Monthly modal price from the bundled sample history (2022–2023).',
    'cmp.trendMandi': 'Mandi',
    'cmp.trendLoading': 'Loading trend…',
    'cmp.trendEmpty': 'No price history for this crop and mandi.',
    'cmp.trendError': 'Could not load the price trend. Is the backend running?',
    'cmp.trendModal': 'Modal price',
    'cmp.trendMin': 'Min price',
    'cmp.trendMax': 'Max price',

    'pred.kicker': 'When to sell',
    'pred.title': 'Predict crop price',
    'pred.sub': 'Demo forecast: uses the project’s trained Random Forest model and bundled sample history, not the live rate feed.',
    'pred.mandi': 'Mandi',
    'pred.horizon': 'Forecast horizon (days)',
    'pred.button': 'Predict Future Price',
    'pred.calc': 'Calculating…',
    'pred.current': 'Current stored price',
    'pred.predicted': 'Predicted price ({days} days)',
    'pred.error': 'Prediction failed. This crop and mandi may not have price history.',

    'login.title': 'Welcome',
    'login.sub': 'Know where and when to sell your crop.',
    'login.tab': 'Log in',
    'signup.tab': 'Sign up',
    'login.email': 'Email',
    'login.password': 'Password',
    'login.button': 'Log in',
    'login.loading': 'Logging in…',
    'login.error': 'Login failed. Check your connection and try again.',

    'reg.title': 'Create your account',
    'reg.name': 'Your name',
    'reg.hint': 'Use 8–72 characters.',
    'reg.button': 'Create account',
    'reg.creating': 'Creating account…',
    'reg.error': 'Registration failed. Please try again.',

    'err.market': 'Could not load market data. Make sure the backend is running.',
    'err.cropsMandis': 'Could not load crop and mandi lists. Make sure the backend is running.',
    'err.live': 'Could not load live Karnataka rates. Please try again shortly.',
    'err.rank': 'Could not rank mandis for this crop. Please try again.',
  },
  kn: {
    'ui.loading': 'ಮಂಡಿವೈಸ್ ಲೋಡ್ ಆಗುತ್ತಿದೆ…',
    'ui.language': 'ಭಾಷೆ',
    'ui.footer': 'ಮಂಡಿವೈಸ್ — ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಆಧಾರಿತ ಬೆಲೆ ಮಾರ್ಗದರ್ಶನ. ಅಂದಾಜುಗಳು ಊಹೆಗಳು; ಖಚಿತ ಬೆಲೆಗಳಲ್ಲ.',

    'nav.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    'nav.compare': 'ಮಂಡಿ ಹುಡುಕಿ',
    'nav.predict': 'ಬೆಲೆ ಅಂದಾಜು',
    'nav.logout': 'ಲಾಗ್ ಔಟ್',

    'dash.kicker': 'ನಿಮ್ಮ ಮಾರುಕಟ್ಟೆ ವಿವರ',
    'dash.namaste': 'ನಮಸ್ಕಾರ, {name} 🌾',
    'dash.sub': 'ಕರ್ನಾಟಕದ ಅಧಿಕೃತ ಮಂಡಿ ದರಗಳನ್ನು ನೋಡಿ; ನಂತರ ಬೆಳೆ ಮಾರಾಟದ ನಿರ್ಧಾರಕ್ಕೆ ಅಂದಾಜು ಸಾಧನಗಳನ್ನು ಬಳಸಿ.',
    'dash.crops': 'ಲಭ್ಯವಿರುವ ಬೆಳೆಗಳು',
    'dash.mandis': 'ನೈಜ ಕರ್ನಾಟಕ ಮಂಡಿಗಳು',
    'dash.card1Title': 'ಪ್ರತ್ಯಕ್ಷ ಕರ್ನಾಟಕ ದರಗಳು',
    'dash.card1Sub': 'ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆಯ ಅಧಿಕೃತ ಮಾರುಕಟ್ಟೆ ಬೆಲೆಗಳು.',
    'dash.card2Title': 'ಬೆಳೆ ಬೆಲೆ ಅಂದಾಜು',
    'dash.card2Sub': 'ತರಬೇತಿ ಪಡೆದ ML ಮಾದರಿಯ ಅಂದಾಜು.',

    'loc.title': 'ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಸ್ಥಳ',
    'loc.saved': 'ಉಳಿಸಲಾಗಿದೆ: {coords}',
    'loc.notsetFull': 'ಇನ್ನೂ ಹೊಂದಿಸಿಲ್ಲ — ಬ್ರೌಸರ್ ಕೇಳಿದಾಗ ಸ್ಥಳಕ್ಕೆ ಅನುಮತಿ ನೀಡಿ.',
    'loc.notsetCompare': 'ಹೊಂದಿಸಿಲ್ಲ — ದೂರ ಮತ್ತು ಹತ್ತಿರದ ಮಂಡಿಗಳನ್ನು ನೋಡಲು ಸ್ಥಳಕ್ಕೆ ಅನುಮತಿ ನೀಡಿ.',
    'loc.notsetShort': 'ಹೊಂದಿಸಿಲ್ಲ',
    'loc.locating': 'ಸ್ಥಳ ಪತ್ತೆ…',
    'loc.update': 'ಸ್ಥಳ ನವೀಕರಿಸಿ',
    'loc.use': 'ನನ್ನ ಪ್ರಸ್ತುತ ಸ್ಥಳ ಬಳಸಿ',
    'loc.find': 'ನನ್ನ ಹತ್ತಿರದ ಮಂಡಿಗಳನ್ನು ಹುಡುಕಿ',

    'cmp.kicker': 'ಅಧಿಕೃತ ಪ್ರತ್ಯಕ್ಷ ದರಗಳು',
    'cmp.title': 'ಕರ್ನಾಟಕ ಮಂಡಿ ಬೆಲೆಗಳು',
    'cmp.sub': 'ಭಾರತ ಸರ್ಕಾರದ AGMARKNET ಡೇಟಾದ ಪ್ರತ್ಯಕ್ಷ ಸಗಟು ದರಗಳು — ನಿಮಗೆ ಹತ್ತಿರದ APMC ಮಾರುಕಟ್ಟೆಗಳಿಗೆ ಹೊಂದಿಸಲಾಗಿದೆ.',
    'cmp.nearby': 'ನಿಮ್ಮ ಹತ್ತಿರದ ಮಂಡಿಗಳು',
    'cmp.crop': 'ಬೆಳೆ',
    'cmp.load': 'ಪ್ರಮಾಣ (ಕ್ವಿಂಟಾಲ್)',
    'cmp.live': 'ಪ್ರತ್ಯಕ್ಷ ದರಗಳನ್ನು ತೋರಿಸಿ',
    'cmp.liveLoading': 'ಪ್ರತ್ಯಕ್ಷ ದರಗಳು ಲೋಡ್ ಆಗುತ್ತಿದೆ…',
    'cmp.rank': 'ಲಾಭದ ಆಧಾರದ ಮೇಲೆ ಶ್ರೇಯಾಂಕಿಸಿ',
    'cmp.rankLoading': 'ಮಂಡಿಗಳನ್ನು ಶ್ರೇಯಾಂಕಿಸಲಾಗುತ್ತಿದೆ…',
    'cmp.rankNoLoc': 'ಪ್ರತಿ ಮಂಡಿಗೆ ದೂರ ಲೆಕ್ಕ ಹಾಕಲು ಮೊದಲು ನಿಮ್ಮ ಸ್ಥಳಕ್ಕೆ ಅನುಮತಿ ನೀಡಿ (ಮೇಲಿನ ಬಟನ್).',
    'cmp.liveTitle': 'ಪ್ರತ್ಯಕ್ಷ ದರಗಳು — {crop}',
    'cmp.synced': 'ನವೀಕರಣ {when}',
    'cmp.reports': '{n} ಮಾರುಕಟ್ಟೆ ವರದಿಗಳು',
    'cmp.reportsOne': '1 ಮಾರುಕಟ್ಟೆ ವರದಿ',
    'cmp.sortedByDistance': ' — ನಿಮ್ಮಿಂದ ದೂರದ ಕ್ರಮದಲ್ಲಿ.',
    'cmp.noLive': 'ಈ ಬೆಳೆಯ ಪ್ರತ್ಯಕ್ಷ ವರದಿಗಳು ಈಗ ಇಲ್ಲ — ಬೇರೆ ಬೆಳೆ ಪ್ರಯತ್ನಿಸಿ.',
    'cmp.range': 'ವ್ಯಾಪ್ತಿ {min}–{max}',
    'cmp.reported': 'ವರದಿ {date}',
    'cmp.rankTitle': 'ಅತ್ಯುತ್ತಮ ಮಂಡಿ{crop} · {qty} ಕ್ವಿಂಟಾಲ್',
    'cmp.rankFor': ' — {crop}',
    'cmp.rankSub': 'ನಿಮ್ಮ ಪ್ರಸ್ತುತ ಸ್ಥಳದಿಂದ ದೂರಗಳು. ಶ್ರೇಯಾಂಕದ ಬೆಲೆಗಳು ಬಂಡಲ್ ಮಾದರಿ ಇತಿಹಾಸದಿಂದ — ನಿರ್ಧಾರಕ್ಕೂ ಮೊದಲು ಮೇಲಿನ ಪ್ರತ್ಯಕ್ಷ ದರಗಳೊಂದಿಗೆ ಹೋಲಿಸಿ.',
    'cmp.best': 'ಅತ್ಯುತ್ತಮ ಮಂಡಿ',
    'cmp.rowMeta': '{km} ಕಿಮೀ · ಬೆಲೆ ₹{price}/ಕ್ವಿ · ಸಾಗಣೆ ₹{transport}',
    'cmp.estProfit': 'ನಿರೀಕ್ಷಿತ ಲಾಭ ₹{amount}',
    'cmp.revenue': 'ಆದಾಯ ₹{amount}',
    'cmp.share': 'WhatsApp ನಲ್ಲಿ ಹಂಚಿಕೊಳ್ಳಿ',
    'cmp.mapTitle': 'ಮಂಡಿ ನಕ್ಷೆ',
    'cmp.mapSub': 'ನಿಮ್ಮ ಸ್ಥಳ ಮತ್ತು ಹತ್ತಿರದ ಮಂಡಿಗಳು — OpenStreetMap ನಕ್ಷೆಯಲ್ಲಿ (ಉಚಿತ, API ಕೀ ಬೇಡ).',
    'cmp.mapYou': 'ನೀವು',
    'cmp.trendTitle': 'ಬೆಲೆ ಪ್ರವೃತ್ತಿ',
    'cmp.trendSub': 'ಮಾಸಿಕ ಮಾಡಲ್ ಬೆಲೆ — ಬಂಡಲ್ ಮಾದರಿ ಇತಿಹಾಸ (2022–2023).',
    'cmp.trendMandi': 'ಮಂಡಿ',
    'cmp.trendLoading': 'ಪ್ರವೃತ್ತಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ…',
    'cmp.trendEmpty': 'ಈ ಬೆಳೆ ಮತ್ತು ಮಂಡಿಗೆ ಬೆಲೆ ಇತಿಹಾಸ ಇಲ್ಲ.',
    'cmp.trendError': 'ಬೆಲೆ ಪ್ರವೃತ್ತಿ ಲೋಡ್ ಆಗಲಿಲ್ಲ. ಬ್ಯಾಕೆಂಡ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ ನೋಡಿ.',
    'cmp.trendModal': 'ಮಾಡಲ್ ಬೆಲೆ',
    'cmp.trendMin': 'ಕನಿಷ್ಠ ಬೆಲೆ',
    'cmp.trendMax': 'ಗರಿಷ್ಠ ಬೆಲೆ',

    'pred.kicker': 'ಮಾರಾಟಕ್ಕೆ ಸರಿಯಾದ ಸಮಯ',
    'pred.title': 'ಬೆಳೆ ಬೆಲೆ ಅಂದಾಜು',
    'pred.sub': 'ಡೆಮೊ ಅಂದಾಜು: ತರಬೇತಿ ಪಡೆದ Random Forest ಮಾದರಿ ಮತ್ತು ಬಂಡಲ್ ಮಾದರಿ ಇತಿಹಾಸ ಬಳಸುತ್ತದೆ; ಪ್ರತ್ಯಕ್ಷ ದರಗಳಲ್ಲ.',
    'pred.mandi': 'ಮಂಡಿ',
    'pred.horizon': 'ಅಂದಾಜು ಅವಧಿ (ದಿನಗಳು)',
    'pred.button': 'ಭವಿಷ್ಯದ ಬೆಲೆ ಅಂದಾಜು',
    'pred.calc': 'ಲೆಕ್ಕ ಹಾಕಲಾಗುತ್ತಿದೆ…',
    'pred.current': 'ಪ್ರಸ್ತುತ ಉಳಿಸಿದ ಬೆಲೆ',
    'pred.predicted': 'ಅಂದಾಜು ಬೆಲೆ ({days} ದಿನಗಳು)',
    'pred.error': 'ಅಂದಾಜು ವಿಫಲವಾಗಿದೆ. ಈ ಬೆಳೆ ಮತ್ತು ಮಂಡಿಗೆ ಬೆಲೆ ಇತಿಹಾಸ ಇಲ್ಲದಿರಬಹುದು.',

    'login.title': 'ಸ್ವಾಗತ',
    'login.sub': 'ನಿಮ್ಮ ಬೆಳೆಯನ್ನು ಎಲ್ಲಿ ಮತ್ತು ಯಾವಾಗ ಮಾರಬೇಕೆಂದು ತಿಳಿಯಿರಿ.',
    'login.tab': 'ಲಾಗ್ ಇನ್',
    'signup.tab': 'ಸೈನ್ ಅಪ್',
    'login.email': 'ಇಮೇಲ್',
    'login.password': 'ಪಾಸ್‌ವರ್ಡ್',
    'login.button': 'ಲಾಗ್ ಇನ್',
    'login.loading': 'ಲಾಗ್ ಇನ್ ಆಗುತ್ತಿದೆ…',
    'login.error': 'ಲಾಗ್ ಇನ್ ವಿಫಲವಾಗಿದೆ. ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',

    'reg.title': 'ನಿಮ್ಮ ಖಾತೆ ರಚಿಸಿ',
    'reg.name': 'ನಿಮ್ಮ ಹೆಸರು',
    'reg.hint': '8–72 ಅಕ್ಷರಗಳನ್ನು ಬಳಸಿ.',
    'reg.button': 'ಖಾತೆ ರಚಿಸಿ',
    'reg.creating': 'ಖಾತೆ ರಚಿಸಲಾಗುತ್ತಿದೆ…',
    'reg.error': 'ನೋಂದಣಿ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',

    'err.market': 'ಮಾರುಕಟ್ಟೆ ಮಾಹಿತಿ ಲೋಡ್ ಆಗಲಿಲ್ಲ. ಬ್ಯಾಕೆಂಡ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ ಎಂದು ಪರಿಶೀಲಿಸಿ.',
    'err.cropsMandis': 'ಬೆಳೆ ಮತ್ತು ಮಂಡಿ ಪಟ್ಟಿಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗಲಿಲ್ಲ. ಬ್ಯಾಕೆಂಡ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ ಪರಿಶೀಲಿಸಿ.',
    'err.live': 'ಪ್ರತ್ಯಕ್ಷ ಕರ್ನಾಟಕ ದರಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗಲಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.',
    'err.rank': 'ಈ ಬೆಳೆಗೆ ಮಂಡಿಗಳನ್ನು ಶ್ರೇಯಾಂಕಿಸಲಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
  },
};

const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  const { user, updateProfile } = useContext(AuthContext);
  const [lang, setLang] = useState(() => localStorage.getItem('mw_lang') || 'en');

  // First visit on this device: honour the language saved on the profile.
  useEffect(() => {
    if (!localStorage.getItem('mw_lang') && user?.language && translations[user.language]) {
      setLang(user.language);
    }
  }, [user?.language]);

  const setLanguage = useCallback((next) => {
    if (!translations[next]) return;
    setLang(next);
    localStorage.setItem('mw_lang', next);
    // Remember the choice on the profile too (silently — not critical).
    if (user) updateProfile({ language: next }).catch(() => {});
  }, [user, updateProfile]);

  const t = useCallback((key, vars) => {
    let value = translations[lang]?.[key] ?? translations.en[key] ?? key;
    if (vars) value = value.replace(/\{(\w+)\}/g, (match, name) => (vars[name] ?? match));
    return value;
  }, [lang]);

  return <LanguageContext.Provider value={{ lang, setLanguage, t }}>{children}</LanguageContext.Provider>;
};

export const useLanguage = () => useContext(LanguageContext);
