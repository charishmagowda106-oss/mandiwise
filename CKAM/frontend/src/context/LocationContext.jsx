import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AuthContext } from './AuthContext';
import {
  hasAskedLocation,
  markLocationAsked,
  readStoredLocation,
  requestCurrentLocation,
  storeLocation,
} from '../services/location';

const locationFromProfile = user => {
  if (
    user &&
    user.location_lat != null &&
    user.location_lng != null &&
    Number.isFinite(Number(user.location_lat)) &&
    Number.isFinite(Number(user.location_lng))
  ) {
    return { lat: Number(user.location_lat), lng: Number(user.location_lng), source: 'profile' };
  }
  return null;
};

/** The farmer's location, shared app-wide (header picker + every page).
 *  Sources: manual picker (town/mandi search), GPS, or the saved profile. */
export const LocationContext = createContext(null);

export function LocationProvider({ children }) {
  const { user, updateProfile } = useContext(AuthContext);
  const [location, setLocation] = useState(() => readStoredLocation() ?? locationFromProfile(user));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inFlight = useRef(false);

  const mirrorToProfile = useCallback(loc => {
    if (!updateProfile) return;
    // Saving the profile location is best-effort — the local copy is the source of truth.
    Promise.resolve(
      updateProfile({ location_lat: loc.lat, location_lng: loc.lng }),
    ).catch(() => {});
  }, [updateProfile]);

  /** GPS fix — also mirrors onto the profile and closes the "pick location" flow. */
  const refresh = useCallback(async () => {
    if (inFlight.current) return; // one geolocation request at a time
    inFlight.current = true;
    setLoading(true);
    setError('');
    try {
      const fresh = await requestCurrentLocation();
      setLocation(fresh);
      markLocationAsked();
      mirrorToProfile(fresh);
      return fresh;
    } catch (err) {
      setError(err?.message || 'Could not read your location.');
      markLocationAsked();
      return null;
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }, [mirrorToProfile]);

  /** Manually chosen place (from the header picker's search). */
  const setManual = useCallback(({ name, lat, lng }) => {
    const next = {
      lat: Number(lat),
      lng: Number(lng),
      name,
      source: 'manual',
      at: Date.now(),
    };
    storeLocation(next);
    setLocation(next);
    setError('');
    mirrorToProfile(next);
    return next;
  }, [mirrorToProfile]);

  // Ask for GPS once on the very first visit (same behaviour the pages had).
  useEffect(() => {
    if (location || hasAskedLocation()) return;
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // After login, adopt the profile location if this device has none saved.
  useEffect(() => {
    if (!location && user) {
      const fromProfile = locationFromProfile(user);
      if (fromProfile) setLocation(fromProfile);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const value = useMemo(
    () => ({ location, loading, error, refresh, setManual }),
    [location, loading, error, refresh, setManual],
  );

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

/** Backwards-compatible hook: pages keep calling useLocation({ autoAsk }). */
export default function useLocation(_options) {
  return useContext(LocationContext);
}
