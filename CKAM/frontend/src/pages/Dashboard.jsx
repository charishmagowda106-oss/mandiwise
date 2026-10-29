import React, { useCallback, useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api, { getApiErrorMessage } from '../services/api';
import useLocation from '../hooks/useLocation';
import { useLanguage } from '../i18n';
import { cropEmoji } from '../services/crops';
import CropFormModal from '../components/CropFormModal';
import {
  Plus, Store, MapPin, Pencil, Trash2, Search, TrendingUp, Loader2, CalendarDays, Package,
} from 'lucide-react';

const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function Dashboard() {
  const { user } = useContext(AuthContext);
  const { t } = useLanguage();
  const { location } = useLocation();
  const [catalog, setCatalog] = useState([]);
  const [myCrops, setMyCrops] = useState(null); // null = loading
  const [mandiCount, setMandiCount] = useState(0);
  const [error, setError] = useState('');
  const [modal, setModal] = useState({ open: false, initial: null });

  const loadMyCrops = useCallback(() => {
    api.get('/my-crops')
      .then(res => setMyCrops(res.data))
      .catch(err => { setMyCrops([]); setError(getApiErrorMessage(err, t('err.market'))); });
  }, [t]);

  useEffect(() => {
    Promise.all([api.get('/crops/'), api.get('/mandis/')])
      .then(([cropsRes, mandisRes]) => { setCatalog(cropsRes.data); setMandiCount(mandisRes.data.length); })
      .catch(() => setError(t('err.market')));
    loadMyCrops();
  }, [loadMyCrops, t]);

  const removeCrop = async row => {
    if (!window.confirm(t('dash.confirmDelete', { name: row.crop_name }))) return;
    try {
      await api.delete(`/my-crops/${row.id}`);
      setMyCrops(prev => (prev || []).filter(item => item.id !== row.id));
    } catch (err) {
      setError(getApiErrorMessage(err, t('crop.saveFailed')));
    }
  };

  const statusStyle = status => ({
    ready: { pill: 'bg-rose-100 text-rose-700', bar: 'from-rose-400 to-orange-300', tint: 'bg-rose-50' },
    soon: { pill: 'bg-amber-100 text-amber-800', bar: 'from-amber-400 to-yellow-300', tint: 'bg-amber-50' },
    growing: { pill: 'bg-emerald-100 text-emerald-700', bar: 'from-emerald-400 to-lime-300', tint: 'bg-emerald-50' },
    watching: { pill: 'bg-sky-100 text-sky-700', bar: 'from-sky-400 to-cyan-300', tint: 'bg-sky-50' },
  }[status] || { pill: 'bg-gray-100 text-gray-600', bar: 'from-gray-300 to-gray-200', tint: 'bg-gray-50' });

  const harvestLabel = row => {
    if (row.expected_harvest_date == null) return t('dash.noHarvestDate');
    if (row.days_to_harvest < 0) return t('dash.harvestOverdue', { n: -row.days_to_harvest });
    if (row.days_to_harvest === 0) return t('dash.harvestToday');
    return t('dash.harvestIn', { n: row.days_to_harvest });
  };

  const statusLabel = status => ({
    ready: t('dash.statusReady'),
    soon: t('dash.statusSoon'),
    growing: t('dash.statusGrowing'),
    watching: t('dash.statusWatching'),
  }[status] || status);

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="mw-hero">
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-20 right-24 h-44 w-44 rounded-full bg-emerald-300/20 blur-2xl" />
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-emerald-100/90">{t('dash.kicker')}</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight sm:text-4xl">{t('dash.namaste', { name: user?.name?.split(' ')[0] })}</h1>
            <p className="mt-2 max-w-xl text-emerald-50/90">{t('dash.heroSub')}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="mw-chip bg-white/15"><Package className="h-3.5 w-3.5" />{t('dash.chipCrops', { n: (myCrops || []).length })}</span>
              <span className="mw-chip bg-white/15"><Store className="h-3.5 w-3.5" />{t('dash.chipMandis', { n: mandiCount })}</span>
              {location && <span className="mw-chip bg-white/15"><MapPin className="h-3.5 w-3.5" />{location.name || `${location.lat.toFixed(2)}, ${location.lng.toFixed(2)}`}</span>}
            </div>
          </div>
          <button type="button" onClick={() => setModal({ open: true, initial: null })} className="inline-flex shrink-0 items-center gap-2 rounded-2xl bg-white px-5 py-3 font-bold text-[#15602e] shadow-sm transition hover:bg-emerald-50">
            <Plus className="h-5 w-5" />{t('dash.addCrop')}
          </button>
        </div>
      </section>

      {!location && (
        <section className="flex flex-col gap-3 rounded-3xl border border-amber-200 bg-amber-50 p-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-2 text-sm font-medium text-amber-900">
            <MapPin className="h-5 w-5 shrink-0" />{t('loc.notsetCompare')}
          </p>
          <p className="text-xs text-amber-700">{t('dash.setLocationHint')}</p>
        </section>
      )}

      {error && <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>}

      {/* My crops */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-[#1c2b20]">{t('dash.myCrops')}</h2>
          {myCrops && myCrops.length > 0 && (
            <button type="button" onClick={() => setModal({ open: true, initial: null })} className="mw-chip border border-[#d8d8ca] bg-white py-1.5 text-[#197638] hover:bg-[#f4f2e8]">
              <Plus className="h-3.5 w-3.5" />{t('dash.addCrop')}
            </button>
          )}
        </div>

        {myCrops === null ? (
          <div className="mw-panel grid place-items-center gap-3 p-12 text-gray-400"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : myCrops.length === 0 ? (
          <div className="mw-panel grid place-items-center gap-3 p-12 text-center">
            <div className="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-emerald-100 to-lime-100 text-5xl">🌱</div>
            <h3 className="text-lg font-bold text-[#1c2b20]">{t('dash.emptyTitle')}</h3>
            <p className="max-w-md text-sm text-gray-500">{t('dash.emptyBody')}</p>
            <button type="button" onClick={() => setModal({ open: true, initial: null })} className="mw-button mt-2"><Plus className="h-5 w-5" />{t('dash.addFirstCrop')}</button>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {myCrops.map((row, index) => {
              const style = statusStyle(row.status);
              return (
                <article key={row.id} className="mw-panel mw-rise overflow-hidden" style={{ animationDelay: `${index * 45}ms` }}>
                  <div className={`h-1.5 bg-gradient-to-r ${style.bar}`} />
                  <div className="p-5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl text-2xl ${style.tint}`}>{cropEmoji(row.crop_name, row.category)}</div>
                        <div>
                          <h3 className="font-bold text-[#1c2b20]">{row.crop_name}</h3>
                          <p className="text-xs text-gray-500">{t('dash.qtyQtl', { n: row.quantity })}</p>
                        </div>
                      </div>
                      <span className={`mw-chip ${style.pill}`}>{statusLabel(row.status)}</span>
                    </div>

                    <p className="mt-3 flex items-center gap-1.5 text-sm text-gray-600">
                      <CalendarDays className="h-4 w-4 text-gray-400" />{harvestLabel(row)}
                    </p>

                    <div className="mt-4 border-t border-dashed border-[#e3e2d3] pt-4">
                      {row.best ? (
                        <>
                          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[#197638]">
                            <Store className="h-3.5 w-3.5" />{t('dash.bestToday')}
                          </p>
                          <div className="mt-1 flex items-baseline justify-between gap-2">
                            <p className="truncate font-semibold text-[#1c2b20]">{row.best.mandi_name}</p>
                            <p className="shrink-0 text-lg font-bold text-[#197638]">₹{money(row.best.current_price)}<span className="text-xs font-medium text-gray-400">/qtl</span></p>
                          </div>
                          <p className="mt-0.5 text-xs text-gray-500">
                            {t('dash.revenueEst', { amount: money(row.best.expected_revenue) })} · {row.best.distance_km.toFixed(1)} km
                          </p>
                        </>
                      ) : (
                        <p className="flex items-center gap-1.5 text-xs text-gray-400"><MapPin className="h-3.5 w-3.5" />{t('dash.noBestYet')}</p>
                      )}
                    </div>

                    <div className="mt-4 flex items-center gap-2">
                      <Link to={`/compare?crop=${row.crop_id}&qty=${row.quantity}`} className="mw-button-soft flex-1 !py-2 text-sm">
                        <Search className="h-4 w-4" />{t('dash.compare')}
                      </Link>
                      <button type="button" onClick={() => setModal({ open: true, initial: row })} aria-label={t('dash.edit')} className="rounded-xl border border-[#d8d8ca] p-2.5 text-gray-500 hover:bg-[#f4f2e8]">
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button type="button" onClick={() => removeCrop(row)} aria-label={t('dash.delete')} className="rounded-xl border border-[#d8d8ca] p-2.5 text-gray-500 hover:bg-red-50 hover:text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Quick tools */}
      <section className="grid gap-4 md:grid-cols-2">
        <Link to="/compare" className="group flex min-h-32 items-center justify-between rounded-3xl bg-gradient-to-br from-[#197638] to-[#0e5a29] p-6 text-white shadow-sm">
          <div><Search className="mb-3 h-6 w-6" /><h2 className="text-xl font-bold">{t('dash.card1Title')}</h2><p className="mt-1 text-sm text-emerald-100">{t('dash.card1Sub')}</p></div>
        </Link>
        <Link to="/predict" className="group flex min-h-32 items-center justify-between rounded-3xl bg-gradient-to-br from-[#f59e0b] to-[#d97706] p-6 text-white shadow-sm">
          <div><TrendingUp className="mb-3 h-6 w-6" /><h2 className="text-xl font-bold">{t('dash.card2Title')}</h2><p className="mt-1 text-sm text-amber-100">{t('dash.card2Sub')}</p></div>
        </Link>
      </section>

      <CropFormModal open={modal.open} initial={modal.initial} onClose={() => setModal({ open: false, initial: null })} onSaved={loadMyCrops} />
    </div>
  );
}
