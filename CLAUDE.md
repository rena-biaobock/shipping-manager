# CLAUDE.md

Guidance for Claude Code when working in this repository.

---

## Architecture Overview

`shipping-manager` is a web application for a steel pipe industry to control stock and automate truck load planning via a Bin-Packing algorithm.

```
┌─────────────────┐     REST/JSON     ┌──────────────────┐
│  React + TS     │ ◄───────────────► │  Python FastAPI  │
│  (Dashboard)    │                   │  (API)           │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                    ┌──────────┴──────────┐
                                    │                     │
                              ┌─────▼──────┐     ┌───────▼──────┐
                              │ PostgreSQL  │     │    Redis      │
                              │ (primary)  │     │ (cache/queue) │
                              └────────────┘     └──────────────┘
```

Two core objectives:
1. **Stock Control** — item registry with per-item status lifecycle management
2. **Bin-Packing** — automatic truck load generation with weight, volume, and dimension constraints

---

## Technology Stack

### Back-end
| Component | Choice |
|-----------|--------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Task queue | Celery + Redis |
| Auth | JWT (python-jose) |
| Testing | pytest + pytest-asyncio + httpx |
| Style | Black + Flake8 + isort |
| Security | Bandit |
| Vulnerability scan | pip-audit |

### Front-end
| Component | Choice |
|-----------|--------|
| Language | TypeScript 5.x |
| Framework | React 18 |
| Build | Vite |
| UI / Dashboard | shadcn/ui + Recharts |
| State | Zustand |
| Data fetching | TanStack Query v5 |
| Forms | React Hook Form + Zod |
| Testing | Vitest + React Testing Library |
| Style | Tailwind CSS |

### Infrastructure
| Component | Choice |
|-----------|--------|
| Database | PostgreSQL 16 |
| Cache / Queue broker | Redis 7 |
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Environment Variables

### Back-end (`backend/.env`)
```dotenv
# App
APP_ENV=development          # development | staging | production
SECRET_KEY=changeme          # JWT signing key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+asyncpg://shipping:shipping@localhost:5432/shipping_manager

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=http://localhost:5173

# Pagination
DEFAULT_PAGE_SIZE=25
MAX_PAGE_SIZE=100
```

### Front-end (`frontend/.env`)
```dotenv
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Directory Structure

```
shipping-manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes/
│   │   │       │   ├── auth.py
│   │   │       │   ├── stock.py          # items + stock entries
│   │   │       │   ├── trucks.py
│   │   │       │   ├── shipments.py
│   │   │       │   └── bin_packing.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py                 # Settings via pydantic-settings
│   │   │   ├── database.py               # Async engine + session factory
│   │   │   └── security.py              # JWT helpers
│   │   ├── models/                       # SQLAlchemy ORM models
│   │   │   ├── base.py
│   │   │   ├── item.py
│   │   │   ├── stock_entry.py
│   │   │   ├── truck.py
│   │   │   ├── shipment.py
│   │   │   └── load_item.py
│   │   ├── schemas/                      # Pydantic request/response schemas
│   │   │   ├── item.py
│   │   │   ├── stock_entry.py
│   │   │   ├── truck.py
│   │   │   ├── shipment.py
│   │   │   └── bin_packing.py
│   │   ├── services/                     # Business logic (no ORM, no HTTP)
│   │   │   ├── stock_service.py
│   │   │   ├── shipment_service.py
│   │   │   └── bin_packing_service.py   # Core algorithm
│   │   ├── jobs/                         # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── stock_snapshot.py         # Daily snapshot job
│   │   │   └── report_generator.py       # Weekly PDF/CSV report
│   │   ├── repositories/                 # DB access layer (one per model)
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   │   └── services/
│   │   ├── integration/
│   │   │   └── api/
│   │   └── conftest.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                       # shadcn primitives
│   │   │   ├── stock/
│   │   │   └── bin-packing/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Stock.tsx
│   │   │   ├── Trucks.tsx
│   │   │   └── Shipments.tsx
│   │   ├── hooks/                        # Custom React hooks
│   │   ├── services/                     # API client functions
│   │   ├── store/                        # Zustand slices
│   │   └── types/                        # Shared TypeScript types
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

---

## Database Schemas

### `items` — steel pipe catalogue
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
sku           VARCHAR(64) UNIQUE NOT NULL
name          VARCHAR(255) NOT NULL
description   TEXT
diameter_mm   NUMERIC(8,2)
length_m      NUMERIC(8,2)
weight_kg     NUMERIC(8,2)           -- weight per unit
unit          VARCHAR(32)            -- 'piece' | 'meter' | 'kg'
active        BOOLEAN DEFAULT TRUE
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ DEFAULT now()
```

### `stock_entries` — inventory movements
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
item_id       UUID REFERENCES items(id)
quantity      NUMERIC(10,2) NOT NULL
status        stock_status NOT NULL   -- enum below
location      VARCHAR(128)            -- warehouse bin/rack code
batch_number  VARCHAR(64)
notes         TEXT
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ DEFAULT now()
```

**`stock_status` enum:** `available` | `reserved` | `in_transit` | `delivered` | `damaged` | `quarantine`

### `trucks`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
name          VARCHAR(128) NOT NULL
plate         VARCHAR(32) UNIQUE
max_weight_kg NUMERIC(10,2) NOT NULL
length_m      NUMERIC(8,2) NOT NULL
width_m       NUMERIC(8,2) NOT NULL
height_m      NUMERIC(8,2) NOT NULL
active        BOOLEAN DEFAULT TRUE
created_at    TIMESTAMPTZ DEFAULT now()
```

### `shipments` — truck load plans
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
truck_id      UUID REFERENCES trucks(id)
status        shipment_status NOT NULL  -- enum below
destination   VARCHAR(255)
customer      VARCHAR(255)
notes         TEXT
total_weight_kg NUMERIC(10,2)
scheduled_at  TIMESTAMPTZ
dispatched_at TIMESTAMPTZ
delivered_at  TIMESTAMPTZ
created_at    TIMESTAMPTZ DEFAULT now()
updated_at    TIMESTAMPTZ DEFAULT now()
```

**`shipment_status` enum:** `draft` | `confirmed` | `loading` | `dispatched` | `delivered` | `cancelled`

### `load_items` — items assigned to a shipment
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
shipment_id      UUID REFERENCES shipments(id)
stock_entry_id   UUID REFERENCES stock_entries(id)
quantity         NUMERIC(10,2) NOT NULL
position_data    JSONB           -- bin-packing coordinates {x,y,z}
```

---

## Services, Jobs, and Models

### Back-end Services
| Service | Responsibility |
|---------|---------------|
| `StockService` | CRUD items, transitions between `stock_status` states, availability checks |
| `ShipmentService` | Create/confirm/dispatch shipments, aggregate weight and volume |
| `BinPackingService` | Given a list of items + truck constraints, return an optimal load plan using First Fit Decreasing (FFD) algorithm with configurable filters (priority, destination, due date) |

### Celery Jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| `stock_snapshot` | Daily 02:00 | Snapshot stock levels to a history table for trend reporting |
| `report_generator` | Monday 06:00 | Generate weekly stock + shipment summary (CSV + PDF) |
| `status_watchdog` | Every 15 min | Flag stock entries unchanged for > 30 days |

### Front-end Pages & Components
| Page | Key Components |
|------|---------------|
| `Dashboard` | KPI cards, low-stock alerts, recent shipments table |
| `Stock` | Item list + filters, status badge, inline status transition |
| `Trucks` | Truck capacity cards |
| `Shipments` | Shipment list, bin-packing wizard, load visualiser |

---

## Common Hurdles

### Async SQLAlchemy session in tests
**Problem:** `AsyncSession` requires a running event loop; pytest's default loop is torn down between tests.
**Fix:** Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pytest.ini` and a `session`-scoped `event_loop` fixture. Share one test database across the session; truncate tables between tests, do not recreate the schema.

### Alembic with async engine
**Problem:** Alembic's `env.py` is synchronous by default.
**Fix:** Use `run_async_migrations()` pattern — create a sync engine via `create_engine(url.render_as_string(hide_password=False))` only inside the Alembic migration context, keeping the app's async engine separate.

### Bin-Packing accuracy vs. performance
**Problem:** 3D bin-packing is NP-hard; brute-force is too slow for large orders.
**Fix:** Use FFD on the dominant dimension (length for steel pipes), then verify weight and volume constraints. Expose a `max_iterations` cap and return the best partial solution when the cap is hit, clearly flagging it as `partial`.

### TanStack Query cache invalidation after mutations
**Problem:** After creating/updating a shipment the stock list is stale.
**Fix:** In mutation `onSuccess`, call `queryClient.invalidateQueries({ queryKey: ['stock'] })` alongside the shipment key. Group related keys under a shared prefix (e.g. `['stock']`, `['shipments']`).

### CORS in development
**Problem:** Vite dev server (`:5173`) hits FastAPI (`:8000`).
**Fix:** Set `ALLOWED_ORIGINS=http://localhost:5173` in `.env` and configure `CORSMiddleware` in `main.py`. Do not use `allow_origins=["*"]` — it masks misconfiguration.

---

## Design Patterns

- **Repository pattern** — all DB queries live in `repositories/`; services depend on repository interfaces, not SQLAlchemy directly. Enables easy test doubles.
- **Service layer** — business logic and state machine transitions live in `services/`, never in route handlers.
- **Schema separation** — distinct Pydantic schemas for Create, Update, Read, and DB model to avoid over-posting.
- **State machine for status** — valid transitions are declared as a dict in the model; the service raises `InvalidTransitionError` for illegal moves.
- **Feature flags via env** — use `Settings` fields to toggle experimental features (e.g. `ENABLE_3D_VISUALISER=false`).
- **TDD** — write the failing test first; implement the minimum code to pass; refactor. Red → Green → Refactor on every change.
- **XP practices** — short iterations, continuous integration on every commit, pair/review all non-trivial logic, refactor relentlessly.

---

## CI Pipeline (runs on every commit)

```
Black + Flake8 + isort   →   pip-audit   →   Bandit   →   pytest + Vitest
    (style)                (vulnerabilities) (static sec)     (tests)
```

All steps must pass before merge. No `# noqa` or `# nosec` without a justification comment.

---

## Weekly Pipeline

| Day / Time | Job | Output |
|-----------|-----|--------|
| Mon 06:00 | `report_generator` | Weekly stock + shipment CSV/PDF emailed to ops team |
| Daily 02:00 | `stock_snapshot` | Appends to `stock_history` for trend dashboard |
| Every 15 min | `status_watchdog` | Creates alert if a stock entry is stale > 30 days |
| On demand | `bin_packing` API call | Returns load plan for a given truck + item selection |

---

## Post-Implementation Checklist

- [ ] All new models have an Alembic migration
- [ ] All new endpoints have integration tests (happy path + at least one error case)
- [ ] All new service methods have unit tests written before implementation (TDD)
- [ ] `stock_status` and `shipment_status` transitions are validated in the service layer
- [ ] New env variables are documented here and added to `.env.example`
- [ ] `pip-audit` and `Bandit` return no new findings
- [ ] Front-end API calls go through `services/` — no raw `fetch` in components
- [ ] TanStack Query keys follow the `['resource', id?]` convention
- [ ] Dashboard KPIs updated to reflect any new stock or shipment states
- [ ] CLAUDE.md updated if architecture, schemas, or environment variables changed

---

## Development Workflow

```bash
# Start all services
docker compose up -d

# Run back-end tests
cd backend && pytest

# Run front-end tests
cd frontend && npm test

# Apply migrations
cd backend && alembic upgrade head

# Create a new migration after model changes
cd backend && alembic revision --autogenerate -m "describe change"
```

Commit convention: one commit per feature / refactor / bug-fix / test. Use imperative mood: `add`, `fix`, `refactor`, `test`, `chore`.
