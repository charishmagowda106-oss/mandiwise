import React, { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import useLocation from '../hooks/useLocation';
import { MapPin, Navigation, Sprout, Store, Search, TrendingUp, ArrowRight } from 'lucide-react';

const coordinate = value => {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(4) : 'Not set';
};

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState({ crops: 0, mandis: 0 });
  const [error, setError] = useState('');
  const { location, loading: locating, error: locError, refresh } = useLocation({ autoAsk: true });

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')])
      .then(([cropsRes, mandisRes]) => setStats({ crops: cropsRes.data.length, mandis: mandisRes.data.length }))
      .catch(() => setError('Could not load market data. Make sure the backend is running.'));
  }, []);

  return (
    <div className="space-y-8">
      <section>
        <p className="mb-2 font-semibold text-[#197638]">Your market overview</p>
        <h1 className="text-4xl font-bold tracking-tight text-[#15261a] sm:text-5xl">Namaste, {user?.name?.split(' ')[0]} <span aria-hidden="true">🌾</span></h1>
        <p className="mt-3 max-w-2xl text-lg text-gray-600">Check official Karnataka mandi rates, then use the demo forecast tools to explore selling decisions.</p>
      </section>

      <section className="mw-panel flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-[#e9f4e9] p-3 text-[#197638]"><MapPin className="h-6 w-6" /></div>
          <div>
            <h2 className="font-bold text-[#1c2b20]">Your current location</h2>
            <p className="mt-1 text-gray-500">
              {location
                ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}${location.accuracy ? ` (±${Math.round(location.accuracy)} m)` : ''}`
                : user?.location_lat != null
                  ? `Saved: ${coordinate(user.location_lat)}, ${coordinate(user.location_lng)}`
                  : 'Not set yet — allow location when your browser asks.'}
            </p>
            {locError && <p className="mt-1 text-sm text-red-600">{locError}</p>}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={refresh} disabled={locating} className="mw-button-soft">
            <Navigation className={`h-5 w-5 ${locating ? 'animate-pulse' : ''}`} />
            {locating ? 'Locating…' : location ? 'Update location' : 'Use my current location'}
          </button>
          <Link to="/compare" className="mw-button"><Search className="h-5 w-5" />Find mandis near me</Link>
        </div>
      </section>

      {error && <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}

      <section className="grid gap-5 sm:grid-cols-2">
        <div className="mw-panel p-6"><Sprout className="mb-5 h-7 w-7 text-[#197638]" /><p className="text-gray-500">Available crops</p><p className="mt-1 text-4xl font-bold">{stats.crops}</p></div>
        <div className="mw-panel p-6"><Store className="mb-5 h-7 w-7 text-[#197638]" /><p className="text-gray-500">Real Karnataka mandis</p><p className="mt-1 text-4xl font-bold">{stats.mandis}</p></div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link to="/compare" className="group flex min-h-40 items-center justify-between rounded-3xl bg-[#197638] p-7 text-white shadow-sm">
          <div><Search className="mb-5 h-7 w-7" /><h2 className="text-2xl font-bold">Live Karnataka Rates</h2><p className="mt-2 text-green-100">View official market prices for a selected crop.</p></div><ArrowRight className="h-6 w-6 transition group-hover:translate-x-1" />
        </Link>
        <Link to="/predict" className="group flex min-h-40 items-center justify-between rounded-3xl bg-[#e9ecd7] p-7 text-[#18351f] shadow-sm">
          <div><TrendingUp className="mb-5 h-7 w-7" /><h2 className="text-2xl font-bold">Predict Crop Price</h2><p className="mt-2 text-[#526456]">Forecast with the trained ML model.</p></div><ArrowRight className="h-6 w-6 transition group-hover:translate-x-1" />
        </Link>
      </section>
    </div>
  );
}
