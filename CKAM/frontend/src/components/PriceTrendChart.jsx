import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import api from '../services/api';
import { useLanguage } from '../i18n';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const monthLabel = iso => new Date(iso).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });

// Two-year monthly trend as a straight-line graph (min/max thin dashed, modal bold).
export default function PriceTrendChart({ cropId, mandis }) {
  const { t } = useLanguage();
  const [mandiId, setMandiId] = useState('');
  const [points, setPoints] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (mandis.length && !mandis.some(m => String(m.id) === String(mandiId))) {
      setMandiId(String(mandis[0].id));
    }
  }, [mandis]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!cropId || !mandiId) return undefined;
    let alive = true;
    setPoints(null);
    setError('');
    api
      .get('/prices/history', { params: { crop_id: cropId, mandi_id: mandiId } })
      .then(res => { if (alive) setPoints(res.data.points || []); })
      .catch(() => { if (alive) setError(t('cmp.trendError')); });
    return () => { alive = false; };
  }, [cropId, mandiId, t]);

  if (!mandis.length) return null;

  const chartData = (points || []).map(p => ({
    ...p,
    label: monthLabel(p.date),
  }));

  return (
    <section className="mw-panel p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold">{t('cmp.trendTitle')}</h2>
          <p className="mt-1 text-sm text-gray-500">{t('cmp.trendSub')}</p>
        </div>
        <div className="min-w-48">
          <label htmlFor="trend-mandi" className="mw-label">{t('cmp.trendMandi')}</label>
          <select
            id="trend-mandi"
            value={mandiId}
            onChange={event => setMandiId(event.target.value)}
            className="mw-input"
          >
            {mandis.map(mandi => (
              <option key={mandi.id} value={mandi.id}>{mandi.name}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="mt-4 rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}
      {!error && points === null && (
        <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-4 text-gray-600">{t('cmp.trendLoading')}</p>
      )}
      {!error && points !== null && chartData.length === 0 && (
        <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-4 text-gray-600">{t('cmp.trendEmpty')}</p>
      )}
      {!error && chartData.length > 0 && (
        <div className="mt-5 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#6b7280' }} />
              <YAxis
                tick={{ fontSize: 12, fill: '#6b7280' }}
                tickFormatter={value => `₹${money(value)}`}
                width={72}
              />
              <Tooltip
                formatter={(value, name) => [`₹${money(value)}`, name]}
                contentStyle={{ borderRadius: 12, borderColor: '#dedfce' }}
              />
              <Legend wrapperStyle={{ fontSize: 13 }} />
              <Line type="linear" isAnimationActive={false} dataKey="modal_price" name={t('cmp.trendModal')} stroke="#197638" strokeWidth={3} dot={{ r: 2.5, fill: '#197638', strokeWidth: 0 }} />
              <Line type="linear" isAnimationActive={false} dataKey="max_price" name={t('cmp.trendMax')} stroke="#9ca3af" strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
              <Line type="linear" isAnimationActive={false} dataKey="min_price" name={t('cmp.trendMin')} stroke="#9ca3af" strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
