# CLAUDE.md

Guidance for Claude Code when working in this repository.

---

## Architecture Overview

`shipping-manager` is a web application for a steel pipe industry to control stock and automate truck load planning via a Bin-Packing algorithm.

```
┌─────────────────┐     REST/JSON     ┌──────────────────┐
│  AngularJS      │ ◄───────────────► │  Python FastAPI  │
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
2. **Bin-Packing** — automatic truck load generation using `volume_tons` and `actual_length_m` as constraints, with filters for warehouse, client, and truck capacity

**Visual design reference:** `Shipping Manager.html` in the project root — a self-contained React prototype that defines the exact dark-theme dashboard aesthetic (color palette, typography, layout, component shapes) to be reproduced in AngularJS. Use it as the pixel-perfect model; do not deviate from its look and feel.

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
| Language | JavaScript (ES6+) |
| Framework | AngularJS 1.8.x |
| Build | Webpack 5 |
| UI / Dashboard | Custom CSS — dark theme matching `Shipping Manager.html` |
| State | AngularJS services + `$rootScope` events |
| HTTP | `$http` service |
| Forms | `ngModel` + custom validators |
| Testing | Jasmine + Karma |
| Style | Custom CSS variables (no utility-first framework) |

### Infrastructure
| Component | Choice |
|-----------|--------|
| Database | PostgreSQL 16 |
| Cache / Queue broker | Redis 7 |
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Architectural Decisions

Full rationale is in [README.md](./README.md). Summary of non-obvious choices:

| Decision | Choice | Why |
|----------|--------|-----|
| Back-end framework | FastAPI | Async-native, built-in Pydantic validation, OpenAPI docs. Flask gives nothing; Django gives too much for a pure API. |
| Database | PostgreSQL | Concurrent write safety, native `JSONB` for position data, DB-level `ENUM` enforcement. |
| Redis | Cache + Celery broker | One service covers both needs; no reason to run RabbitMQ + Memcached separately. |
| ORM | SQLAlchemy 2.x async | Sync SQLAlchemy blocks the FastAPI event loop. Tortoise ORM is async but has a less mature migration story. |
| Migrations | Alembic | `--autogenerate` from ORM models. Standard SQLAlchemy companion. |
| Task queue | Celery | Retry logic, job visibility, on-demand triggers from the API. Cron alone provides none of these. |
| Auth | JWT | Single-tenant internal tool; stateless tokens require no session store. |
| Test HTTP client | httpx `AsyncClient` | Tests FastAPI endpoints in-process without a live server; fully async. |
| Style linting | Black + Flake8 + isort | One named tool per concern, matching the CI intent. Ruff is a valid alternative. |
| Front-end framework | AngularJS 1.8.x | Fits the team's existing AngularJS familiarity; two-way binding simplifies dashboard filter state without a separate state library. |
| Front-end CSS | Custom CSS variables | The dark dashboard design (`Shipping Manager.html`) uses a fixed palette; a utility framework adds indirection without benefit. |
| Navigation | Collapsible left sidebar | Three pages (Stock, Loads, Load Generation) need persistent navigation; sidebar scales better than a top bar as items grow, and can be retracted to save horizontal space. |
| PK on stock_labels | `progressivo` VARCHAR | The barcode *is* the identity. A surrogate UUID creates two identities for one physical object. |
| Weight unit | `volume_tons` (not kg) | Source data is in metric tons; confirmed by cross-checking piece count × unit weight. |
| `actual_length_m` nullable | Yes | ~30% of labels are plates/fittings with no meaningful length. |
| Bin-packing algorithm | FFD (First Fit Decreasing) | Well-understood heuristic, ≤ 11/9 of optimal, fast enough for real-time use. Exact solvers don't scale. |
| `order_condition` | Enum, not free text | Five fixed values drive load prioritisation; free text makes ordering unreliable. |
| `embarque_id` | VARCHAR ref, not boolean | Source column holds a 7-digit external shipment ID, not a flag. Discarding it breaks reconciliation. |
| Product description | Single field, not parsed | Non-pipe items have free-form descriptions; parsing rules from one export are fragile. |

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
ALLOWED_ORIGINS=http://localhost:8080

# Pagination
DEFAULT_PAGE_SIZE=25
MAX_PAGE_SIZE=100

# Idle threshold (days without scanning before a label is flagged as idle)
IDLE_SCAN_THRESHOLD_DAYS=30
```

### Front-end (`frontend/.env`)
```dotenv
API_BASE_URL=http://localhost:8000/api/v1
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
│   │   │       │   ├── stock_labels.py   # physical labels / inventory
│   │   │       │   ├── loads.py          # load plans
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
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── sidebar/          # Collapsible sidebar + nav
│   │   │   │   ├── summary-card/     # TotalCard + BreakdownCard
│   │   │   │   ├── capacity-bar/     # Capacity fill bar
│   │   │   │   └── status-badge/     # label_status / load_status badge
│   │   │   ├── pages/
│   │   │   │   ├── stock/            # Stock page (controller + template)
│   │   │   │   ├── loads/            # Loads page (controller + template)
│   │   │   │   └── load-generation/  # Load Generation page (controller + template)
│   │   │   ├── services/
│   │   │   │   ├── stock.service.js
│   │   │   │   ├── loads.service.js
│   │   │   │   └── bin-packing.service.js
│   │   │   └── app.module.js         # AngularJS module + route config
│   │   ├── styles/
│   │   │   └── main.css              # CSS variables + global dark theme
│   │   └── index.html
│   ├── webpack.config.js
│   ├── package.json
│   └── Dockerfile
├── Shipping Manager.html             # Visual design reference (do not modify)
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

### `loads` — truck load plans

Trucks are not tracked as entities. The user selects a fixed capacity class when creating a load. The truck plate is optional free text for reference only.

```sql
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
truck_capacity_tons NUMERIC(10,3) NOT NULL   -- user-selected: 27 | 31 | 38 (metric tons)
truck_plate         VARCHAR(32)              -- optional, free text
status              load_status NOT NULL     -- see enum below
destination         VARCHAR(255)
customer            VARCHAR(255)
total_weight_tons   NUMERIC(10,3)            -- sum of assigned load_items.volume_tons
created_at          TIMESTAMPTZ DEFAULT now()
dispatched_at       TIMESTAMPTZ
delivered_at        TIMESTAMPTZ
updated_at          TIMESTAMPTZ DEFAULT now()
```

**`load_status` enum:** `draft` | `confirmed` | `dispatched` | `delivered` | `cancelled`

### `load_items` — labels assigned to a load
```sql
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
load_id             UUID REFERENCES loads(id)
stock_label_id      VARCHAR(64) REFERENCES stock_labels(progressivo)
```

---

## Services, Jobs, and Models

### Back-end Services
| Service | Responsibility |
|---------|---------------|
| `StockService` | CRUD labels, validate `label_status` transitions, filter by warehouse/product/status |
| `LoadService` | Create/confirm/dispatch loads, aggregate `volume_tons` against `truck_capacity_tons`, manage `load_status` state machine |
| `BinPackingService` | Given a set of available labels + a capacity class (27/31/38 t), return an optimal load plan. Primary packing metric: `volume_tons`. Primary dimensional constraint: `actual_length_m`. Available filters: `warehouse_code`, `customer`, `truck_capacity_tons`. Algorithm: FFD on `volume_tons`, verify `actual_length_m` when present, check total ≤ `truck_capacity_tons`. Returns best partial plan flagged as `partial: true` when cap is hit. |

### Celery Jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| `stock_snapshot` | Daily 02:00 | Snapshot label counts and total volume_tons per warehouse_code + status to a history table |
| `idle_label_watchdog` | Every 15 min | Set `status = 'idle'` on labels where `days_without_scan ≥ IDLE_SCAN_THRESHOLD_DAYS` |
| `report_generator` | Monday 06:00 | Generate weekly stock + shipment summary (CSV + PDF) |

### Front-end Pages & Services

Three pages. Navigation via collapsible left sidebar. All data fetching through AngularJS services (no raw `$http` in controllers).

| Page | AngularJS Controller | Purpose |
|------|---------------------|---------|
| `Stock` | `StockController` | Read-only label list with summary breakdowns and filters |
| `Loads` | `LoadsController` | Load list with summary breakdowns, inline item detail, and row search |
| `Load Generation` | `LoadGenController` | Filter panel + generate + confirm load plans |

| Service | File | Purpose |
|---------|------|---------|
| `StockService` | `services/stock.service.js` | `GET /api/v1/stock-labels`, client-side filter/search helpers |
| `LoadsService` | `services/loads.service.js` | `GET /api/v1/loads`, `GET /api/v1/loads/:id/items`, status transition calls |
| `BinPackingService` | `services/bin-packing.service.js` | `POST /api/v1/bin-packing` |

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

### CORS in development
**Problem:** Webpack dev server (`:8080`) hits FastAPI (`:8000`).
**Fix:** Set `ALLOWED_ORIGINS=http://localhost:8080` in `.env` and configure `CORSMiddleware` in `main.py`. Do not use `allow_origins=["*"]`.

### AngularJS $digest loop and large datasets
**Problem:** Two-way binding on a full stock label list causes slow `$digest` cycles when the dataset is large.
**Fix:** Use `track by` in `ng-repeat` (`track by item.progressivo`), and apply client-side filters via a service method rather than chained AngularJS filters. Run `$scope.$applyAsync()` instead of `$scope.$apply()` when resolving `$http` promises manually.

---

## Design Patterns

- **Repository pattern** — all DB queries live in `repositories/`; services depend on repository interfaces, not SQLAlchemy directly.
- **Service layer** — business logic and state machine transitions live in `services/`, never in route handlers.
- **Schema separation** — distinct Pydantic schemas for Create, Update, Read, and DB model.
- **State machine for status** — valid transitions declared as a dict; service raises `InvalidTransitionError` for illegal moves.
- **Feature flags via env** — use `Settings` fields to toggle experimental features (e.g. `ENABLE_3D_VISUALISER=false`).
- **TDD** — write the failing test first; implement the minimum code to pass; refactor. Red → Green → Refactor on every change.
- **XP practices** — short iterations, continuous integration on every commit, pair/review all non-trivial logic, refactor relentlessly.
- **AngularJS service singleton** — all API calls and client-side aggregation live in services; controllers only bind scope properties and call service methods.

---

## Front-end Design

Three pages. Navigation is a **collapsible left sidebar** with a toggle button to retract it. When retracted, the sidebar shows only icons; when expanded, it shows icons + labels.

**Design reference:** reproduce the exact dark theme, typography, color palette, and component shapes from `Shipping Manager.html`. Key CSS variables:

```css
--bg: #0d0f12;
--surface: #141720;
--surface2: #1c2130;
--surface3: #222840;
--border: #252c3a;
--border2: #2e384d;
--text: #f0f2fa;
--text-muted: #9ba8c8;
--text-dim: #5a6890;
--accent: #f5a623;
--green: #2ecc8a;
--yellow: #f5c842;
--red: #e8435a;
--blue: #4a9eff;
--font: 'Space Grotesk', sans-serif;
--mono: 'Space Mono', monospace;
```

### Navigation (Sidebar)

```
┌────────────┐
│ ShipManager│  ← logo + version
│ [≡ toggle] │
├────────────┤
│ ■ Stock    │  ← active: left accent border + background highlight
│ ■ Loads    │
│ ■ Load Gen │
├────────────┤
│ Last sync  │  ← footer
└────────────┘
```

Active item has a left orange border (`--accent`) and `--surface2` background. Retract button collapses sidebar to icon-only width (48 px). Expand button restores full width (210 px).

---

### Page: Stock

Read-only view of all physical labels in the warehouse.

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Total Tonnage]  [Tonnage by Country ▬▬]  [Tonnage by Client ▬▬]  │
│                   [Tonnage by Status ▬▬]                            │
├─────────────────────────────────────────────────────────────────────┤
│  [Search…]  [Warehouse ▾]  [Std Bundle ▾]  [Order Condition ▾]      │
│  [Exit Date from]  [Exit Date to]                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Table (paginated, 25 rows default)                                 │
│  Label | Item Code | Description | Client | Warehouse | Country |  │
│  Order | Std Bundle | Boarding | Tonnage | Pieces | Condition |     │
│  Exit Date | NF | Invoice                                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Summary cards (top row):**

| Card | Type | Value |
|------|------|-------|
| Total Tonnage | `TotalCard` | SUM of `volume_tons` across all labels + total piece count |
| Tonnage by Country | `BreakdownCard` | Mini bar chart: country → SUM `volume_tons` |
| Tonnage by Client | `BreakdownCard` | Mini bar chart: customer → SUM `volume_tons` |
| Tonnage by Status | `BreakdownCard` | Mini bar chart: `label_status` → SUM `volume_tons` |

**Data fetching:** single `GET /api/v1/stock-labels` call. All filtering, search, and KPI aggregation happen client-side.

**Search (client-side, substring, case-insensitive):** matches any of:
`progressivo`, `item_code`, `description`, `customer`, `country`, `order_number`, `embarque_id`, `nf`, `invoice`

**Fixed filters (client-side):**

| Filter | Type | Options |
|--------|------|---------|
| Warehouse | Select | All · (distinct `warehouse_code` values from loaded data) |
| Standard Bundle | Select | All · Yes · No |
| Order Condition | Select | All · fixo_futuro · pedido_ate_hoje · antecipa_futuro · fixo_mes_atual · antecipa_mes_atual |
| Exit Date (from) | Date input | filters `exit_date ≥ from` |
| Exit Date (to) | Date input | filters `exit_date ≤ to` |

**Table columns:**

| Column | Field | Notes |
|--------|-------|-------|
| Label | `progressivo` | mono font, accent color |
| Item Code | `item_code` | mono font |
| Description | `description` | |
| Client | `customer` | muted |
| Warehouse | `warehouse_code` | mono, muted |
| Country | `country` | muted |
| Order | `order_number` | mono, muted |
| Std Bundle | `is_standard_bundle` | YES (green) / NO (dim) |
| Boarding | `embarque_id` | muted |
| Tonnage | `volume_tons` | mono, right-aligned |
| Pieces | `piece_count` | mono, right-aligned |
| Condition | `order_condition` | mono |
| Exit Date | `exit_date` | mono, muted |
| NF | `nf` | mono, muted |
| Invoice | `invoice` | mono, muted |

**No mutations on this page.**

---

### Page: Loads

View and manage load plans.

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Total Tonnage]  [by Country ▬▬]  [by Client ▬▬]  [by Status ▬▬] │
│                   [by Destination ▬▬]                               │
├─────────────────────────────────────────────────────────────────────┤
│  [Search by load id, destination, status…]                          │
├─────────────────────────────────────────────────────────────────────┤
│  Table                                                              │
│  Load ID | Date | Destination | Total Tonnage | Capacity |          │
│  Used Capacity | Status                                             │
│  ▶ click row → expands inline showing load items                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Summary cards (top row):**

| Card | Type | Value |
|------|------|-------|
| Total Tonnage | `TotalCard` | SUM of `total_weight_tons` across all loads + total load count |
| Tonnage by Country | `BreakdownCard` | Mini bar chart: country (from load items) → SUM `volume_tons` |
| Tonnage by Client | `BreakdownCard` | Mini bar chart: customer (from load items) → SUM `volume_tons` |
| Tonnage by Status | `BreakdownCard` | Mini bar chart: `load_status` → SUM `total_weight_tons` |
| Tonnage by Destination | `BreakdownCard` | Mini bar chart: `destination` → SUM `total_weight_tons` |

**Data fetching:** single `GET /api/v1/loads` call. All aggregation and search happen client-side.

**Search (client-side, substring, case-insensitive):** matches `id`, `destination`, `status`

**Table columns:**

| Column | Field | Notes |
|--------|-------|-------|
| Load ID | `id` | mono, accent color |
| Date | `created_at` | date only, mono, muted |
| Destination | `destination` | |
| Total Tonnage | `total_weight_tons` | mono, right-aligned |
| Capacity | `truck_capacity_tons` | mono, right-aligned |
| Used Capacity | computed | `CapacityBar` — mini bar showing fill % |
| Status | `status` | `LoadStatusBadge` |

**Row click → inline expand (below the row):**

The expanded section slides open beneath the clicked row (CSS `expandDown` animation matching the design reference). It shows a nested table of load items:

| Sub-column | Field | Notes |
|------------|-------|-------|
| Code | `item_code` | mono, accent |
| Description | `description` | |
| Client | `customer` | muted |
| Pieces | `piece_count` | mono, right-aligned |
| Tonnage | `volume_tons` | mono, right-aligned |

A totals row (TOTAL) shows sum of pieces and tonnage for the load.

Load items are fetched via `GET /api/v1/loads/:id/items` on first expand, then cached in the controller.

---

### Page: Load Generation

Separate page (not a modal/wizard) for generating and confirming truck loads via bin-packing.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ── Filters ─────────────────────────────────────────────────────── │
│  [Warehouse ▾]  [Client ▾]  [27 t] [31 t] [38 t]  [⟳ GENERATE]    │
├─────────────────────────────────────────────────────────────────────┤
│  Results table (appears after generation)                           │
│  Load | Items | Total Pieces | Total Tonnage | Used Capacity |      │
│  Destination | Action                                               │
└─────────────────────────────────────────────────────────────────────┘
```

**Filters:**

| Filter | Type | Notes |
|--------|------|-------|
| Warehouse | Select | All · (distinct `warehouse_code` values) |
| Client | Select | All · (distinct `customer` values) |
| Max Tonnage | Button group | `[27 t]` `[31 t]` `[38 t]` — single select, required |

**Generate button:** calls `POST /api/v1/bin-packing` with filters and selected capacity. Displays results in the table below.

**Results table columns:**

| Column | Notes |
|--------|-------|
| Load | Generated load ID + truck capacity label |
| Items | List of item codes + truncated descriptions |
| Total Pieces | Sum of `piece_count` |
| Total Tonnage | Sum of `volume_tons`, bold |
| Used Capacity | `CapacityBar` |
| Destination | Text input (required before confirming) |
| Action | `CONFIRM` button — disabled until destination is filled; turns to `CONFIRMED` badge after confirm |

**Confirm action:** calls `POST /api/v1/loads` to create the load with `status = draft`. Labels transition to `in_shipment`. Confirmed rows become read-only with a green CONFIRMED badge.

---

### Shared Components

| Component | File | Purpose |
|-----------|------|---------|
| `TotalCard` | `components/summary-card/total-card.html` | Large number card (label + value + sub-label) |
| `BreakdownCard` | `components/summary-card/breakdown-card.html` | Mini horizontal bar chart by dimension |
| `StatusBadge` | `components/status-badge/status-badge.html` | Dot + label badge for `label_status` |
| `LoadStatusBadge` | `components/status-badge/load-status-badge.html` | Dot + label badge for `load_status` |
| `CapacityBar` | `components/capacity-bar/capacity-bar.html` | Fill bar with percentage label |
| `Sidebar` | `components/sidebar/sidebar.html` | Collapsible nav sidebar |

### Status Color Map

**`label_status`:**

| Status | Color |
|--------|-------|
| available | `--green` |
| reserved | `--yellow` |
| in_shipment | `--blue` |
| idle | `--accent` (orange) |
| delivered | `--text-muted` (gray) |
| damaged | `--red` |

**`load_status`:**

| Status | Color |
|--------|-------|
| draft | `--text-muted` (gray) |
| confirmed | `--green` |
| dispatched | `--accent` (orange) |
| delivered | `--blue` |
| cancelled | `--red` |

---

## CI Pipeline (runs on every commit)

```
Black + Flake8 + isort   →   pip-audit   →   Bandit   →   pytest + Jasmine/Karma
    (style)                (vulnerabilities) (static sec)        (tests)
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
- [ ] `label_status` and `load_status` transitions are validated in the service layer
- [ ] `actual_length_m` NULL case is handled in any code that touches pipe dimensions
- [ ] Excel serial date fields are always converted via `excel_serial_to_dt()` before persisting
- [ ] New env variables are documented here and added to `.env.example`
- [ ] `pip-audit` and `Bandit` return no new findings
- [ ] Front-end API calls go through AngularJS services — no raw `$http` in controllers
- [ ] `ng-repeat` uses `track by` on the label's natural key
- [ ] Dashboard summary cards updated to reflect any new stock or load states
- [ ] CLAUDE.md updated if architecture, schemas, or environment variables changed
- [ ] Visual output checked against `Shipping Manager.html` for design fidelity

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

# Front-end dev server (Webpack)
cd frontend && npm start
```

Commit convention: one commit per feature / refactor / bug-fix / test. Use imperative mood: `add`, `fix`, `refactor`, `test`, `chore`.
