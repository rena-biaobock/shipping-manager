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

**Stock model:** each physical bundle of pipes or components carries a barcode label (`progressivo`). Every row in the system is one label. Labels belong to a product (`Item` code), sit in a two-level warehouse location (`Deposito` → `Endereço`), may be assigned to a customer order, and are tracked by periodic warehouse scans.

Two core objectives:
1. **Stock Control** — label registry with status lifecycle, warehouse location, order assignment, and scan-based idle tracking
2. **Bin-Packing** — automatic truck load generation using `volume_tons` and `actual_length_m` as constraints, with filters for market type (MI/ME), destination country, and order condition

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

# Idle threshold (days without scanning before a label is flagged as idle)
IDLE_SCAN_THRESHOLD_DAYS=30
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
│   │   │       │   ├── products.py       # product catalogue
│   │   │       │   ├── stock_labels.py   # physical labels / inventory
│   │   │       │   ├── orders.py
│   │   │       │   ├── trucks.py
│   │   │       │   ├── shipments.py
│   │   │       │   └── bin_packing.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py                 # Settings via pydantic-settings
│   │   │   ├── database.py               # Async engine + session factory
│   │   │   └── security.py
│   │   ├── models/                       # SQLAlchemy ORM models
│   │   │   ├── base.py
│   │   │   ├── product.py
│   │   │   ├── stock_label.py
│   │   │   ├── order.py
│   │   │   ├── truck.py
│   │   │   ├── shipment.py
│   │   │   └── load_item.py
│   │   ├── schemas/                      # Pydantic request/response schemas
│   │   │   ├── product.py
│   │   │   ├── stock_label.py
│   │   │   ├── order.py
│   │   │   ├── truck.py
│   │   │   ├── shipment.py
│   │   │   └── bin_packing.py
│   │   ├── services/
│   │   │   ├── stock_service.py
│   │   │   ├── order_service.py
│   │   │   ├── shipment_service.py
│   │   │   └── bin_packing_service.py
│   │   ├── jobs/
│   │   │   ├── celery_app.py
│   │   │   ├── stock_snapshot.py
│   │   │   ├── idle_label_watchdog.py
│   │   │   └── report_generator.py
│   │   ├── repositories/
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
│   │   │   ├── ui/
│   │   │   ├── stock/
│   │   │   └── bin-packing/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Stock.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Trucks.tsx
│   │   │   └── Shipments.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
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

### `products` — steel pipe / component catalogue
One row per unique product code (`item_code`). The `description` field encodes pipe specs as `{OD}x{wall}x{length}-{standard}-{class} {threading} {treatment}` (e.g. `60,30x3,00x6000-NBR5580-CL Rir BSP Galv`).

```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
item_code         VARCHAR(32) UNIQUE NOT NULL     -- source: "Item"
description       VARCHAR(512) NOT NULL           -- source: "Descricao"
nominal_length_m  NUMERIC(8,2)                    -- 6.0 or 12.0 for pipes
standard          VARCHAR(64)                     -- NBR5580, API5L, ASTM A572, …
active            BOOLEAN DEFAULT TRUE
created_at        TIMESTAMPTZ DEFAULT now()
updated_at        TIMESTAMPTZ DEFAULT now()
```

### `stock_labels` — physical inventory labels (one row = one barcode tag)
Each label represents a physical bundle of one product sitting in a warehouse location.

```sql
progressivo         VARCHAR(64) PRIMARY KEY        -- source: "progressivo" (barcode)
product_id          UUID REFERENCES products(id)
customer_item_ref   VARCHAR(128)                   -- source: "Cliente Item"
actual_length_m     NUMERIC(8,3)                   -- source: "Comprimento Real" (may be NULL for plates/fittings)
warehouse_code      VARCHAR(32) NOT NULL           -- source: "Deposito"  (e.g. '2', 'A12', 'B08')
address             VARCHAR(32)                    -- source: "Endereço"  (rack/bin, e.g. 'E10', 'J16')
location_detail     VARCHAR(128)                   -- source: "Localizacao"
market_type         market_type NOT NULL           -- enum: MI | ME
is_standard_bundle  BOOLEAN                        -- source: "Fardo Padrão"
volume_tons         NUMERIC(10,4) NOT NULL         -- source: "Volume Geral" (metric tons)
piece_count         INTEGER NOT NULL               -- source: "Qt PC"
status              label_status NOT NULL          -- see enum below
order_id            UUID REFERENCES orders(id)     -- NULL when has_order = false
embarque_id         VARCHAR(32)                    -- source: "Embarque Fifo" / "Embarque Etiq" (shipment ref when non-zero)
scan_count          INTEGER DEFAULT 0              -- source: "Qtd Escaneamentos"
last_scanned_at     TIMESTAMPTZ                    -- source: "Ultimo Escaneamento" (convert from Excel serial float)
days_without_scan   INTEGER                        -- source: "Dias sem Escanear" (denormalised for queries)
avg_days_idle       INTEGER                        -- source: "Média dias Parado"
created_at          TIMESTAMPTZ DEFAULT now()
updated_at          TIMESTAMPTZ DEFAULT now()
```

**`label_status` enum:** `available` | `reserved` | `in_shipment` | `delivered` | `idle` | `damaged`

Derivation from source data:
- `available` — `Tem Pedido? = Não`, no embarque
- `reserved` — `Tem Pedido? = Sim`, no embarque yet
- `in_shipment` — `Embarque Fifo/Etiq` is a non-zero order number
- `idle` — flagged by watchdog when `Dias sem Escanear ≥ IDLE_SCAN_THRESHOLD_DAYS`

### `orders` — customer orders
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
order_number    VARCHAR(64) UNIQUE NOT NULL    -- source: "Pedido"
client_order_ref VARCHAR(64)                  -- source: "Ped Cli"
customer        VARCHAR(255)                  -- source: "Cliente"
country         VARCHAR(64)                   -- source: "País" (Brasil, Paraguai, Uruguai, Bolivia, Argentina)
market_type     market_type NOT NULL          -- MI | ME
condition       order_condition NOT NULL      -- see enum below
exit_date       DATE                          -- source: "Data Saida Pedido"
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

**`order_condition` enum:** `fixo_futuro` | `pedido_ate_hoje` | `antecipa_futuro` | `fixo_mes_atual` | `antecipa_mes_atual`

**`market_type` enum:** `MI` (Mercado Interno / domestic) | `ME` (Mercado Externo / export)

### `trucks`
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
name            VARCHAR(128) NOT NULL
plate           VARCHAR(32) UNIQUE
max_weight_tons NUMERIC(10,3) NOT NULL   -- capacity in metric tons (matches volume_tons unit)
length_m        NUMERIC(8,2) NOT NULL
width_m         NUMERIC(8,2) NOT NULL
height_m        NUMERIC(8,2) NOT NULL
active          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMPTZ DEFAULT now()
```

### `shipments` — confirmed truck load plans
```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
truck_id          UUID REFERENCES trucks(id)
status            shipment_status NOT NULL   -- see enum below
destination       VARCHAR(255)
customer          VARCHAR(255)
country           VARCHAR(64)
market_type       market_type
notes             TEXT
total_weight_tons NUMERIC(10,3)
scheduled_at      TIMESTAMPTZ
dispatched_at     TIMESTAMPTZ
delivered_at      TIMESTAMPTZ
created_at        TIMESTAMPTZ DEFAULT now()
updated_at        TIMESTAMPTZ DEFAULT now()
```

**`shipment_status` enum:** `draft` | `confirmed` | `loading` | `dispatched` | `delivered` | `cancelled`

### `load_items` — labels assigned to a shipment
```sql
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
shipment_id         UUID REFERENCES shipments(id)
stock_label_id      VARCHAR(64) REFERENCES stock_labels(progressivo)
position_data       JSONB    -- bin-packing coordinates {x, y, z, rotation}
```

---

## Services, Jobs, and Models

### Back-end Services
| Service | Responsibility |
|---------|---------------|
| `StockService` | CRUD labels, validate `label_status` transitions, filter by warehouse/product/order/status |
| `OrderService` | Link/unlink orders to labels, manage `order_condition` transitions |
| `ShipmentService` | Create/confirm/dispatch shipments, aggregate `volume_tons` against truck capacity |
| `BinPackingService` | Given a set of labels + a truck, return an optimal load plan. Primary packing metric: `volume_tons`. Primary dimensional constraint: `actual_length_m` (critical — standard pipe lengths are 6 m and 12 m). Available filters: `market_type` (MI/ME), `country`, `order_condition`, `exit_date` range. Algorithm: First Fit Decreasing on `volume_tons`, then verify length fits truck `length_m`, then check total weight ≤ `max_weight_tons`. Returns best partial plan when `max_iterations` cap is hit, flagged as `partial: true`. |

### Celery Jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| `stock_snapshot` | Daily 02:00 | Snapshot label counts and total volume_tons per warehouse_code + status to a history table |
| `idle_label_watchdog` | Every 15 min | Set `status = 'idle'` on labels where `days_without_scan ≥ IDLE_SCAN_THRESHOLD_DAYS` |
| `report_generator` | Monday 06:00 | Generate weekly stock + shipment summary (CSV + PDF) |

### Front-end Pages & Components
| Page | Key Components |
|------|---------------|
| `Dashboard` | KPI cards (total labels, total tons, idle count, reserved), low-stock alerts, recent shipments |
| `Stock` | Label list with filters (warehouse, status, market_type, idle flag), scan info, status transitions |
| `Orders` | Order list, link/unlink labels, order condition badge |
| `Trucks` | Truck capacity cards |
| `Shipments` | Shipment list, bin-packing wizard (select truck + filters → proposed load), load visualiser |

---

## Common Hurdles

### Excel serial date to Python datetime (`Ultimo Escaneamento`)
**Problem:** Excel stores dates as floats (days since 1900-01-01, with a leap-year bug). The `Ultimo Escaneamento` column arrives as e.g. `46099.656`.
**Fix:**
```python
from datetime import datetime, timedelta
EXCEL_EPOCH = datetime(1899, 12, 30)
def excel_serial_to_dt(serial: float) -> datetime:
    return EXCEL_EPOCH + timedelta(days=serial)
```

### Async SQLAlchemy session in tests
**Problem:** `AsyncSession` requires a running event loop; pytest's default loop is torn down between tests.
**Fix:** Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pytest.ini` and a `session`-scoped `event_loop` fixture. Share one test database across the session; truncate tables between tests, do not recreate the schema.

### Alembic with async engine
**Problem:** Alembic's `env.py` is synchronous by default.
**Fix:** Use `run_async_migrations()` pattern — create a sync engine via `create_engine(url.render_as_string(hide_password=False))` only inside the Alembic migration context, keeping the app's async engine separate.

### `actual_length_m` is NULL for ~30 % of labels
**Problem:** Plates, fittings, and other non-pipe items don't have a length.
**Fix:** In `BinPackingService`, treat `actual_length_m = NULL` as "no length constraint" — only enforce the truck's `length_m` constraint when the field is present.

### Bin-Packing accuracy vs. performance
**Problem:** 3D bin-packing is NP-hard; brute-force is too slow for large orders.
**Fix:** Use FFD on `volume_tons` (dominant metric), then verify `actual_length_m ≤ truck.length_m` per label and cumulative `volume_tons ≤ truck.max_weight_tons`. Expose a `max_iterations` cap and return the best partial solution when the cap is hit, clearly flagging it as `partial`.

### TanStack Query cache invalidation after mutations
**Problem:** After creating/updating a shipment the stock label list is stale.
**Fix:** In mutation `onSuccess`, call `queryClient.invalidateQueries({ queryKey: ['stock-labels'] })` alongside the shipment key. Group related keys under a shared prefix.

### CORS in development
**Problem:** Vite dev server (`:5173`) hits FastAPI (`:8000`).
**Fix:** Set `ALLOWED_ORIGINS=http://localhost:5173` in `.env` and configure `CORSMiddleware` in `main.py`. Do not use `allow_origins=["*"]`.

---

## Design Patterns

- **Repository pattern** — all DB queries live in `repositories/`; services depend on repository interfaces, not SQLAlchemy directly.
- **Service layer** — business logic and state machine transitions live in `services/`, never in route handlers.
- **Schema separation** — distinct Pydantic schemas for Create, Update, Read, and DB model.
- **State machine for status** — valid transitions declared as a dict; service raises `InvalidTransitionError` for illegal moves.
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
| Mon 06:00 | `report_generator` | Weekly stock + shipment CSV/PDF |
| Daily 02:00 | `stock_snapshot` | Appends to history table (label counts + total tons per warehouse + status) |
| Every 15 min | `idle_label_watchdog` | Sets `status = 'idle'` on labels where `days_without_scan ≥ IDLE_SCAN_THRESHOLD_DAYS` |
| On demand | `bin_packing` API call | Returns load plan for a given truck + filtered label set |

---

## Post-Implementation Checklist

- [ ] All new models have an Alembic migration
- [ ] All new endpoints have integration tests (happy path + at least one error case)
- [ ] All new service methods have unit tests written before implementation (TDD)
- [ ] `label_status` and `shipment_status` transitions are validated in the service layer
- [ ] `actual_length_m` NULL case is handled in any code that touches pipe dimensions
- [ ] Excel serial date fields are always converted via `excel_serial_to_dt()` before persisting
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
