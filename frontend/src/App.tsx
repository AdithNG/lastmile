import { useState } from "react";
import { DeliveryMap } from "./components/DeliveryMap";
import { FleetPanel } from "./components/FleetPanel";
import { MetricsBar } from "./components/MetricsBar";
import { SimulationControls } from "./components/SimulationControls";
import { useRouteWebSocket } from "./hooks/useRouteWebSocket";
import { api, type OptimizeResult, type RouteStop } from "./services/api";

interface RouteState {
  routeId: number;
  vehicleId: number;
  stops: RouteStop[];
  totalDistanceKm: number;
  depotLat: number;
  depotLng: number;
}

// City centres for initial map positioning
const CITY_CENTRES: Record<string, [number, number]> = {
  seattle: [47.6062, -122.3321],
  la: [34.0522, -118.2437],
  nyc: [40.7128, -74.0060],
};

export default function App() {
  const [routes, setRoutes] = useState<RouteState[]>([]);
  const [metrics, setMetrics] = useState<OptimizeResult | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<number | null>(null);
  const [city, setCity] = useState("seattle");

  const wsEvent = useRouteWebSocket(selectedRouteId);

  // Apply live reroute updates from WebSocket
  if (wsEvent?.event === "rerouted") {
    setRoutes((prev) =>
      prev.map((r) =>
        r.routeId === wsEvent.route.route_id
          ? {
              ...r,
              stops: wsEvent.route.stops.map((s) => ({
                stop_id: s.stop_id,
                sequence: s.sequence,
                planned_arrival: s.planned_arrival,
              })),
            }
          : r
      )
    );
  }

  async function handleOptimized(result: OptimizeResult, routeIds: number[]) {
    setMetrics(result);

    // Fetch stop details for each route to build map layers
    const populated: RouteState[] = await Promise.all(
      routeIds.map(async (routeId, i) => {
        const stops = await api.getRouteStops(routeId);
        return {
          routeId,
          vehicleId: i + 1,
          stops,
          totalDistanceKm: result.total_distance_km / routeIds.length,
          depotLat: CITY_CENTRES[city][0],
          depotLng: CITY_CENTRES[city][1],
        };
      })
    );
    setRoutes(populated);
    setSelectedRouteId(populated[0]?.routeId ?? null);
  }

  const [centre] = useState<[number, number]>(CITY_CENTRES.seattle);
  const mapCentre = CITY_CENTRES[city] ?? centre;

  const mapLayers = routes.map((r) => ({
    routeId: r.routeId,
    depotLat: r.depotLat,
    depotLng: r.depotLng,
    stops: r.stops.map((s) => ({
      stopId: s.stop_id,
      lat: 0,        // populated below once we have coords
      lng: 0,
      plannedArrival: s.planned_arrival,
      sequence: s.sequence,
    })),
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f172a", color: "#e0e0e0" }}>
      {/* Header */}
      <header style={{ padding: "12px 16px", background: "#0f172a", borderBottom: "1px solid #1f2937", display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: "#3b82f6", letterSpacing: -0.5 }}>LastMile</span>
        <span style={{ fontSize: 12, color: "#6b7280" }}>Route Optimization Engine</span>
      </header>

      {/* Simulation controls */}
      <SimulationControls onOptimized={handleOptimized} />

      {/* Metrics bar — only shown after optimization */}
      {metrics && (
        <MetricsBar
          totalDistanceKm={metrics.total_distance_km}
          greedyDistanceKm={metrics.greedy_distance_km}
          improvementPct={metrics.improvement_pct}
          numRoutes={metrics.num_routes}
          totalStops={routes.reduce((acc, r) => acc + r.stops.length, 0)}
        />
      )}

      {/* Main content */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <FleetPanel
          routes={routes.map((r) => ({ ...r }))}
          selectedRouteId={selectedRouteId}
          onSelect={setSelectedRouteId}
        />
        <DeliveryMap
          routes={mapLayers}
          centerLat={mapCentre[0]}
          centerLng={mapCentre[1]}
        />
      </div>
    </div>
  );
}
