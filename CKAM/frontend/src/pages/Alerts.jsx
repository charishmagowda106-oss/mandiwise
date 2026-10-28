import React, { useEffect, useState, useContext } from 'react';
import api, { getApiErrorMessage } from '../services/api';
import useLocation from '../hooks/useLocation';
import { AuthContext } from '../context/AuthContext';
import { useLanguage } from '../i18n';
import {
  BellRing, BellOff, MapPin, Navigation, PlusCircle, RefreshCw, Trash2, CheckCircle2,
} from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const formatStamp = value => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
};

export default function Alerts() {
  const { t } = useLanguage();
  const { user } = useContext(AuthContext);
  const { location, loading: locating, error: locError, refresh } = useLocation({ autoAsk: true });

  const [crops, setCrops] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [cropId, setCropId] = useState('');
  const [quantity, setQuantity] = useState('10');
  const [minProfit, setMinProfit] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [checkResults, setCheckResults] = useState({}); // alertId -> message

  const load = async () => {
    try {
      const [cropsRes, alertsRes] = await Promise.all([api.get('/crops/'), api.get('/alerts')]);
      setCrops(cropsRes.data);
      if (!cropId && cropsRes.data.length) setCropId(String(cropsRes.data[0].id));
      setAlerts(alertsRes.data);
    } catch (err) {
      setError(getApiErrorMessage(err, t('err.cropsMandis')));
    }
  };

  useEffect(() => { load(); /* eslint-disable-line */ }, []);

  const locationReady = Boolean(location) || (user?.location_lat != null && user?.location_lng != null);

  const handleCreate = async event => {
    event.preventDefault();
    setError('');
    setNotice('');
    setSubmitting(true);
    try {
      await api.post('/alerts', {
        crop_id: Number(cropId),
        quantity: Number(quantity) || 1,
        unit: 'quintal',
        lat: location?.lat ?? user?.location_lat ?? null,
        lng: location?.lng ?? user?.location_lng ?? null,
        transport_rate_per_km: 10,
        min_profit: minProfit.trim() === '' ? null : Number(minProfit),
      });
      setNotice(t('alert.created'));
      setMinProfit('');
      await load();
    } catch (err) {
      setError(getApiErrorMessage(err, t('alert.createError')));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActive = async alert => {
    try {
      const res = await api.patch(`/alerts/${alert.id}`, { active: !alert.active });
      setAlerts(prev => prev.map(item => (item.id === alert.id ? res.data : item)));
    } catch (err) {
      setError(getApiErrorMessage(err, t('alert.createError')));
    }
  };

  const removeAlert = async alert => {
    try {
      await api.delete(`/alerts/${alert.id}`);
      setAlerts(prev => prev.filter(item => item.id !== alert.id));
    } catch (err) {
      setError(getApiErrorMessage(err, t('alert.createError')));
    }
  };

  const checkNow = async alert => {
    setCheckResults(prev => ({ ...prev, [alert.id]: t('alert.checking') }));
    try {
      const res = await api.post(`/alerts/${alert.id}/check`);
      const data = res.data;
      const message = data.notified
        ? t('alert.checkNotified', { profit: money(data.last_best_profit ?? 0) })
        : data.last_best_profit == null
          ? t('alert.checkNoData')
          : t('alert.checkWatching', { profit: money(data.last_best_profit) });
      setCheckResults(prev => ({ ...prev, [alert.id]: message }));
      await load();
    } catch (err) {
      setCheckResults(prev => ({ ...prev, [alert.id]: getApiErrorMessage(err, t('alert.createError')) }));
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <p className="font-semibold text-[#197638]">{t('alert.kicker')}</p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">{t('alert.title')}</h1>
        <p className="mt-3 text-gray-600">{t('alert.sub')}</p>
      </header>

      {/* Create alert */}
      <form onSubmit={handleCreate} className="mw-panel grid gap-5 p-6 md:p-8">
        <h2 className="text-xl font-bold">{t('alert.newTitle')}</h2>
        {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">{error}</p>}
        {notice && <p className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">{notice}</p>}
        <div className="grid gap-5 md:grid-cols-3 md:items-end">
          <div>
            <label htmlFor="alert-crop" className="mw-label">{t('cmp.crop')}</label>
            <select id="alert-crop" value={cropId} onChange={event => setCropId(event.target.value)} className="mw-input">
              {crops.map(crop => <option key={crop.id} value={crop.id}>{crop.name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="alert-qty" className="mw-label">{t('cmp.load')}</label>
            <input id="alert-qty" type="number" min="1" step="1" value={quantity} onChange={event => setQuantity(event.target.value)} className="mw-input" />
          </div>
          <div>
            <label htmlFor="alert-minprofit" className="mw-label">{t('alert.minProfit')}</label>
            <input id="alert-minprofit" type="number" min="0" step="50" value={minProfit} onChange={event => setMinProfit(event.target.value)} placeholder={t('alert.anyProfit')} className="mw-input" />
            <p className="mt-1 text-xs text-gray-500">{t('alert.minProfitHint')}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-[#f6f5ea] px-4 py-3">
          <div className="flex items-start gap-2 text-sm text-gray-600">
            <MapPin className="mt-0.5 h-4 w-4 text-[#197638]" />
            <span>
              {location
                ? t('loc.saved', { coords: `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` })
                : locationReady ? t('loc.saved', { coords: `${user?.location_lat?.toFixed?.(4)}, ${user?.location_lng?.toFixed?.(4)}` }) : t('loc.notsetCompare')}
              {locError && <span className="block text-red-600">{locError}</span>}
            </span>
          </div>
          <button type="button" onClick={refresh} disabled={locating} className="mw-button-soft">
            <Navigation className={`h-4 w-4 ${locating ? 'animate-pulse' : ''}`} />
            {locating ? t('loc.locating') : location ? t('loc.update') : t('loc.use')}
          </button>
        </div>

        <button type="submit" disabled={submitting || !cropId} className="mw-button justify-self-start">
          <PlusCircle className="h-5 w-5" />
          {submitting ? t('alert.creating') : t('alert.create')}
        </button>
      </form>

      {/* Existing alerts */}
      <section>
        <h2 className="text-2xl font-bold">{t('alert.yours')}</h2>
        {alerts.length === 0 ? (
          <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-5 text-gray-600">{t('alert.none')}</p>
        ) : (
          <div className="mt-4 space-y-3">
            {alerts.map(alert => (
              <div key={alert.id} className="mw-panel p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="font-bold text-[#1c2b20]">
                      {alert.crop_name || `Crop #${alert.crop_id}`}
                      <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-semibold ${alert.active ? 'bg-[#e9f4e9] text-[#197638]' : 'bg-gray-100 text-gray-500'}`}>
                        {alert.active ? t('alert.active') : t('alert.paused')}
                      </span>
                    </p>
                    <p className="mt-1 text-sm text-gray-500">
                      {t('alert.meta', {
                        qty: alert.quantity,
                        target: alert.min_profit != null ? `≥ ₹${money(alert.min_profit)}` : t('alert.anyProfitShort'),
                      })}
                    </p>
                    {alert.last_best_profit != null && (
                      <p className="mt-1 text-sm text-[#197638]">
                        {t('alert.lastSeen', { profit: money(alert.last_best_profit) })}
                      </p>
                    )}
                    {alert.last_notified_at && (
                      <p className="mt-1 text-xs text-gray-400">
                        {t('alert.notifiedAt', { when: formatStamp(alert.last_notified_at) })}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => checkNow(alert)}
                      title={t('alert.check')}
                      className="flex items-center gap-2 rounded-xl border border-[#d8d8ca] px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-[#f4f2e8]"
                    >
                      <RefreshCw className="h-4 w-4" /> {t('alert.check')}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleActive(alert)}
                      title={alert.active ? t('alert.pause') : t('alert.resume')}
                      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-semibold ${alert.active ? 'border-[#d8d8ca] text-gray-700 hover:bg-[#f4f2e8]' : 'border-[#197638] bg-[#197638] text-white'}`}
                    >
                      {alert.active ? <BellOff className="h-4 w-4" /> : <BellRing className="h-4 w-4" />}
                      {alert.active ? t('alert.pause') : t('alert.resume')}
                    </button>
                    <button
                      type="button"
                      onClick={() => removeAlert(alert)}
                      title={t('alert.delete')}
                      className="rounded-xl border border-red-200 p-2 text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                {checkResults[alert.id] && (
                  <p className="mt-3 flex items-start gap-2 rounded-2xl bg-[#f6f5ea] px-4 py-3 text-sm text-gray-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#197638]" />
                    {checkResults[alert.id]}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
