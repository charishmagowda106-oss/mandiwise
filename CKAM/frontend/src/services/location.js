export const STORAGE_KEY = 'mw_location_v1';
export const ASKED_KEY = 'mw_location_asked_v1';

import api from './api';

/** Search places by name for the manual picker (local mandis/towns + OSM). */
export const searchLocations = async (query, { limit = 8 } = {}) => {
  const res = await api.get('/locations/search', { params: { q: query, limit } });
  return res.data.results || [];
};


export const readStoredLocation = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Number.isFinite(parsed?.lat) && Number.isFinite(parsed?.lng) ? parsed : null;
  } catch {
    return null;
  }
};

export const storeLocation = location => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(location));
  } catch {
    /* storage unavailable (private mode) — location just won't persist */
  }
};

export const hasAskedLocation = () => {
  try {
    return localStorage.getItem(ASKED_KEY) === '1';
  } catch {
    return false;
  }
};

export const markLocationAsked = () => {
  try {
    localStorage.setItem(ASKED_KEY, '1');
  } catch {
    /* ignore */
  }
};

/** Resolve the farmer's current GPS position (browser Geolocation API). */
export const requestCurrentLocation = ({ timeout = 12000 } = {}) =>
  new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Location is not supported by this browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      position => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
          at: Date.now(),
        };
        storeLocation(location);
        resolve(location);
      },
      error => {
        const message =
          error.code === error.PERMISSION_DENIED
            ? 'Location permission denied. Click the lock icon in your browser address bar, allow location, then try again.'
            : 'Could not read your location. Check that GPS/network is on and try again.';
        reject(new Error(message));
      },
      { enableHighAccuracy: true, timeout, maximumAge: 30000 },
    );
  });

/** Great-circle distance in kilometres. */
export const haversineKm = (a, b) => {
  if (!a || !b) return null;
  const toRad = value => (value * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
};

/** "APMC Hubballi" / "Hubballi APMC" -> "hubballi" */
export const normalizeMarketName = name =>
  String(name ?? '')
    .toLowerCase()
    .replace(/\(.*?\)/g, ' ')
    .replace(/[^a-z0-9 ]/g, ' ')
    .replace(/\bapmc\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

/** Map a live-feed market name onto a known mandi row (with coordinates). */
export const matchMarket = (liveName, mandiIndex) => {
  const key = normalizeMarketName(liveName);
  if (!key) return null;
  const exact = mandiIndex.get(key);
  if (exact) return exact;
  if (key.length < 4) return null;
  for (const [candidate, mandi] of mandiIndex) {
    if (candidate.includes(key) || key.includes(candidate)) return mandi;
  }
  return null;
};
