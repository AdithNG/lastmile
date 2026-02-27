import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import { ROUTE_COLORS } from "./FleetPanel";

// Fix default Leaflet marker icons broken by bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface StopCoord {
  stopId: number;
  lat: number;
  lng: number;
  plannedArrival: string | null;
  sequence: number;
  address?: string;
  earliestTime?: string;
  latestTime?: string;
  weightKg?: number;
}

interface RouteLayer {
  routeId: number;
  stops: StopCoord[];
  depotLat: number;
  depotLng: number;
}

interface Props {
  routes: RouteLayer[];
  centerLat?: number;
  centerLng?: number;
}

function RecenterMap({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng], 12);
  }, [lat, lng, map]);
  return null;
}

export function DeliveryMap({ routes, centerLat = 47.6062, centerLng = -122.3321 }: Props) {
  return (
    <MapContainer
      center={[centerLat, centerLng]}
      zoom={12}
      style={{ flex: 1, height: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
      />
      <RecenterMap lat={centerLat} lng={centerLng} />

      {routes.map((route, ri) => {
        const color = ROUTE_COLORS[ri % ROUTE_COLORS.length];
        const depotIcon = L.divIcon({ className: "", html: `<div style="width:14px;height:14px;background:#fff;border:3px solid ${color};border-radius:50%"/>` });
        const stopIcon = L.divIcon({ className: "", html: `<div style="width:10px;height:10px;background:${color};border-radius:50%"/>` });

        const polyline: [number, number][] = [
          [route.depotLat, route.depotLng],
          ...route.stops.map((s) => [s.lat, s.lng] as [number, number]),
          [route.depotLat, route.depotLng],
        ];

        return (
          <div key={route.routeId}>
            <Marker position={[route.depotLat, route.depotLng]} icon={depotIcon}>
              <Popup>Depot</Popup>
            </Marker>
            <Polyline positions={polyline} color={color} weight={2.5} opacity={0.8} />
            {route.stops.map((s) => (
              <Marker key={s.stopId} position={[s.lat, s.lng]} icon={stopIcon}>
                <Popup>
                  <div style={{ fontSize: 12, lineHeight: 1.6 }}>
                    <strong>Stop #{s.sequence + 1}</strong><br />
                    {s.address && <>{s.address}<br /></>}
                    ETA: <b>{s.plannedArrival ?? "—"}</b><br />
                    {s.earliestTime && <>Window: {s.earliestTime} – {s.latestTime}<br /></>}
                    {s.weightKg != null && <>Weight: {s.weightKg} kg</>}
                  </div>
                </Popup>
              </Marker>
            ))}
          </div>
        );
      })}
    </MapContainer>
  );
}
