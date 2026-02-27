# LastMile
> A real-time delivery route optimization engine — built to demonstrate mastery of the core problem Amazon Logistics solves at scale.

---

## Why This Project

Amazon ran the **Last Mile Routing Research Challenge** with MIT to solve exactly this problem. Their internal system (DDP — Dynamic Dispatch Platform) uses reinforcement learning to optimize tens of millions of deliveries. This project is your simplified but technically rigorous implementation of that same problem domain.

When an Amazon interviewer asks about your project, you say:
> "I built a route optimization engine that models the same core problem as Amazon's DDP system — the Capacitated Vehicle Routing Problem with Time Windows — using a greedy nearest-neighbor heuristic with 2-opt improvement, real-time traffic integration, and a live React dashboard."

That is a 30-minute interview conversation. Not a 2-minute one.

---

## What This Project Actually Is (Plain English)

You have:
- A **depot** (warehouse/distribution center) where drivers start
- A set of **delivery stops** (addresses with coordinates)
- A fleet of **drivers/vehicles** (each with capacity limits)
- **Time windows** per stop (customer is only home 2–4pm)
- **Real-time traffic** that changes travel time between stops

Your system must answer: **"What is the most efficient set of routes to assign to each driver so all packages are delivered on time, no vehicle is overloaded, and total distance/time is minimized?"**

This is called the **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** — one of the most studied NP-hard problems in computer science. Amazon processes this for millions of stops daily.

---

## The Core Algorithm (This Is The Heart of the Project)

### Phase 1: Nearest Neighbor Heuristic (Greedy Construction)
Build an initial solution fast:
1. Start at depot
2. Assign the nearest unvisited stop to the current driver's route
3. Check: does adding this stop violate capacity or time window constraints?
4. If yes → close this route, start a new driver's route
5. Repeat until all stops are assigned

This gives you a **feasible but not optimal** solution in O(n²) time.

### Phase 2: 2-Opt Local Search (Improvement)
Improve the greedy solution:
- Take any two edges in a route: (A→B) and (C→D)
- Try reversing the segment between them: (A→C) and (B→D)
- If the new total distance is shorter AND time windows are still satisfied → accept the swap
- Repeat until no improving swap exists

This is the same class of improvement used in Amazon's DDP system. It's simple to implement but produces dramatically better routes.

### Phase 3: Real-Time Rerouting
When a driver is already on the road:
- Receive live traffic update (via HERE Maps or OpenRouteService API)
- Recalculate remaining stops on that driver's route
- If a time window is at risk → trigger rerouting via the API
- Push updated route to the driver's "mobile" view

This is what separates a toy project from a real system.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python, FastAPI | Amazon's preferred languages; async support for real-time updates |
| Algorithm | Python (NumPy, SciPy) | Matrix distance calculations, route scoring |
| Task Queue | Celery + Redis | Async route computation without blocking API |
| Database | PostgreSQL | Store routes, stops, drivers, delivery history |
| Cache | Redis | Cache distance matrices, active route state |
| Mapping API | OpenRouteService (free) or HERE Maps | Real driving distances, traffic data |
| Frontend | React + TypeScript | Live map dashboard |
| Map Visualization | Leaflet.js (via react-leaflet) | Open source, free, renders routes on map |
| Cloud | AWS (EC2, RDS, ElastiCache, S3) | Aligns directly with Amazon interviews |
| Containerization | Docker + Docker Compose | |
| CI/CD | GitHub Actions | |

---

## What You're Actually Building (Feature by Feature)

### Core Engine
- **Distance matrix builder** — given N stops, compute an N×N matrix of real driving distances/times using the mapping API. This is the foundation everything else runs on.
- **CVRPTW solver** — the greedy + 2-opt algorithm described above, implemented in pure Python with NumPy for matrix operations
- **Constraint validator** — checks every proposed route assignment against capacity limits and time windows before accepting it
- **Route scorer** — scores a complete solution by total distance, total time, and number of constraint violations

### API Layer (FastAPI)
- Accept a JSON payload of stops (lat/lng, time window, package weight)
- Trigger async route computation via Celery worker
- Return optimized route assignments per driver with ETA per stop
- Accept real-time traffic webhook and trigger rerouting
- WebSocket endpoint for live route updates to the frontend

### Data Models
```
Depot: id, name, lat, lng, open_time, close_time
Vehicle: id, depot_id, capacity_kg, driver_name
Stop: id, address, lat, lng, earliest_time, latest_time, package_weight_kg, status
Route: id, vehicle_id, date, stops (ordered list), total_distance_km, total_time_min
RouteStop: route_id, stop_id, sequence, planned_arrival, actual_arrival
```

### Frontend Dashboard (React + TypeScript)
- **Map view** — Leaflet map showing depot, all stops as pins, and each driver's route as a colored polyline
- **Fleet panel** — list of all drivers with their route summary (stops, distance, ETA)
- **Stop detail** — click any pin to see package info, time window, planned arrival
- **Live reroute indicator** — when rerouting triggers, animate the route change on the map
- **Metrics panel** — total fleet distance, on-time delivery %, average stops per driver, utilization %

### Simulation Mode (This Makes It Demonstrable)
Since you don't have real drivers, build a simulator:
- Generate a random set of N stops around a city (use real coordinates from a city like LA or Seattle)
- Assign realistic time windows (morning slots, afternoon slots)
- Assign random package weights
- Run the optimizer
- "Play" the simulation — animate drivers moving along their routes in real time on the map
- Inject a random traffic event mid-simulation and watch routes update live

This is the **demo moment** — you show an interviewer a live animated map of routes being optimized and rerouted in real time.

---

## Folder Structure

```
lastmile/
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI entry point + WebSocket
│   │   ├── config.py                    # Settings, env vars
│   │   ├── database.py                  # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── depot.py
│   │   │   ├── vehicle.py
│   │   │   ├── stop.py
│   │   │   └── route.py
│   │   ├── routers/
│   │   │   ├── routes.py                # Route generation endpoints
│   │   │   ├── stops.py                 # Stop CRUD
│   │   │   ├── vehicles.py              # Vehicle/driver management
│   │   │   └── simulation.py            # Simulation control endpoints
│   │   ├── services/
│   │   │   ├── distance_matrix.py       # Calls mapping API, builds N×N matrix
│   │   │   ├── optimizer.py             # CVRPTW solver (greedy + 2-opt)
│   │   │   ├── constraint_checker.py    # Time window + capacity validation
│   │   │   ├── rerouter.py              # Real-time rerouting logic
│   │   │   └── simulator.py            # Fake driver movement for demo
│   │   └── workers/
│   │       └── celery_tasks.py          # Async route computation tasks
│   ├── tests/
│   │   ├── test_optimizer.py            # Unit tests for routing algorithm
│   │   ├── test_constraints.py
│   │   └── test_distance_matrix.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DeliveryMap.tsx          # Leaflet map with routes + pins
│   │   │   ├── FleetPanel.tsx           # Driver list + route summaries
│   │   │   ├── MetricsBar.tsx           # KPI summary bar
│   │   │   ├── StopDetail.tsx           # Click-to-inspect stop info
│   │   │   └── SimulationControls.tsx   # Play/pause/speed simulation
│   │   ├── hooks/
│   │   │   └── useRouteWebSocket.ts     # WebSocket connection for live updates
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/routes/optimize` | Submit stops + vehicles, returns `job_id` for polling |
| GET | `/routes/{job_id}/status` | Poll optimization result: `queued → done / failed` |
| GET | `/routes/{route_id}/stops` | Ordered stop list (sequence + ETA) |
| GET | `/routes/{route_id}/detail` | Full stop data: lat/lng, address, time windows, weight |
| POST | `/routes/{route_id}/reroute` | Recompute ETAs with traffic delay factors applied |
| WS | `/routes/ws/{route_id}` | WebSocket — live rerouted stop sequence |
| POST | `/simulation/start` | Generate a realistic scenario (depot + vehicles + stops) |
| POST | `/simulation/inject-traffic` | Build synthetic traffic event list for rerouting demo |
| GET | `/stops` | List all stops |
| POST | `/stops` | Create a stop |
| GET | `/vehicles` | List fleet |
| GET | `/health` | Health check |

---

## The Algorithmic Depth (What You Talk About in Interviews)

### Why is this NP-hard?
With N stops and V vehicles, the number of possible route assignments is factorial. For just 20 stops and 3 vehicles, that's more combinations than atoms in the observable universe. You cannot brute force it. You need heuristics.

### Why greedy + 2-opt?
- Greedy nearest-neighbor builds a solution in O(n²) — fast enough for real-time use
- 2-opt improvement typically reduces total distance by 10–20% over greedy alone
- Amazon's research shows 2-opt variants outperform exact solvers on large real-world instances because exact solvers become infeasible above ~50 stops

### What's the tradeoff you made?
Optimality vs. speed. A true optimal solution for 100 stops is computationally intractable. Your 2-opt heuristic runs in seconds and gets within ~5–15% of optimal — acceptable for real operations. This is the exact same tradeoff Amazon makes.

### What would you do to improve it further?
- **Or-opt**: move chains of 2–3 stops between routes (stronger than 2-opt)
- **Lin-Kernighan**: more powerful edge-swap heuristic
- **Reinforcement learning**: Amazon's DDP approach — train a policy network to sequence stops based on historical driver behavior
- **Simulated annealing**: accept worse solutions occasionally to escape local optima

You don't need to implement these. But knowing them makes you dangerous in an interview.

---

## Environment Variables

```env
# App
SECRET_KEY=your_secret
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/lastmile
REDIS_URL=redis://localhost:6379

# Mapping API
ORS_API_KEY=your_openrouteservice_key   # Free tier: 2000 req/day

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis

  worker:
    build: ./backend
    command: celery -A app.workers.celery_tasks worker --loglevel=info
    env_file: .env
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: lastmile
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

---

## Build Status

| Component | Status | Notes |
|-----------|--------|-------|
| Data models (SQLAlchemy) | ✅ Done | Depot, Vehicle, Stop, Route, RouteStop |
| Alembic migrations | ✅ Done | Full DDL in `versions/`, runs on container start |
| Distance matrix | ✅ Done | ORS API + haversine fallback |
| Constraint checker | ✅ Done | Time windows + capacity validation |
| CVRPTW solver (greedy + 2-opt) | ✅ Done | 25 unit tests, 0 warnings |
| Celery async task queue | ✅ Done | Redis broker, async worker |
| FastAPI REST + WebSocket | ✅ Done | `/optimize`, `/detail`, `/reroute`, `/ws/{id}` |
| Simulation engine | ✅ Done | Seattle / LA / NYC scenarios |
| React + Leaflet frontend | ✅ Done | Map, fleet panel, metrics bar, traffic button |
| Live traffic reroute demo | ✅ Done | WebSocket push, ETAs update on map |
| Docker Compose | ✅ Done | 5 services, healthchecks |
| GitHub Actions CI/CD | ✅ Done | pytest → Docker build → SSH deploy to EC2 |
| AWS deployment (IaC) | ✅ Done | Terraform: VPC, EC2, RDS, ElastiCache — see `infra/` |

---

## Getting Started (Dev)

```bash
git clone https://github.com/AdithNG/lastmile
cd lastmile
cp .env.example .env
# Add your OpenRouteService API key (free at openrouteservice.org)
docker-compose up --build

# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

---

## Resume Bullets (Once Built)

- Built a real-time **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)** solver in Python using greedy nearest-neighbor construction and 2-opt local search improvement, reducing total route distance by up to 20% over naive assignment
- Designed an async optimization pipeline using **FastAPI, Celery, and Redis** capable of processing 100-stop scenarios in under 3 seconds
- Implemented **live route rerouting** triggered by real-time traffic events via WebSocket, updating active driver routes without service interruption
- Built a full simulation and visualization layer using **React, TypeScript, and Leaflet.js** with animated driver movement and live route state on an interactive map
- Deployed the full stack on **AWS (EC2, RDS, ElastiCache)** with Docker and a GitHub Actions CI/CD pipeline

---

## Why This Impresses Amazon Specifically

- It's in **their exact problem domain** — Amazon Logistics solves CVRPTW millions of times per day
- It demonstrates **algorithmic thinking**, not just API glue — you can explain NP-hardness, heuristics, and tradeoffs
- The **async architecture** (FastAPI + Celery + Redis + WebSocket) mirrors how Amazon's distributed systems are actually built
- It's **deployed on AWS** — you're showing comfort with the platform they sell
- Amazon literally co-hosted a **research challenge at MIT** on this exact problem. You built your own version.
