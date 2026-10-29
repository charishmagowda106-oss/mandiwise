import React, { useEffect, useState } from 'react';
import { X, Loader2, Sprout } from 'lucide-react';
import api, { getApiErrorMessage } from '../services/api';
import { useLanguage } from '../i18n';
import { cropEmoji } from '../services/crops';

/** Add / edit one of the farmer's sown crops (quantity, harvest date, costs).
 *  Costs are optional but unlock real net-profit estimates (feature #13). */
export default function CropFormModal({ open, initial, onClose, onSaved }) {
  const { t } = useLanguage();
  const [crops, setCrops] = useState([]);
  const [form, setForm] = useState({ crop_id: '', quantity: '10', sown_date: '', expected_harvest_date: '', cost_seed: '', cost_fertilizer: '', cost_labor: '', cost_other: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;
    api.get('/crops/').then(res => setCrops(res.data)).catch(() => setError(t('err.cropsMandis')));
  }, [open, t]);

  useEffect(() => {
    if (!open) return;
    setError('');
    setForm(initial
      ? {
          crop_id: String(initial.crop_id),
          quantity: String(initial.quantity ?? 10),
          sown_date: initial.sown_date || '',
          expected_harvest_date: initial.expected_harvest_date || '',
          cost_seed: initial.cost_seed ?? '',
          cost_fertilizer: initial.cost_fertilizer ?? '',
          cost_labor: initial.cost_labor ?? '',
          cost_other: initial.cost_other ?? '',
        }
      : { crop_id: '', quantity: '10', sown_date: '', expected_harvest_date: '', cost_seed: '', cost_fertilizer: '', cost_labor: '', cost_other: '' });
  }, [open, initial]);

  if (!open) return null;

  const set = key => event => setForm(prev => ({ ...prev, [key]: event.target.value }));
  const selectedCrop = crops.find(crop => String(crop.id) === String(form.crop_id));

  const submit = async event => {
    event.preventDefault();
    if (!form.crop_id) { setError(t('crop.pickCrop')); return; }
    setBusy(true);
    setError('');
    const numberOrNull = value => (value === '' || value == null ? null : Number(value));
    const payload = {
      quantity: Number(form.quantity) || 10,
      sown_date: form.sown_date || null,
      expected_harvest_date: form.expected_harvest_date || null,
      cost_seed: numberOrNull(form.cost_seed),
      cost_fertilizer: numberOrNull(form.cost_fertilizer),
      cost_labor: numberOrNull(form.cost_labor),
      cost_other: numberOrNull(form.cost_other),
    };
    try {
      if (initial) {
        await api.patch(`/my-crops/${initial.id}`, payload);
      } else {
        await api.post('/my-crops', { ...payload, crop_id: Number(form.crop_id) });
      }
      onSaved?.();
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, t('crop.saveFailed')));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-black/45 p-4" onClick={onClose}>
      <form
        onSubmit={submit}
        onClick={event => event.stopPropagation()}
        className="mw-rise max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-bold text-[#1c2b20]">
            <span className="text-2xl">{selectedCrop ? cropEmoji(selectedCrop.name, selectedCrop.category) : '🌱'}</span>
            {initial ? t('crop.editTitle') : t('crop.addTitle')}
          </h2>
          <button type="button" onClick={onClose} className="rounded-xl p-2 text-gray-400 hover:bg-[#f4f2e8]"><X className="h-5 w-5" /></button>
        </div>

        <div className="mt-5 space-y-4">
          <div>
            <label className="mw-label">{t('crop.fieldCrop')}</label>
            <select value={form.crop_id} onChange={set('crop_id')} disabled={Boolean(initial)} className="mw-input">
              <option value="">{t('crop.pickCrop')}</option>
              {crops.map(crop => <option key={crop.id} value={crop.id}>{cropEmoji(crop.name, crop.category)} {crop.name}</option>)}
            </select>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="mw-label">{t('crop.fieldQty')}</label>
              <input type="number" min="0.5" step="0.5" value={form.quantity} onChange={set('quantity')} className="mw-input" />
            </div>
            <div>
              <label className="mw-label">{t('crop.fieldSown')}</label>
              <input type="date" value={form.sown_date} onChange={set('sown_date')} className="mw-input" />
            </div>
            <div>
              <label className="mw-label">{t('crop.fieldHarvest')}</label>
              <input type="date" value={form.expected_harvest_date} onChange={set('expected_harvest_date')} className="mw-input" />
            </div>
          </div>

          <div className="rounded-2xl bg-[#f6f8ee] p-4">
            <p className="text-sm font-bold text-[#28412c]">{t('crop.costsTitle')}</p>
            <p className="mt-0.5 text-xs text-gray-500">{t('crop.costsHint')}</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-4">
              {[['cost_seed', t('crop.costSeed')], ['cost_fertilizer', t('crop.costFert')], ['cost_labor', t('crop.costLabor')], ['cost_other', t('crop.costOther')]].map(([key, label]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs font-semibold text-gray-500">{label}</label>
                  <input type="number" min="0" step="100" value={form[key]} onChange={set(key)} placeholder="₹" className="mw-input !px-3 !py-2 text-sm" />
                </div>
              ))}
            </div>
          </div>

          {error && <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="mw-button-soft">{t('ui.cancel')}</button>
          <button type="submit" disabled={busy} className="mw-button">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sprout className="h-4 w-4" />}
            {busy ? t('crop.saving') : t('crop.save')}
          </button>
        </div>
      </form>
    </div>
  );
}
