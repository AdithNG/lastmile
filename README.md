# LastMile

**Real-time delivery route optimization engine** — a full-stack implementation of the Capacitated Vehicle Routing Problem with Time Windows (CVRPTW), the same core logistics problem Amazon solves for millions of deliveries every day.

[![CI](https://github.com/AdithNG/lastmile/actions/workflows/ci.yml/badge.svg)](https://github.com/AdithNG/lastmile/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.4-blue)

---

## What It Does

LastMile takes a set of delivery stops scattered across a city, a fleet of vehicles each with a weight capacity, and time windows for each stop — and computes the optimal set of routes for each driver. When traffic conditions change mid-delivery, it reroutes in real time and pushes updated ETAs to the frontend over WebSocket.

**Demo** (`docker compose up --build`, then open `http://localhost:3000`):
1. Select a city (Seattle / LA / NYC), set number of stops and vehicles
2. Click **Run Simulation** — the engine generates stops, solves the CVRPTW, and draws colored route polylines on the map
3. Click any route in the fleet panel to see its full stop list with addresses and ETAs
4. Click **Simulate Traffic Delay** — the route turns red and dashed on the map immediately, the rerouter recomputes ETAs with a 1.8× delay factor, and updated stop times push live via WebSocket

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (React + Leaflet)                                  │
│  SimulationControls → FleetPanel → DeliveryMap              │
│  WebSocket: receives live reroute events                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│  FastAPI (port 8000)                                        │
│  /simulation/start  →  generate scenario in PostgreSQL      │
│  /routes/optimize   →  enqueue Celery task, return job_id   │
│  /routes/{id}/detail→  full stop data with lat/lng          │
│  /routes/{id}/reroute → recompute ETAs, broadcast WS        │
│  /routes/ws/{id}    →  WebSocket endpoint                   │
└──────────┬───────────────────────────┬───────────────────────┘
           │                           │
┌──────────▼──────────┐   ┌────────────▼──────────────┐
│  Celery Worker      │   │  PostgreSQL (RDS in prod)  │
│  CVRPTWSolver       │   │  depots, vehicles, stops,  │
│  greedy + 2-opt     │   │  routes, route_stops       │
└──────────┬──────────┘   └────────────────────────────┘
           │
┌──────────▼──────────┐
│  Redis (ElastiCache) │
│  task broker +       │
│  result backend      │
└─────────────────────┘
```

---

## The Algorithm

CVRPTW is NP-hard — for 20 stops and 3 vehicles there are more possible assignments than atoms in the observable universe. Brute force is impossible. LastMile uses a two-phase heuristic:

### Phase 1 — Greedy Nearest-Neighbor Construction `O(n²)`

Starting from the depot, repeatedly assign the nearest unvisited stop to the current vehicle's route. Before each assignment, validate:
- **Capacity constraint**: total package weight ≤ vehicle capacity
- **Time window constraint**: arrival time falls within `[earliest, latest]` for that stop

If adding a stop would violate either constraint, close the current route and start a new vehicle. This produces a feasible solution fast.

### Phase 2 — 2-Opt Local Search (Improvement)

For each route, try reversing every possible sub-segment `[i, j]`:
- If reversing produces a shorter total distance **and** all time windows still hold → accept
- Repeat until no improving swap exists

In practice this reduces total distance by **10–20% over greedy** in seconds. This is the same class of improvement Amazon's DDP system uses.

### Phase 3 — Real-Time Rerouting

When a traffic event arrives, the rerouter:
1. Rebuilds the time matrix for remaining stops
2. Applies a `delay_factor` multiplier to affected edges
3. Recomputes ETAs along the existing stop sequence
4. Broadcasts the updated stop list over WebSocket — the map updates without a page reload

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend API | Python 3.11, FastAPI | Async, WebSocket support |
| Algorithm | Pure Python + NumPy | CVRPTWSolver, constraint checker, distance matrix |
| Task Queue | Celery + Redis | Non-blocking optimization — API returns job_id immediately |
| Database | PostgreSQL 15 + SQLAlchemy async | Alembic migrations, asyncpg driver |
| Frontend | React 18, TypeScript, Vite | |
| Map | Leaflet.js via react-leaflet | Colored polylines, marker popups, live recentering |
| Distances | OpenRouteService API | Falls back to haversine when key not set or stop count exceeds ORS 50-location limit |
| Containers | Docker Compose | 5 services: backend, worker, frontend, db, redis |
| Cloud | AWS EC2 + RDS + ElastiCache | Terraform IaC in `infra/terraform/` — spin up on demand |
| CI/CD | GitHub Actions | pytest + Docker build on every push |

---

## Project Structure

```
lastmile/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── config.py                  # Pydantic settings
│   │   ├── database.py                # Async SQLAlchemy engine
│   │   ├── models/                    # Depot, Vehicle, Stop, Route, RouteStop
│   │   ├── routers/
│   │   │   ├── routes.py              # Optimize, detail, reroute, WebSocket
│   │   │   ├── stops.py
│   │   │   ├── vehicles.py
│   │   │   └── simulation.py
│   │   ├── services/
│   │   │   ├── optimizer.py           # CVRPTWSolver — greedy + 2-opt
│   │   │   ├── constraint_checker.py  # Time window + capacity validation
│   │   │   ├── distance_matrix.py     # ORS API + haversine fallback
│   │   │   ├── rerouter.py            # Live ETA recomputation
│   │   │   └── simulator.py          # Scenario generator (Seattle/LA/NYC)
│   │   └── workers/
│   │       └── celery_tasks.py        # Async optimization task
│   ├── alembic/                       # Database migrations
│   ├── tests/                         # 25 unit tests — optimizer, constraints, distances
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DeliveryMap.tsx        # Leaflet map — polylines, markers, popups
│   │   │   ├── FleetPanel.tsx         # Route list + expandable stop details
│   │   │   ├── MetricsBar.tsx         # Distance / improvement / stop count
│   │   │   └── SimulationControls.tsx # City, stop count, vehicle count, run button
│   │   ├── hooks/
│   │   │   └── useRouteWebSocket.ts   # WebSocket connection + keep-alive
│   │   ├── services/
│   │   │   └── api.ts                 # Typed fetch wrappers
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── infra/
│   ├── terraform/                     # VPC, EC2, RDS, ElastiCache, security groups
│   └── DEPLOY.md                      # Step-by-step AWS deployment guide
├── .github/
│   └── workflows/
│       ├── ci.yml                     # pytest + Docker build on every push
│       └── deploy.yml                 # SSH deploy to EC2 on merge to main
├── docker-compose.yml
└── .env.example
```

---

## Getting Started

### Local Development

```bash
git clone https://github.com/AdithNG/lastmile
cd lastmile
cp .env.example .env
docker compose up --build

# Backend API + docs:  http://localhost:8000/docs
# Frontend dashboard:  http://localhost:3000
```

The system works without any API keys — distances use haversine fallback. For real road distances, add a free [OpenRouteService](https://openrouteservice.org) key to `.env` and keep stop count ≤ 49 (ORS free tier cap).

### Run Tests

```bash
docker compose exec backend python -m pytest tests/ -v
# 25 passed in ~1s
```

### Production Deploy (AWS)

See [`infra/DEPLOY.md`](infra/DEPLOY.md) for the full guide. The short version:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # fill in your values
terraform init && terraform apply              # ~8 minutes
```

Then add `EC2_HOST` and `EC2_SSH_KEY` to GitHub Secrets — every push to `main` auto-deploys.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/simulation/start` | Generate scenario (depot + vehicles + stops) for a city |
| POST | `/routes/optimize` | Submit optimization job, returns `job_id` |
| GET | `/routes/{job_id}/status` | Poll: `queued → done / failed` |
| GET | `/routes/{route_id}/detail` | Full stop data: lat/lng, address, time window, weight |
| POST | `/routes/{route_id}/reroute` | Recompute ETAs with traffic delay factors |
| WS | `/routes/ws/{route_id}` | Live rerouted stop sequence |
| POST | `/simulation/inject-traffic` | Generate synthetic traffic events for demo |
| GET | `/health` | Health check |

Interactive docs at `/docs` (Swagger UI) after starting the backend.

---

## Interview Talking Points

**Why is CVRPTW NP-hard?**
With N stops and V vehicles the assignment space is factorial. For 20 stops and 3 vehicles there are more combinations than atoms in the observable universe — exact solvers become infeasible above ~50 stops.

**Why greedy + 2-opt instead of an exact solver?**
Greedy builds a feasible solution in O(n²). 2-opt improves it by reversing sub-segments until no swap reduces distance — typically 10–20% improvement. It runs in seconds, scales to hundreds of stops, and produces routes within ~5–15% of optimal. Exact solvers like branch-and-bound take exponential time and are impractical for real operations. This is the same tradeoff Amazon makes.

**What would you add next?**
Or-opt (move chains of 2–3 stops between routes), Lin-Kernighan (stronger edge swaps), or reinforcement learning (Amazon's DDP approach — a policy network trained on historical driver behavior to sequence stops).

---

## Resume Bullets

- Implemented a **CVRPTW route optimization engine** in Python using greedy nearest-neighbor construction and 2-opt local search, achieving 10–20% distance reduction over naive assignment across fleets of 3–10 vehicles and 5–50 stops
- Designed an **async optimization pipeline** with FastAPI, Celery, and Redis — the API returns a job ID immediately and the solver runs in a background worker, enabling non-blocking optimization for concurrent requests
- Built **real-time traffic rerouting** via WebSocket: when a traffic event fires, the rerouter rebuilds the time matrix with delay factors, recomputes all remaining ETAs, and pushes the updated stop sequence to the frontend without a page refresh
- Provisioned the full AWS stack using **Terraform** (VPC, EC2, RDS PostgreSQL, ElastiCache Redis) with a GitHub Actions CD pipeline that SSHes into EC2, rebuilds Docker containers, runs Alembic migrations, and health-checks the API on every merge to main

---

## Why This Project

Amazon co-hosted the **Last Mile Routing Research Challenge with MIT** to solve exactly this problem. Their internal DDP (Dynamic Dispatch Platform) uses reinforcement learning to optimize tens of millions of deliveries. LastMile is a technically rigorous, end-to-end implementation of the same problem domain — fully runnable in one command with Docker Compose.
