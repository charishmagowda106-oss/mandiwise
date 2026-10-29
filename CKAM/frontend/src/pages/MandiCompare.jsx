import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api, { getApiErrorMessage } from '../services/api';
import useLocation from '../hooks/useLocation';
import { haversineKm, matchMarket, normalizeMarketName } from '../services/location';
import { useLanguage } from '../i18n';
import { MapPin, Navigation, IndianRupee, Radio, Store, Trophy, MessageCircle, BellRing, CheckCircle2 } from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const formatStamp = value => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
};

export default function MandiCompare() {
  const { t } = useLanguage();
  const [crops, setCrops] = useState([]);
  const [cropId, setCropId] = useState('');
  const [mandis, setMandis] = useState([]);
  const [quantity, setQuantity] = useState('10');
  const [liveResults, setLiveResults] = useState(null);
  const [ranked, setRanked] = useState([]);
  const [loadingLive, setLoadingLive] = useState(false);
  const [loadingRank, setLoadingRank] = useState(false);
  const [error, setError] = useState('');
  const [rankError, setRankError] = useState('');
  const [alertBusy, setAlertBusy] = useState(false);
  const [alertNotice, setAlertNotice] = useState('');
  const navigate = useNavigate();
  // Dashboard "Compare" links land here as /compare?crop=<id>&qty=<n> to prefill.
  const [searchParams] = useSearchParams();

  const { location, loading: locating, error: locError, refresh } = useLocation({ autoAsk: true });

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')])
      .then(([cropsRes, mandisRes]) => {
        setCrops(cropsRes.data);
        const paramCrop = searchParams.get('crop');
        const paramQty = searchParams.get('qty');
        const matched = paramCrop && cropsRes.data.some(item => String(item.id) === String(paramCrop));
        if (matched) setCropId(String(paramCrop));
        else if (cropsRes.data.length) setCropId(String(cropsRes.data[0].id));
        if (paramQty && Number(paramQty) > 0) setQuantity(String(paramQty));
        setMandis(mandisRes.data);
      })
      .catch(() => setError(getApiErrorMessage(null, t('err.cropsMandis'))));
  }, [t, searchParams]);

  const selectedCrop = crops.find(item => String(item.id) === String(cropId));

  const mandiIndex = useMemo(() => {
    const index = new Map();
    mandis.forEach(mandi => index.set(normalizeMarketName(mandi.name), mandi));
    return index;
  }, [mandis]);

  const nearest = useMemo(() => {
    if (!location) return [];
    return mandis
      .map(mandi => ({ ...mandi, distance_km: haversineKm(location, mandi) }))
      .filter(mandi => Number.isFinite(mandi.distance_km))
      .sort((a, b) => a.distance_km - b.distance_km)
      .slice(0, 8);
  }, [mandis, location]);

  const handleLive = async event => {
    event.preventDefault();
    setLoadingLive(true);
    setError('');
    setLiveResults(null);
    try {
      const res = await api.get('/live-prices/karnataka', {
        params: { commodity: selectedCrop?.name, limit: 100 },
      });
      const records = (res.data.records || []).map(record => {
        const mandi = matchMarket(record.mandi, mandiIndex);
        const distance_km = mandi && location ? haversineKm(location, mandi) : null;
        return { ...record, distance_km };
      });
      if (location) {
        records.sort((a, b) => (a.distance_km ?? 1e9) - (b.distance_km ?? 1e9));
      }
      setLiveResults({ ...res.data, records });
    } catch (err) {
      setError(getApiErrorMessage(err, t('err.live')));
    } finally {
      setLoadingLive(false);
    }
  };

  const handleRank = async () => {
    setRankError('');
    setRanked([]);
    if (!location) {
      setRankError(t('cmp.rankNoLoc'));
      return;
    }
    setLoadingRank(true);
    try {
      const res = await api.post('/recommendations/compare', {
        crop_id: Number(cropId),
        quantity: Number(quantity) || 1,
        unit: 'quintal',
        lat: location.lat,
        lng: location.lng,
        transport_rate_per_km: 10,
      });
      setRanked(res.data);
    } catch (err) {
      setRankError(getApiErrorMessage(err, t('err.rank')));
    } finally {
      setLoadingRank(false);
    }
  };

  // Watch this deal: creates a price alert prefilled from the current ranking.
  const best = ranked[0];
  const createQuickAlert = async () => {
    if (!best || !location) return;
    setAlertBusy(true);
    setAlertNotice('');
    try {
      const target = Math.floor((best.estimated_profit * 0.95) / 50) * 50; // ~current best, rounded down
      await api.post('/alerts', {
        crop_id: Number(cropId),
        quantity: Number(quantity) || 1,
        unit: 'quintal',
        lat: location.lat,
        lng: location.lng,
        transport_rate_per_km: 10,
        min_profit: Math.max(target, 0),
      });
      setAlertNotice(t('cmp.alertCreated', { amount: money(Math.max(target, 0)) }));
    } catch (err) {
      setAlertNotice(getApiErrorMessage(err, t('cmp.alertError')));
    } finally {
      setAlertBusy(false);
    }
  };

  // One tap shares the full recommendation on WhatsApp.
  const shareUrl = row => {    const lines = [
      `🌾 MandiWise — ${selectedCrop?.name ?? ''}`,
      `Best mandi: ${row.mandi_name} (${(row.distance_km ?? 0).toFixed(1)} km)`,
      `Price: ₹${money(row.current_price)}/quintal`,
      `Transport: ₹${money(row.transport_cost)}`,
      `Estimated profit: ₹${money(row.estimated_profit)}`,
      typeof window !== 'undefined' ? window.location.origin : '',
    ].filter(Boolean);
    return `https://wa.me/?text=${encodeURIComponent(lines.join('\n'))}`;
  };

  return (
    <div className="space-y-8">
      <header>
        <p className="font-semibold text-[#197638]">{t('cmp.kicker')}</p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">{t('cmp.title')}</h1>
        <p className="mt-3 text-gray-600">{t('cmp.sub')}</p>
      </header>

      {/* Farmer's current location */}
      <section className="mw-panel flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-[#e9f4e9] p-3 text-[#197638]"><MapPin className="h-6 w-6" /></div>
          <div>
            <p className="font-bold text-[#1c2b20]">{t('loc.title')}</p>
            <p className="text-sm text-gray-500">
              {location
                ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}${location.accuracy ? ` (±${Math.round(location.accuracy)} m)` : ''}`
                : t('loc.notsetCompare')}
            </p>
            {locError && <p className="mt-1 text-sm text-red-600">{locError}</p>}
          </div>
        </div>
        <button type="button" onClick={refresh} disabled={locating} className="mw-button-soft">
          <Navigation className={`h-5 w-5 ${locating ? 'animate-pulse' : ''}`} />
          {locating ? t('loc.locating') : location ? t('loc.update') : t('loc.use')}
        </button>
      </section>

      {/* Nearest real mandis */}
      {location && nearest.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold">{t('cmp.nearby')}</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {nearest.map(mandi => (
              <div key={mandi.id} className="mw-panel p-5">
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full bg-[#e9f4e9] px-2.5 py-1 text-xs font-semibold text-[#197638]">
                    {mandi.distance_km.toFixed(1)} km
                  </span>
                  <Store className="h-5 w-5 text-[#197638]" />
                </div>
                <p className="mt-3 font-bold text-[#1c2b20]">{mandi.name}</p>
                <p className="text-sm text-gray-500">{mandi.district} district</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Controls */}
      <form onSubmit={handleLive} className="mw-panel grid gap-5 p-6 md:p-8">
        <div className="grid gap-5 md:grid-cols-3 md:items-end">
          <div>
            <label htmlFor="compare-crop" className="mw-label">{t('cmp.crop')}</label>
            <select
              id="compare-crop"
              value={cropId}
              onChange={event => setCropId(event.target.value)}
              className="mw-input"
            >
              {crops.map(crop => (
                <option key={crop.id} value={crop.id}>{crop.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="compare-quantity" className="mw-label">{t('cmp.load')}</label>
            <input
              id="compare-quantity"
              type="number"
              min="1"
              step="1"
              value={quantity}
              onChange={event => setQuantity(event.target.value)}
              className="mw-input"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="submit" disabled={loadingLive} className="mw-button">
            <Radio className="h-5 w-5" />
            {loadingLive ? t('cmp.liveLoading') : t('cmp.live')}
          </button>
          <button type="button" onClick={handleRank} disabled={loadingRank} className="mw-button-soft">
            <Trophy className="h-5 w-5" />
            {loadingRank ? t('cmp.rankLoading') : t('cmp.rank')}
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      )}
      {rankError && (
        <p role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800">
          {rankError}
        </p>
      )}

      {/* Live results */}
      {liveResults && (
        <section>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-2xl font-bold">{t('cmp.liveTitle', { crop: selectedCrop ? selectedCrop.name : '' })}</h2>
            <p className="text-sm text-gray-500">
              {liveResults.source}{liveResults.updated_at ? ` · ${t('cmp.synced', { when: formatStamp(liveResults.updated_at) })}` : ''}
            </p>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            {liveResults.records.length === 1 ? t('cmp.reportsOne') : t('cmp.reports', { n: liveResults.records.length })}
            {location ? t('cmp.sortedByDistance') : '.'}
          </p>
          {liveResults.records.length === 0 ? (
            <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-5 text-gray-600">
              {t('cmp.noLive')}
            </p>
          ) : (
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {liveResults.records.map((record, index) => (
                <article key={`${record.mandi}-${record.commodity}-${index}`} className="mw-panel p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-[#1c2b20]">{record.mandi}</p>
                      <p className="text-sm text-gray-500">{record.district}{record.district ? ' district' : ''}</p>
                    </div>
                    {Number.isFinite(record.distance_km) && (
                      <span className="flex items-center gap-1 whitespace-nowrap rounded-full bg-[#e9f4e9] px-2.5 py-1 text-xs font-semibold text-[#197638]">
                        <Navigation className="h-3 w-3" />
                        {record.distance_km.toFixed(1)} km
                      </span>
                    )}
                  </div>
                  <div className="mt-4 flex items-baseline gap-2">
                    <IndianRupee className="h-5 w-5 text-[#197638]" />
                    <span className="text-3xl font-bold">{money(record.modal_price)}</span>
                    <span className="text-sm text-gray-500">/ quintal</span>
                  </div>
                  {record.min_price != null && record.max_price != null && (
                    <p className="mt-1 text-sm text-gray-500">
                      {t('cmp.range', { min: money(record.min_price), max: money(record.max_price) })}
                    </p>
                  )}
                  <p className="mt-3 text-xs text-gray-400">
                    {t('cmp.reported', { date: record.arrival_date })}{record.variety ? ` · ${record.variety}` : ''}
                  </p>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Profit ranking */}
      {ranked.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold">
            {t('cmp.rankTitle', { crop: selectedCrop ? t('cmp.rankFor', { crop: selectedCrop.name }) : '', qty: quantity })}
          </h2>
          <p className="mt-1 text-sm text-gray-500">{t('cmp.rankSub')}</p>
          {best && location && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={createQuickAlert}
                disabled={alertBusy}
                className="mw-button"
              >
                <BellRing className="h-5 w-5" />
                {alertBusy ? t('cmp.alertSaving') : t('cmp.alertMe', { amount: money(Math.floor((best.estimated_profit * 0.95) / 50) * 50) })}
              </button>
              <button type="button" onClick={() => navigate('/alerts')} className="mw-button-soft">
                {t('cmp.alertManage')}
              </button>
            </div>
          )}
          {alertNotice && (
            <p className="mt-3 flex items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              {alertNotice}
            </p>
          )}
          <div className="mt-4 space-y-3">
            {ranked.map(row => (
              <div
                key={row.mandi_id}
                className={`mw-panel flex flex-wrap items-center justify-between gap-4 p-5 ${
                  row.rank === 1 ? 'ring-2 ring-[#197638]' : ''
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-[#197638]">#{row.rank}</span>
                  <div>
                    <p className="font-bold text-[#1c2b20]">
                      {row.mandi_name}
                      {row.rank === 1 && (
                        <span className="ml-2 rounded-full bg-[#197638] px-2 py-0.5 text-xs font-semibold text-white">
                          {t('cmp.best')}
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-500">
                      {t('cmp.rowMeta', {
                        km: (row.distance_km ?? 0).toFixed(1),
                        price: money(row.current_price),
                        transport: money(row.transport_cost),
                      })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-lg font-bold text-[#1c2b20]">{t('cmp.estProfit', { amount: money(row.estimated_profit) })}</p>
                    <p className="text-sm text-gray-500">{t('cmp.revenue', { amount: money(row.expected_revenue) })}</p>
                  </div>
                  <a
                    href={shareUrl(row)}
                    target="_blank"
                    rel="noreferrer"
                    title={t('cmp.share')}
                    className="flex items-center gap-2 rounded-xl border border-[#d8d8ca] px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-[#f4f2e8]"
                  >
                    <MessageCircle className="h-4 w-4" />
                    {t('cmp.share')}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
