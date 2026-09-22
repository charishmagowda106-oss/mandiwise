import { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import {
  hasAskedLocation,
  markLocationAsked,
  readStoredLocation,
  requestCurrentLocation,
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

/**
 * Farmer's current location. Stores it locally, mirrors it onto the profile,
 * and (optionally) asks the browser once on first ever visit.
 */
export default function useLocation({ autoAsk = false } = {}) {
  const { user, updateProfile } = useContext(AuthContext);
  const [location, setLocation] = useState(() => readStoredLocation() ?? locationFromProfile(user));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (inFlight.current) return; // one geolocation request at a time
    inFlight.current = true;
    setLoading(true);
    setError('');
    try {
      const fresh = await requestCurrentLocation();
      setLocation(fresh);
      markLocationAsked();
      if (updateProfile) {
        Promise.resolve(
          updateProfile({ location_lat: fresh.lat, location_lng: fresh.lng }),
        ).catch(() => {
          /* saving the profile location is best-effort */
        });
      }
    } catch (err) {
      setError(err?.message || 'Could not read your location.');
      markLocationAsked();
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }, [updateProfile]);

  useEffect(() => {
    if (!autoAsk || location || hasAskedLocation()) return;
    refresh();
  }, [autoAsk, location, refresh]);

  return { location, loading, error, refresh };
}
