import { useEffect, useRef, useState } from "react";
import { DeliveryMap } from "./components/DeliveryMap";
import { FleetPanel } from "./components/FleetPanel";
import { MetricsBar } from "./components/MetricsBar";
import { SimulationControls } from "./components/SimulationControls";
import { useRouteWebSocket } from "./hooks/useRouteWebSocket";
import { api, type OptimizeResult, type RouteStopDetail } from "./services/api";

interface RouteState {
  routeId: number;
  stops: RouteStopDetail[];
  totalDistanceKm: number;
  depotLat: number;
  depotLng: number;
}

const CITY_CENTRES: Record<string, [number, number]> = {
  seattle: [47.6062, -122.3321],
  la:      [34.0522, -118.2437],
  nyc:     [40.7128, -74.0060],
};

export default function App() {
  const [routes, setRoutes] = useState<RouteState[]>([]);
  const [metrics, setMetrics] = useState<OptimizeResult | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
  const [mapCentre, setMapCentre] = useState<[number, number]>(CITY_CENTRES.seattle);
  const [trafficLoading, setTrafficLoading] = useState(false);
  const [trafficRouteIds, setTrafficRouteIds] = useState<Set<number>>(new Set());

  // Keep a ref so the WebSocket effect closure can access latest routes without stale state
  const routesRef = useRef<RouteState[]>([]);
  routesRef.current = routes;

  const wsEvent = useRouteWebSocket(selectedRouteId);

  // Apply live reroute updates — stops from rerouter already carry lat/lng
  useEffect(() => {
    if (!wsEvent || wsEvent.event !== "rerouted") return;
    const { route_id, stops: newStops } = wsEvent.route;

    setRoutes((prev) =>
      prev.map((r) => {
        if (r.routeId !== route_id) return r;
        return {
          ...r,
          stops: newStops.map((s) => {
            const existing = r.stops.find((ps) => ps.stop_id === s.stop_id);
            return {
              stop_id: s.stop_id,
              sequence: s.sequence,
              planned_arrival: s.planned_arrival,
              lat: s.lat,
              lng: s.lng,
              address: existing?.address ?? "",
              earliest_time: existing?.earliest_time ?? "",
              latest_time: existing?.latest_time ?? "",
              package_weight_kg: existing?.package_weight_kg ?? 0,
            };
          }),
        };
      })
    );
  }, [wsEvent]);

  async function handleOptimized(result: OptimizeResult, routeIds: number[], city: string) {
    const centre = CITY_CENTRES[city] ?? CITY_CENTRES.seattle;
    setMapCentre(centre);
    setMetrics(result);

    const populated: RouteState[] = await Promise.all(
      routeIds.map(async (routeId) => {
        const stops = await api.getRouteDetail(routeId);
        return {
          routeId,
          stops,
          totalDistanceKm: result.total_distance_km / routeIds.length,
          depotLat: centre[0],
          depotLng: centre[1],
        };
      })
    );

    setRoutes(populated);
    setSelectedRouteId(populated[0]?.routeId ?? null);
  }

  async function handleTrafficInject(routeId: number) {
    setTrafficLoading(true);
    setTrafficRouteIds((prev) => new Set([...prev, routeId]));
    try {
      const events = await api.injectTraffic(routeId, 1.8);
      await api.reroute(routeId, events);
    } catch (err) {
      console.error("Traffic inject failed:", err);
    } finally {
      setTrafficLoading(false);
    }
  }

  const mapLayers = routes.map((r) => ({
    routeId: r.routeId,
    depotLat: r.depotLat,
    depotLng: r.depotLng,
    stops: r.stops.map((s) => ({
      stopId: s.stop_id,
      lat: s.lat,
      lng: s.lng,
      plannedArrival: s.planned_arrival,
      sequence: s.sequence,
      address: s.address,
      earliestTime: s.earliest_time,
      latestTime: s.latest_time,
      weightKg: s.package_weight_kg,
    })),
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f172a", color: "#e0e0e0" }}>
      <header style={{ padding: "12px 16px", background: "#0f172a", borderBottom: "1px solid #1f2937", display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: "#3b82f6", letterSpacing: -0.5 }}>LastMile</span>
        <span style={{ fontSize: 12, color: "#6b7280" }}>Route Optimization Engine</span>
      </header>

      <SimulationControls onOptimized={handleOptimized} />

      {metrics && (
        <MetricsBar
          totalDistanceKm={metrics.total_distance_km}
          greedyDistanceKm={metrics.greedy_distance_km}
          improvementPct={metrics.improvement_pct}
          numRoutes={metrics.num_routes}
          totalStops={routes.reduce((acc, r) => acc + r.stops.length, 0)}
        />
      )}

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <FleetPanel
          routes={routes.map((r) => ({
            routeId: r.routeId,
            vehicleId: r.routeId,
            stops: r.stops,
            totalDistanceKm: r.totalDistanceKm,
          }))}
          selectedRouteId={selectedRouteId}
          onSelect={setSelectedRouteId}
          onInjectTraffic={handleTrafficInject}
          trafficLoading={trafficLoading}
        />
        <DeliveryMap
          routes={mapLayers}
          centerLat={mapCentre[0]}
          centerLng={mapCentre[1]}
          trafficRouteIds={trafficRouteIds}
        />
      </div>
    </div>
  );
}
