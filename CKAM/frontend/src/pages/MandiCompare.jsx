import React, { useEffect, useMemo, useState } from 'react';
import api, { getApiErrorMessage } from '../services/api';
import useLocation from '../hooks/useLocation';
import { haversineKm, matchMarket, normalizeMarketName } from '../services/location';
import { MapPin, Navigation, IndianRupee, Radio, Store, Trophy } from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

const formatStamp = value => {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
};

export default function MandiCompare() {
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

  const { location, loading: locating, error: locError, refresh } = useLocation({ autoAsk: true });

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')])
      .then(([cropsRes, mandisRes]) => {
        setCrops(cropsRes.data);
        if (cropsRes.data.length) setCropId(String(cropsRes.data[0].id));
        setMandis(mandisRes.data);
      })
      .catch(() =>
        setError(getApiErrorMessage(null, 'Could not load crop and mandi lists. Make sure the backend is running.')),
      );
  }, []);

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
      setError(getApiErrorMessage(err, 'Could not load live Karnataka rates. Please try again shortly.'));
    } finally {
      setLoadingLive(false);
    }
  };

  const handleRank = async () => {
    setRankError('');
    setRanked([]);
    if (!location) {
      setRankError('Allow your location first (button above) so distances to each mandi can be calculated.');
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
      setRankError(getApiErrorMessage(err, 'Could not rank mandis for this crop. Please try again.'));
    } finally {
      setLoadingRank(false);
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <p className="font-semibold text-[#197638]">Official live rates</p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">Karnataka mandi prices</h1>
        <p className="mt-3 text-gray-600">
          Live wholesale modal prices from the Government of India’s AGMARKNET dataset, matched to the real
          APMC markets nearest to you.
        </p>
      </header>

      {/* Farmer's current location */}
      <section className="mw-panel flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-[#e9f4e9] p-3 text-[#197638]"><MapPin className="h-6 w-6" /></div>
          <div>
            <p className="font-bold text-[#1c2b20]">Your current location</p>
            <p className="text-sm text-gray-500">
              {location
                ? `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}${location.accuracy ? ` (±${Math.round(location.accuracy)} m)` : ''}`
                : 'Not set — allow location to see distances and the nearest mandis.'}
            </p>
            {locError && <p className="mt-1 text-sm text-red-600">{locError}</p>}
          </div>
        </div>
        <button type="button" onClick={refresh} disabled={locating} className="mw-button-soft">
          <Navigation className={`h-5 w-5 ${locating ? 'animate-pulse' : ''}`} />
          {locating ? 'Locating…' : location ? 'Update location' : 'Use my current location'}
        </button>
      </section>

      {/* Nearest real mandis */}
      {location && nearest.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold">Mandis near you</h2>
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
            <label htmlFor="compare-crop" className="mw-label">Crop</label>
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
            <label htmlFor="compare-quantity" className="mw-label">Load (quintals)</label>
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
            {loadingLive ? 'Loading live rates…' : 'Show live rates'}
          </button>
          <button type="button" onClick={handleRank} disabled={loadingRank} className="mw-button-soft">
            <Trophy className="h-5 w-5" />
            {loadingRank ? 'Ranking mandis…' : 'Rank by profit'}
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
            <h2 className="text-2xl font-bold">Live rates{selectedCrop ? ` — ${selectedCrop.name}` : ''}</h2>
            <p className="text-sm text-gray-500">
              {liveResults.source}{liveResults.updated_at ? ` · synced ${formatStamp(liveResults.updated_at)}` : ''}
            </p>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            {liveResults.records.length} market report{liveResults.records.length === 1 ? '' : 's'}
            {location ? ', sorted by distance from you.' : '.'}
          </p>
          {liveResults.records.length === 0 ? (
            <p className="mt-4 rounded-2xl bg-[#f6f5ea] p-5 text-gray-600">
              No live reports for this crop right now — try another crop.
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
                      Range {money(record.min_price)}–{money(record.max_price)}
                    </p>
                  )}
                  <p className="mt-3 text-xs text-gray-400">
                    Reported {record.arrival_date}{record.variety ? ` · ${record.variety}` : ''}
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
            Best mandi{selectedCrop ? ` for ${selectedCrop.name}` : ''} · {quantity} quintal
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Distances from your current location. Ranking prices come from the bundled sample history —
            compare with the live rates above before deciding.
          </p>
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
                          BEST MANDI
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(row.distance_km ?? 0).toFixed(1)} km · price ₹{money(row.current_price)}/qtl · transport ₹
                      {money(row.transport_cost)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-[#1c2b20]">Est. profit ₹{money(row.estimated_profit)}</p>
                  <p className="text-sm text-gray-500">revenue ₹{money(row.expected_revenue)}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
