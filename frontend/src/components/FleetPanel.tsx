import type { RouteStopDetail } from "../services/api";

// Route colours mirror what's drawn on the map
export const ROUTE_COLORS = ["#3b82f6", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6", "#ec4899"];

interface RouteInfo {
  routeId: number;
  vehicleId: number;
  stops: RouteStopDetail[];
  totalDistanceKm: number;
}

interface Props {
  routes: RouteInfo[];
  selectedRouteId: number | null;
  onSelect: (routeId: number) => void;
  onInjectTraffic?: (routeId: number) => void;
  trafficLoading?: boolean;
}

export function FleetPanel({ routes, selectedRouteId, onSelect, onInjectTraffic, trafficLoading }: Props) {
  return (
    <div style={{ width: 280, background: "#111827", color: "#e0e0e0", overflowY: "auto", padding: 12, flexShrink: 0 }}>
      <h3 style={{ margin: "0 0 12px", fontSize: 13, textTransform: "uppercase", letterSpacing: 1, color: "#9ca3af" }}>
        Fleet
      </h3>

      {routes.map((r, i) => {
        const color = ROUTE_COLORS[i % ROUTE_COLORS.length];
        const isSelected = selectedRouteId === r.routeId;

        return (
          <div key={r.routeId} style={{ marginBottom: 8 }}>
            {/* Route header row */}
            <div
              onClick={() => onSelect(r.routeId)}
              style={{
                padding: "10px 12px",
                borderRadius: 6,
                cursor: "pointer",
                background: isSelected ? "#1f2937" : "transparent",
                borderLeft: `3px solid ${color}`,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14 }}>Route {r.routeId}</div>
              <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                {r.stops.length} stops · {r.totalDistanceKm.toFixed(1)} km
              </div>
            </div>

            {/* Expanded stop list + traffic button when route is selected */}
            {isSelected && r.stops.length > 0 && (
              <div style={{ paddingLeft: 8, marginTop: 4 }}>
                <div style={{ maxHeight: 200, overflowY: "auto" }}>
                  {r.stops.map((s) => (
                    <div
                      key={s.stop_id}
                      style={{ padding: "5px 8px", borderBottom: "1px solid #1f2937", fontSize: 11 }}
                    >
                      <div>
                        <span style={{ color, fontWeight: 700 }}>#{s.sequence + 1}</span>
                        {" "}
                        <span style={{ color: "#d1d5db" }}>{s.address.split(",")[0]}</span>
                      </div>
                      <div style={{ color: "#6b7280", marginTop: 1 }}>
                        ETA: {s.planned_arrival ?? "—"} · {s.package_weight_kg} kg
                      </div>
                    </div>
                  ))}
                </div>

                {onInjectTraffic && (
                  <button
                    onClick={() => onInjectTraffic(r.routeId)}
                    disabled={trafficLoading}
                    style={{
                      marginTop: 8,
                      width: "100%",
                      padding: "7px 0",
                      background: trafficLoading ? "#374151" : "#dc2626",
                      color: "#fff",
                      border: "none",
                      borderRadius: 4,
                      cursor: trafficLoading ? "default" : "pointer",
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {trafficLoading ? "Rerouting…" : "Simulate Traffic Delay"}
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}

      {routes.length === 0 && (
        <p style={{ color: "#4b5563", fontSize: 13 }}>No routes yet. Run a simulation.</p>
      )}
    </div>
  );
}
