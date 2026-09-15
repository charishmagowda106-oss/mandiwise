import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { MapPin, Search, Trophy, Truck, IndianRupee } from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function MandiCompare() {
  const [crops, setCrops] = useState([]);
  const [form, setForm] = useState({ crop_id: '', quantity: 10, unit: 'quintal', lat: 20.0, lng: 78.0, transport_rate_per_km: 10.0 });
  const [results, setResults] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState('');

  useEffect(() => {
    api.get('/crops/').then(res => {
      setCrops(res.data);
      if (res.data.length) setForm(f => ({ ...f, crop_id: res.data[0].id }));
    }).catch(() => setError('Could not load crops. Make sure the backend is running.'));
  }, []);

  const handleCompare = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const res = await api.post('/recommendations/compare', { ...form, crop_id: Number(form.crop_id), quantity: Number(form.quantity), lat: Number(form.lat), lng: Number(form.lng), transport_rate_per_km: Number(form.transport_rate_per_km) });
      setResults(res.data);
    } catch { setError('Mandi comparison failed. Check your values and backend connection.'); }
    finally { setLoading(false); }
  };

  return <div className="space-y-8">
    <header><p className="font-semibold text-[#197638]">Where to sell</p><h1 className="mt-2 text-4xl font-bold tracking-tight">Find your best mandi</h1><p className="mt-3 text-gray-600">Comparison uses current stored prices, straight-line distance, and your transport rate.</p></header>
    <form onSubmit={handleCompare} className="mw-panel grid gap-5 p-6 md:grid-cols-2 md:p-8">
      <div><label className="mw-label">Crop</label><select required value={form.crop_id} onChange={e => setForm({...form, crop_id:e.target.value})} className="mw-input">{crops.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <div><label className="mw-label">Quantity</label><div className="flex gap-2"><input required min="0.01" step="0.01" type="number" value={form.quantity} onChange={e => setForm({...form, quantity:e.target.value})} className="mw-input"/><select value={form.unit} onChange={e => setForm({...form, unit:e.target.value})} className="mw-input max-w-32"><option value="quintal">Quintal</option><option value="kg">Kg</option></select></div></div>
      <div><label className="mw-label">Latitude</label><input required min="-90" max="90" step="any" type="number" value={form.lat} onChange={e => setForm({...form, lat:e.target.value})} className="mw-input"/></div>
      <div><label className="mw-label">Longitude</label><input required min="-180" max="180" step="any" type="number" value={form.lng} onChange={e => setForm({...form, lng:e.target.value})} className="mw-input"/></div>
      <div><label className="mw-label">Transport rate (₹/km)</label><input required min="0" step="0.01" type="number" value={form.transport_rate_per_km} onChange={e => setForm({...form, transport_rate_per_km:e.target.value})} className="mw-input"/></div>
      <div className="flex items-end"><button disabled={loading || !form.crop_id} className="mw-button w-full" type="submit"><Search className="h-5 w-5" />{loading ? 'Comparing…' : 'Find Best Mandi'}</button></div>
    </form>
    {error && <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}
    {results && <section className="space-y-4"><h2 className="text-2xl font-bold">Ranked results</h2>{results.length === 0 && <p className="mw-panel p-6 text-gray-600">No matching price data was found.</p>}{results.map(r => <article key={r.mandi_id} className={`rounded-3xl border p-6 shadow-sm ${r.rank === 1 ? 'border-[#79ac85] bg-[#f1f6ea]' : 'border-[#d8d8ca] bg-white'}`}>
      <div className="flex flex-col justify-between gap-5 sm:flex-row"><div><div className="flex items-center gap-2 text-sm font-bold text-[#197638]">{r.rank === 1 ? <Trophy className="h-5 w-5 text-amber-500"/> : `#${r.rank}`} {r.recommendation}</div><h3 className="mt-2 text-2xl font-bold">{r.mandi_name}</h3><p className="mt-2 flex items-center gap-2 text-gray-500"><MapPin className="h-4 w-4"/>{r.distance_km} km away</p></div><div className="sm:text-right"><p className="text-sm text-gray-500">Estimated selling return</p><p className="text-3xl font-bold text-[#197638]">₹{money(r.estimated_profit)}</p></div></div>
      <div className="mt-6 grid gap-3 border-t border-[#dce5d7] pt-5 text-sm sm:grid-cols-3"><p className="flex items-center gap-2"><IndianRupee className="h-4 w-4"/>₹{money(r.current_price)}/quintal</p><p>Gross ₹{money(r.expected_revenue)}</p><p className="flex items-center gap-2"><Truck className="h-4 w-4"/>Transport ₹{money(r.transport_cost)}</p></div>
    </article>)}</section>}
  </div>;
}
