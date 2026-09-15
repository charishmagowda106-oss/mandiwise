import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

dashboard_jsx = """
import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({ crops: 0, mandis: 0 });

  useEffect(() => {
    const fetchData = async () => {
      const [cropsRes, mandisRes] = await Promise.all([
        api.get('/crops/'),
        api.get('/mandis/')
      ]);
      setStats({
        crops: cropsRes.data.length,
        mandis: mandisRes.data.length
      });
    };
    fetchData();
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
          <h3 className="text-gray-500 font-medium">Available Crops</h3>
          <p className="text-3xl font-bold text-agrigreen-600">{stats.crops}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border border-gray-100">
          <h3 className="text-gray-500 font-medium">Available Mandis</h3>
          <p className="text-3xl font-bold text-agrigreen-600">{stats.mandis}</p>
        </div>
      </div>
      <div className="mt-8 p-6 bg-green-50 rounded-lg">
        <h3 className="text-xl font-semibold mb-2">Welcome to MandiWise</h3>
        <p className="text-gray-700">Use the navigation menu to find the best mandi for your crop or predict future prices using our Machine Learning engine.</p>
      </div>
    </div>
  );
}
"""
write_file('frontend/src/pages/Dashboard.jsx', dashboard_jsx)

compare_jsx = """
import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function MandiCompare() {
  const [crops, setCrops] = useState([]);
  const [form, setForm] = useState({ crop_id: '', quantity: 10, unit: 'quintal', lat: 20.0, lng: 78.0, transport_rate_per_km: 10.0 });
  const [results, setResults] = useState(null);

  useEffect(() => {
    api.get('/crops/').then(res => {
      setCrops(res.data);
      if(res.data.length > 0) setForm(f => ({...f, crop_id: res.data[0].id}));
    });
  }, []);

  const handleCompare = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/recommendations/compare', {
        ...form,
        crop_id: parseInt(form.crop_id),
        quantity: parseFloat(form.quantity),
        transport_rate_per_km: parseFloat(form.transport_rate_per_km)
      });
      setResults(res.data);
    } catch (err) {
      alert("Error comparing mandis");
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Where should I sell?</h2>
      <div className="bg-white p-6 rounded shadow mb-6">
        <form onSubmit={handleCompare} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Crop</label>
            <select value={form.crop_id} onChange={e=>setForm({...form, crop_id: e.target.value})} className="mt-1 block w-full border p-2 rounded">
              {crops.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Quantity</label>
            <div className="flex gap-2 mt-1">
              <input type="number" value={form.quantity} onChange={e=>setForm({...form, quantity: e.target.value})} className="border p-2 rounded w-full" />
              <select value={form.unit} onChange={e=>setForm({...form, unit: e.target.value})} className="border p-2 rounded">
                <option value="quintal">Quintal</option>
                <option value="kg">Kg</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium">Transport Rate (₹/km)</label>
            <input type="number" value={form.transport_rate_per_km} onChange={e=>setForm({...form, transport_rate_per_km: e.target.value})} className="mt-1 block w-full border p-2 rounded" />
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button type="submit" className="bg-agrigreen-600 text-white px-6 py-2 rounded hover:bg-agrigreen-700">Find Best Mandi</button>
          </div>
        </form>
      </div>

      {results && (
        <div>
          <h3 className="text-xl font-bold mb-4">Results</h3>
          <div className="space-y-4">
            {results.map((r, idx) => (
              <div key={idx} className={`p-4 rounded border ${r.rank === 1 ? 'border-green-500 bg-green-50' : 'bg-white'}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-lg">{r.mandi_name} {r.rank === 1 && <span className="text-xs bg-green-500 text-white px-2 py-1 rounded ml-2">BEST MANDI</span>}</h4>
                    <p className="text-sm text-gray-600">Distance: {r.distance_km} km</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Est. Profit</p>
                    <p className="text-xl font-bold text-green-700">₹{r.estimated_profit}</p>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2 text-sm text-gray-600 border-t pt-2">
                  <div>Price: ₹{r.current_price}/q</div>
                  <div>Revenue: ₹{r.expected_revenue}</div>
                  <div>Transport: -₹{r.transport_cost}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
"""
write_file('frontend/src/pages/MandiCompare.jsx', compare_jsx)

predict_jsx = """
import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function PricePrediction() {
  const [crops, setCrops] = useState([]);
  const [mandis, setMandis] = useState([]);
  const [form, setForm] = useState({ crop_id: '', mandi_id: '', days_ahead: 7 });
  const [result, setResult] = useState(null);

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')]).then(([cRes, mRes]) => {
      setCrops(cRes.data);
      setMandis(mRes.data);
      if(cRes.data.length > 0) setForm(f => ({...f, crop_id: cRes.data[0].id}));
      if(mRes.data.length > 0) setForm(f => ({...f, mandi_id: mRes.data[0].id}));
    });
  }, []);

  const handlePredict = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/predict/', {
        crop_id: parseInt(form.crop_id),
        mandi_id: parseInt(form.mandi_id),
        days_ahead: parseInt(form.days_ahead)
      });
      setResult(res.data);
    } catch (err) {
      alert("Error predicting price");
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Price Prediction Engine</h2>
      <div className="bg-white p-6 rounded shadow mb-6">
        <form onSubmit={handlePredict} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium">Crop</label>
            <select value={form.crop_id} onChange={e=>setForm({...form, crop_id: e.target.value})} className="mt-1 block w-full border p-2 rounded">
              {crops.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Mandi</label>
            <select value={form.mandi_id} onChange={e=>setForm({...form, mandi_id: e.target.value})} className="mt-1 block w-full border p-2 rounded">
              {mandis.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Forecast Horizon (Days)</label>
            <input type="number" value={form.days_ahead} onChange={e=>setForm({...form, days_ahead: e.target.value})} className="mt-1 block w-full border p-2 rounded" />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <button type="submit" className="bg-agrigreen-600 text-white px-6 py-2 rounded hover:bg-agrigreen-700">Predict Future Price</button>
          </div>
        </form>
      </div>

      {result && (
        <div className="bg-white p-6 rounded shadow border border-gray-200">
          <h3 className="text-xl font-bold mb-4">Prediction Results</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-50 p-4 rounded text-center">
              <p className="text-gray-500 text-sm">Current Price</p>
              <p className="text-2xl font-bold">₹{result.current_price}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded text-center">
              <p className="text-blue-600 text-sm">Predicted Price ({form.days_ahead} days)</p>
              <p className="text-2xl font-bold text-blue-700">₹{result.predicted_price}</p>
            </div>
          </div>
          <div className="text-center mb-4">
            <span className={`px-4 py-2 rounded-full font-bold ${result.expected_change_percent >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              Expected Change: {result.expected_change_percent >= 0 ? '+' : ''}{result.expected_change_percent}%
            </span>
          </div>
          <p className="text-xs text-gray-500 text-center italic">{result.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
"""
write_file('frontend/src/pages/PricePrediction.jsx', predict_jsx)
