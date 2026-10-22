import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useLanguage } from '../i18n';

// Leaflet's default marker images break under Vite bundling, so we draw the
// pins ourselves with tiny CSS shapes — zero image files, zero missing icons.
const userIcon = L.divIcon({
  className: '',
  html: '<div style="width:16px;height:16px;border-radius:9999px;background:#197638;border:3px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45)"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const mandiIcon = L.divIcon({
  className: '',
  html: '<div style="width:15px;height:15px;border-radius:9999px 9999px 9999px 0;background:#17321f;border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45);transform:rotate(-45deg)"></div>',
  iconSize: [15, 15],
  iconAnchor: [7, 15],
});

const KARNATAKA_CENTER = [15.36, 75.12];

// MapContainer fixes its center after mount — this child flies the view when
// the farmer's GPS arrives (or when they press "Update location").
function Recenter({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.setView(center, zoom);
  }, [center, zoom, map]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

export default function MandiMap({ location, mandis }) {
  const { t } = useLanguage();
  const center = location ? [location.lat, location.lng] : KARNATAKA_CENTER;
  const zoom = location ? 9 : 7;

  return (
    <section>
      <h2 className="text-2xl font-bold">{t('cmp.mapTitle')}</h2>
      <p className="mt-1 text-sm text-gray-500">{t('cmp.mapSub')}</p>
      <div className="mw-panel mt-4 overflow-hidden p-0">
        <MapContainer center={center} zoom={zoom} scrollWheelZoom style={{ height: 400, width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Recenter center={center} zoom={zoom} />
          {location && (
            <Marker position={[location.lat, location.lng]} icon={userIcon}>
              <Popup><strong>{t('cmp.mapYou')}</strong></Popup>
            </Marker>
          )}
          {mandis.map(mandi => (
            <Marker key={mandi.id} position={[mandi.lat, mandi.lng]} icon={mandiIcon}>
              <Popup>
                <strong>{mandi.name}</strong>
                <br />
                {mandi.district} district
                {Number.isFinite(mandi.distance_km) && (
                  <>
                    <br />
                    {mandi.distance_km.toFixed(1)} km
                  </>
                )}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </section>
  );
}
