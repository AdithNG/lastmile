const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface SimulationConfig {
  city?: string;
  num_stops?: number;
  num_vehicles?: number;
  seed?: number;
}

export interface SimulationResult {
  depot_id: number;
  vehicle_ids: number[];
  stop_ids: number[];
  city: string;
  num_stops: number;
  num_vehicles: number;
}

export interface OptimizeRequest {
  depot_id: number;
  vehicle_ids: number[];
  stop_ids: number[];
  date: string; // "YYYY-MM-DD"
}

export interface OptimizeResult {
  route_ids: number[];
  total_distance_km: number;
  greedy_distance_km: number;
  improvement_pct: number;
  num_routes: number;
}

export interface RouteStop {
  stop_id: number;
  sequence: number;
  planned_arrival: string | null;
}

export interface RouteStopDetail {
  stop_id: number;
  sequence: number;
  planned_arrival: string | null;
  lat: number;
  lng: number;
  address: string;
  earliest_time: string;
  latest_time: string;
  package_weight_kg: number;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  startSimulation: (cfg: SimulationConfig) =>
    post<SimulationResult>("/simulation/start", cfg),

  optimize: (req: OptimizeRequest) =>
    post<{ job_id: string; status: string }>("/routes/optimize", req),

  pollJob: (jobId: string) =>
    get<{ status: string; result?: OptimizeResult }>(`/routes/${jobId}/status`),

  getRouteStops: (routeId: number) =>
    get<RouteStop[]>(`/routes/${routeId}/stops`),

  getRouteDetail: (routeId: number) =>
    get<RouteStopDetail[]>(`/routes/${routeId}/detail`),

  reroute: (routeId: number, trafficEvents: object[]) =>
    post(`/routes/${routeId}/reroute`, { traffic_events: trafficEvents }),

  injectTraffic: (routeId: number, delayFactor: number) =>
    post("/simulation/inject-traffic", { route_id: routeId, delay_factor: delayFactor }),
};
