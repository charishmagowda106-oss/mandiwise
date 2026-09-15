import React, { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import { MapPin, Navigation, Sprout, Store, Search, TrendingUp, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState({ crops: 0, mandis: 0 });
  const [error, setError] = useState('');

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
        <p className="mt-3 max-w-2xl text-lg text-gray-600">Make a clearer selling decision using market prices, distance, transport cost and ML forecasts.</p>
      </section>

      <section className="mw-panel flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-[#e9f4e9] p-3 text-[#197638]"><MapPin className="h-6 w-6" /></div>
          <div><h2 className="font-bold text-[#1c2b20]">Saved farm location</h2><p className="mt-1 text-gray-500">{user?.location_lat?.toFixed(4) ?? 'Not set'}, {user?.location_lng?.toFixed(4) ?? 'Not set'}</p></div>
        </div>
        <Link to="/compare" className="mw-button-soft"><Navigation className="h-5 w-5" />Use for mandi search</Link>
      </section>

      {error && <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}

      <section className="grid gap-5 sm:grid-cols-2">
        <div className="mw-panel p-6"><Sprout className="mb-5 h-7 w-7 text-[#197638]" /><p className="text-gray-500">Available crops</p><p className="mt-1 text-4xl font-bold">{stats.crops}</p></div>
        <div className="mw-panel p-6"><Store className="mb-5 h-7 w-7 text-[#197638]" /><p className="text-gray-500">Available mandis</p><p className="mt-1 text-4xl font-bold">{stats.mandis}</p></div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link to="/compare" className="group flex min-h-40 items-center justify-between rounded-3xl bg-[#197638] p-7 text-white shadow-sm">
          <div><Search className="mb-5 h-7 w-7" /><h2 className="text-2xl font-bold">Find Best Mandi</h2><p className="mt-2 text-green-100">Rank markets by your estimated return.</p></div><ArrowRight className="h-6 w-6 transition group-hover:translate-x-1" />
        </Link>
        <Link to="/predict" className="group flex min-h-40 items-center justify-between rounded-3xl bg-[#e9ecd7] p-7 text-[#18351f] shadow-sm">
          <div><TrendingUp className="mb-5 h-7 w-7" /><h2 className="text-2xl font-bold">Predict Crop Price</h2><p className="mt-2 text-[#526456]">Forecast with the trained ML model.</p></div><ArrowRight className="h-6 w-6 transition group-hover:translate-x-1" />
        </Link>
      </section>
    </div>
  );
}
