import { useEffect, useRef, useState } from "react";

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export interface RerouteEvent {
  event: "rerouted";
  route: {
    route_id: number;
    stops: Array<{
      stop_id: number;
      sequence: number;
      planned_arrival: string;
      planned_arrival_min: number;
      lat: number;
      lng: number;
    }>;
  };
}

export function useRouteWebSocket(routeId: number | null) {
  const [lastEvent, setLastEvent] = useState<RerouteEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (routeId === null) return;

    const ws = new WebSocket(`${WS_BASE}/routes/ws/${routeId}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        setLastEvent(JSON.parse(e.data));
      } catch {
        // ignore malformed frames
      }
    };

    // Keep-alive ping every 25 seconds
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25_000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [routeId]);

  return lastEvent;
}
