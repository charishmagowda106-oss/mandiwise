import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { TrendingUp, Clock, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function PricePrediction() {
  const [crops, setCrops] = useState([]), [mandis, setMandis] = useState([]);
  const [form, setForm] = useState({ crop_id: '', mandi_id: '', days_ahead: 7 });
  const [result, setResult] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')]).then(([cRes, mRes]) => {
      setCrops(cRes.data); setMandis(mRes.data);
      if (cRes.data.length) setForm(f => ({...f, crop_id:cRes.data[0].id}));
      if (mRes.data.length) setForm(f => ({...f, mandi_id:mRes.data[0].id}));
    }).catch(() => setError('Could not load market data. Make sure the backend is running.'));
  }, []);

  const handlePredict = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try { const res = await api.post('/predict/', {crop_id:Number(form.crop_id), mandi_id:Number(form.mandi_id), days_ahead:Number(form.days_ahead)}); setResult(res.data); }
    catch { setError('Prediction failed. This crop and mandi may not have price history.'); }
    finally { setLoading(false); }
  };

  return <div className="space-y-8">
    <header><p className="font-semibold text-[#197638]">When to sell</p><h1 className="mt-2 text-4xl font-bold tracking-tight">Predict crop price</h1><p className="mt-3 text-gray-600">Use the project’s trained Random Forest model to estimate a future modal price.</p></header>
    <form onSubmit={handlePredict} className="mw-panel grid gap-5 p-6 md:grid-cols-3 md:p-8">
      <div><label className="mw-label">Crop</label><select required value={form.crop_id} onChange={e=>setForm({...form,crop_id:e.target.value})} className="mw-input">{crops.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
      <div><label className="mw-label">Mandi</label><select required value={form.mandi_id} onChange={e=>setForm({...form,mandi_id:e.target.value})} className="mw-input">{mandis.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></div>
      <div><label className="mw-label">Forecast horizon (days)</label><input required min="1" max="365" type="number" value={form.days_ahead} onChange={e=>setForm({...form,days_ahead:e.target.value})} className="mw-input"/></div>
      <button disabled={loading || !form.crop_id || !form.mandi_id} type="submit" className="mw-button md:col-span-3"><TrendingUp className="h-5 w-5"/>{loading ? 'Calculating…' : 'Predict Future Price'}</button>
    </form>
    {error && <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}
    {result && <section className="grid gap-5 md:grid-cols-2">
      <div className="mw-panel p-7"><p className="flex items-center gap-2 text-gray-500"><TrendingUp className="h-5 w-5"/>Current stored price</p><p className="mt-3 text-4xl font-bold">₹{money(result.current_price)}<span className="text-lg font-medium text-gray-500">/quintal</span></p></div>
      <div className="mw-panel border-[#91b49a] bg-[#f1f6ea] p-7"><p className="flex items-center gap-2 text-gray-500"><Clock className="h-5 w-5"/>Predicted price ({form.days_ahead} days)</p><p className="mt-3 text-4xl font-bold">₹{money(result.predicted_price)}</p><p className={`mt-3 flex items-center gap-1 font-bold ${result.expected_change_percent >= 0 ? 'text-green-700' : 'text-red-700'}`}>{result.expected_change_percent >= 0 ? <ArrowUpRight className="h-5 w-5"/> : <ArrowDownRight className="h-5 w-5"/>}{result.expected_change_percent}%</p></div>
      <p className="text-sm text-gray-500 md:col-span-2">{result.disclaimer}</p>
    </section>}
  </div>;
}
