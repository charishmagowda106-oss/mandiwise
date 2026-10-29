import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Search, X, Loader2, Crosshair, Store } from 'lucide-react';
import useLocation from '../hooks/useLocation';
import { searchLocations } from '../services/location';
import { useLanguage } from '../i18n';

/** Header chip + picker: use the GPS position OR set any place manually
 *  (search a town/mandi). One shared location feeds every page. */
export default function LocationPicker() {
  const { t } = useLanguage();
  const { location, loading: locating, error, refresh, setManual } = useLocation();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const requestId = useRef(0);

  const label = location
    ? location.name || `${location.lat.toFixed(2)}, ${location.lng.toFixed(2)}`
    : t('loc.notsetShort');

  // Debounced search (400 ms) once the farmer types 2+ characters.
  useEffect(() => {
    const text = query.trim();
    if (text.length < 2) {
      setResults([]);
      setSearchError('');
      return undefined;
    }
    setSearching(true);
    setSearchError('');
    const id = ++requestId.current;
    const timer = setTimeout(async () => {
      try {
        const places = await searchLocations(text);
        if (id === requestId.current) setResults(places);
      } catch {
        if (id === requestId.current) {
          setResults([]);
          setSearchError(t('loc.searchFailed'));
        }
      } finally {
        if (id === requestId.current) setSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [query, t]);

  const choose = place => {
    setManual(place);
    setOpen(false);
    setQuery('');
    setResults([]);
  };

  const useGps = async () => {
    const fresh = await refresh();
    if (fresh) setOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(value => !value)}
        title={t('loc.pickerTitle')}
        className="flex items-center gap-1.5 rounded-xl border border-[#d8d8ca] px-2.5 py-2 text-sm font-semibold text-[#1d3323] hover:bg-[#f4f2e8]"
      >
        <MapPin className="h-4 w-4 text-[#197638]" />
        <span className="max-w-[7.5rem] truncate">{label}</span>
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-[min(24rem,calc(100vw-2.5rem))] rounded-2xl border border-[#dedfce] bg-white p-4 shadow-xl">
          <div className="flex items-center justify-between">
            <p className="text-sm font-bold text-[#1c2b20]">{t('loc.pickerTitle')}</p>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg p-1 text-gray-400 hover:bg-[#f4f2e8]">
              <X className="h-4 w-4" />
            </button>
          </div>

          {location && (
            <p className="mt-1 text-xs text-gray-500">
              {t('loc.current', { name: location.name || `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` })}
            </p>
          )}

          {/* Option 1: GPS */}
          <button
            type="button"
            onClick={useGps}
            disabled={locating}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-[#197638] px-4 py-3 text-sm font-bold text-white hover:bg-[#15602e] disabled:opacity-60"
          >
            {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Navigation className="h-4 w-4" />}
            {locating ? t('loc.locating') : t('loc.gps')}
          </button>

          {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

          <div className="my-3 flex items-center gap-2 text-xs text-gray-400">
            <span className="h-px flex-1 bg-[#e5e5d8]" />
            {t('loc.or')}
            <span className="h-px flex-1 bg-[#e5e5d8]" />
          </div>

          {/* Option 2: search any place */}
          <label className="flex items-center gap-2 rounded-xl border border-[#d8d8ca] px-3 py-2.5 focus-within:border-[#197638]">
            <Search className="h-4 w-4 shrink-0 text-gray-400" />
            <input
              value={query}
              onChange={event => setQuery(event.target.value)}
              placeholder={t('loc.searchPlaceholder')}
              className="w-full bg-transparent text-sm outline-none"
              autoFocus
            />
            {searching && <Loader2 className="h-4 w-4 shrink-0 animate-spin text-gray-400" />}
          </label>
          <p className="mt-1.5 text-[11px] text-gray-400">{t('loc.resultsHint')}</p>

          <div className="mt-1 max-h-56 overflow-y-auto">
            {searchError && <p className="px-1 py-3 text-xs text-red-600">{searchError}</p>}
            {!searchError && query.trim().length >= 2 && !searching && results.length === 0 && (
              <p className="px-1 py-3 text-xs text-gray-500">{t('loc.noResults')}</p>
            )}
            {results.map(place => (
              <button
                key={`${place.source}-${place.name}-${place.lat}`}
                type="button"
                onClick={() => choose(place)}
                className="flex w-full items-start gap-2 rounded-xl px-2 py-2.5 text-left hover:bg-[#f4f2e8]"
              >
                {place.source === 'mandi' ? (
                  <Store className="mt-0.5 h-4 w-4 shrink-0 text-[#197638]" />
                ) : (
                  <Crosshair className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                )}
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-[#1c2b20]">{place.name}</span>
                  <span className="block truncate text-xs text-gray-500">{place.display}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
