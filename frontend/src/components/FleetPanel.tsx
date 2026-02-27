import type { RouteStop } from "../services/api";

// Route colours mirror what's drawn on the map
export const ROUTE_COLORS = ["#3b82f6", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6", "#ec4899"];

interface RouteInfo {
  routeId: number;
  vehicleId: number;
  stops: RouteStop[];
  totalDistanceKm: number;
}

interface Props {
  routes: RouteInfo[];
  selectedRouteId: number | null;
  onSelect: (routeId: number) => void;
}

export function FleetPanel({ routes, selectedRouteId, onSelect }: Props) {
  return (
    <div style={{ width: 260, background: "#111827", color: "#e0e0e0", overflowY: "auto", padding: 12 }}>
      <h3 style={{ margin: "0 0 12px", fontSize: 13, textTransform: "uppercase", letterSpacing: 1, color: "#9ca3af" }}>
        Fleet
      </h3>
      {routes.map((r, i) => (
        <div
          key={r.routeId}
          onClick={() => onSelect(r.routeId)}
          style={{
            padding: "10px 12px",
            marginBottom: 8,
            borderRadius: 6,
            cursor: "pointer",
            background: selectedRouteId === r.routeId ? "#1f2937" : "transparent",
            borderLeft: `3px solid ${ROUTE_COLORS[i % ROUTE_COLORS.length]}`,
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 14 }}>Route {r.routeId}</div>
          <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
            {r.stops.length} stops · {r.totalDistanceKm.toFixed(1)} km
          </div>
        </div>
      ))}
      {routes.length === 0 && (
        <p style={{ color: "#4b5563", fontSize: 13 }}>No routes yet. Run a simulation.</p>
      )}
    </div>
  );
}
