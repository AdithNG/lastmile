interface Props {
  totalDistanceKm: number;
  greedyDistanceKm: number;
  improvementPct: number;
  numRoutes: number;
  totalStops: number;
}

export function MetricsBar({ totalDistanceKm, greedyDistanceKm, improvementPct, numRoutes, totalStops }: Props) {
  return (
    <div style={{ display: "flex", gap: 24, padding: "12px 16px", background: "#1a1a2e", color: "#e0e0e0", fontSize: 13 }}>
      <Metric label="Total Distance" value={`${totalDistanceKm.toFixed(1)} km`} />
      <Metric label="Greedy Baseline" value={`${greedyDistanceKm.toFixed(1)} km`} />
      <Metric label="2-opt Improvement" value={`${improvementPct.toFixed(1)}%`} highlight />
      <Metric label="Routes" value={String(numRoutes)} />
      <Metric label="Stops" value={String(totalStops)} />
    </div>
  );
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span style={{ color: "#888", fontSize: 11, textTransform: "uppercase", letterSpacing: 1 }}>{label}</span>
      <span style={{ fontWeight: 700, fontSize: 16, color: highlight ? "#4ade80" : "#fff" }}>{value}</span>
    </div>
  );
}
