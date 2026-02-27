import { useState } from "react";
import { api, type OptimizeResult } from "../services/api";

interface Props {
  onOptimized: (result: OptimizeResult, routeIds: number[]) => void;
}

export function SimulationControls({ onOptimized }: Props) {
  const [city, setCity] = useState("seattle");
  const [stops, setStops] = useState(20);
  const [vehicles, setVehicles] = useState(3);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runSimulation() {
    setLoading(true);
    setStatus("Generating scenario…");

    try {
      const scenario = await api.startSimulation({ city, num_stops: stops, num_vehicles: vehicles });
      setStatus("Optimizing routes…");

      const { job_id } = await api.optimize({
        depot_id: scenario.depot_id,
        vehicle_ids: scenario.vehicle_ids,
        stop_ids: scenario.stop_ids,
        date: new Date().toISOString().slice(0, 10),
      });

      // Poll until done
      let result: OptimizeResult | undefined;
      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const poll = await api.pollJob(job_id);
        if (poll.status === "done" && poll.result) {
          result = poll.result;
          break;
        }
        if (poll.status === "failed") throw new Error("Optimization failed");
      }

      if (!result) throw new Error("Optimization timed out");

      setStatus(`Done — ${result.improvement_pct.toFixed(1)}% improvement over greedy`);
      onOptimized(result, result.route_ids);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 16, background: "#111827", color: "#e0e0e0", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
      <select value={city} onChange={(e) => setCity(e.target.value)} style={selectStyle}>
        <option value="seattle">Seattle</option>
        <option value="la">Los Angeles</option>
        <option value="nyc">New York</option>
      </select>

      <label style={labelStyle}>
        Stops
        <input type="number" min={5} max={50} value={stops} onChange={(e) => setStops(+e.target.value)} style={inputStyle} />
      </label>

      <label style={labelStyle}>
        Vehicles
        <input type="number" min={1} max={10} value={vehicles} onChange={(e) => setVehicles(+e.target.value)} style={inputStyle} />
      </label>

      <button onClick={runSimulation} disabled={loading} style={btnStyle}>
        {loading ? "Running…" : "Run Simulation"}
      </button>

      {status && <span style={{ fontSize: 13, color: "#9ca3af" }}>{status}</span>}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  background: "#1f2937", color: "#e0e0e0", border: "1px solid #374151",
  borderRadius: 4, padding: "6px 10px", fontSize: 13,
};
const inputStyle: React.CSSProperties = {
  width: 60, background: "#1f2937", color: "#e0e0e0", border: "1px solid #374151",
  borderRadius: 4, padding: "4px 8px", fontSize: 13, marginLeft: 6,
};
const labelStyle: React.CSSProperties = { fontSize: 13, display: "flex", alignItems: "center" };
const btnStyle: React.CSSProperties = {
  background: "#3b82f6", color: "#fff", border: "none", borderRadius: 4,
  padding: "8px 16px", cursor: "pointer", fontSize: 13, fontWeight: 600,
};
