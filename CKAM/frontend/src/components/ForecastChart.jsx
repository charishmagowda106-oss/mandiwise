import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import api from '../services/api';
import { useLanguage } from '../i18n';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const monthLabel = iso => new Date(iso).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
const dayLabel = iso => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

// One graph with the two-year history (solid) and the future predictions
// (dashed), so the forecast is always read against the past trend.
export default function ForecastChart({ cropId, mandiId, daysAhead }) {
  const { t } = useLanguage();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!cropId || !mandiId) return undefined;
    let alive = true;
    setRows(null);
    setError('');
    Promise.all([
      api.get('/prices/history', { params: { crop_id: cropId, mandi_id: mandiId } }),
      api.post('/predict/forecast', {
        crop_id: Number(cropId),
        mandi_id: Number(mandiId),
        days_ahead: Number(daysAhead) || 7,
      }),
    ])
      .then(([historyRes, forecastRes]) => {
        if (!alive) return;
        const history = (historyRes.data.points || []).map(point => ({
          label: monthLabel(point.date),
          history: point.modal_price,
        }));
        // bridge: today's current price, then each future day's prediction
        const forecast = [{ label: t('pred.chartToday'), forecast: forecastRes.data.current_price }];
        (forecastRes.data.points || []).forEach(point => {
          forecast.push({ label: dayLabel(point.date), forecast: point.predicted_price });
        });
        setRows([...history, ...forecast]);
      })
      .catch(() => { if (alive) setError(t('pred.chartError')); });
    return () => { alive = false; };
  }, [cropId, mandiId, daysAhead, t]);

  return (
    <section className="mw-panel p-6">
      <h2 className="text-2xl font-bold">{t('pred.chartTitle')}</h2>
      <p className="mt-1 text-sm text-gray-500">{t('pred.chartSub')}</p>

      {error && <p className="mt-4 rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}
      {!error && rows === null && (
        <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-4 text-gray-600">{t('pred.chartLoading')}</p>
      )}
      {!error && rows && rows.length > 0 && (
        <div className="mt-5 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12, fill: '#6b7280' }}
                interval="preserveStartEnd"
                minTickGap={24}
              />
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
              <Line
                type="linear"
                dataKey="history"
                name={t('pred.chartHistory')}
                stroke="#197638"
                strokeWidth={3}
                connectNulls={false}
                isAnimationActive={false}
                dot={{ r: 2.5, fill: '#197638', strokeWidth: 0 }}
              />
              <Line
                type="linear"
                dataKey="forecast"
                name={t('pred.chartForecast')}
                stroke="#d97706"
                strokeWidth={3}
                strokeDasharray="7 5"
                connectNulls={false}
                isAnimationActive={false}
                dot={{ r: 3, fill: '#d97706', strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
