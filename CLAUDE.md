# CLAUDE.md

Guidance for Claude Code when working in this repository.

---

## Architecture Overview

`shipping-manager` is a web application for a steel pipe industry to control stock and automate truck load planning via a Bin-Packing algorithm.

```
┌─────────────────┐     REST/JSON     ┌──────────────────┐
│  AngularJS      │ ◄───────────────► │  FastAPI         │
│  (Dashboard)    │                   │  (Python REST)   │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                    ┌──────────┴──────────┐
                                    │                     │
                              ┌─────▼──────┐     ┌───────▼──────┐
                              │ stock.xlsx │     │  In-memory   │
                              │  (source)  │     │  load store  │
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
| Framework | FastAPI 0.115 |
| ASGI server | Uvicorn |
| Validation | Pydantic v2 |
| Data source | openpyxl — reads `stock.xlsx` at startup, cached in memory |
| Load state | In-process dict store (stateless across restarts; DB migration pending) |
| CORS | FastAPI `CORSMiddleware` |
| Testing | pytest + FastAPI `TestClient` |
| Style | ruff (optional) |

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
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Architectural Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Back-end language | Python / FastAPI | Standard Python REST stack; type-safe via Pydantic; auto-generated OpenAPI docs; easy onboarding. |
| Data source | `stock.xlsx` (openpyxl) | Source-of-truth data arrives as Excel exports; no DB migration needed for read path. |
| Load state | In-memory dict | Simplest possible persistence for the current scope; swapping in SQLite/Postgres is a one-file change to `load_service.py`. |
| REST prefix | `/web/api/v1/` | Maintains same URL space as the original PASOE design; no frontend changes required. |
| Bin-packing algorithm | FFD (First Fit Decreasing) | Well-understood heuristic, ≤ 11/9 of optimal, fast enough for real-time use. Exact solvers don't scale. |
| `actual_length_m` nullable | Yes | ~30% of labels are plates/fittings with no meaningful length. |
| Weight unit | `volume_tons` (not kg) | Source data is in metric tons; the Excel `Volume Geral` column is in kg and is divided by 1000 on load. |
| Bin plan response keys | camelCase (`totalTons`, `totalPcs`, `_id`) | AngularJS templates use these names directly; changing them would break the frontend. |
| `order_condition` | Enum, not free text | Five fixed values drive load prioritisation; free text makes ordering unreliable. |
| `embarque_id` | VARCHAR ref, not boolean | Source column holds a 7-digit external shipment ID, not a flag. Discarding it breaks reconciliation. |
| Front-end framework | AngularJS 1.8.x | Fits the team's existing AngularJS familiarity; two-way binding simplifies dashboard filter state. |
| Front-end CSS | Custom CSS variables | The dark dashboard design uses a fixed palette; a utility framework adds indirection without benefit. |
| Navigation | Collapsible left sidebar | Three pages need persistent navigation; sidebar scales better than a top bar and can be retracted. |

---

## Environment Variables

### Back-end (set in Docker or `.env`)
```dotenv
# Path to the Excel inventory file (mounted volume in Docker)
XLSX_PATH=/data/stock.xlsx

# Comma-separated allowed CORS origins
CORS_ORIGINS=http://localhost,http://localhost:4200

# Uvicorn port
PORT=8080
```

### Front-end (`frontend/.env`)
```dotenv
API_BASE_URL=http://localhost:8080/web/api/v1
```

---

## Directory Structure

```
shipping-manager/
├── backend/
│   ├── src/
│   │   ├── main.py                    # FastAPI app + CORS + router wiring
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── stock_labels.py    # GET /web/api/v1/stock-labels
│   │   │       ├── loads.py           # GET/POST /loads, GET /:id/items, PATCH /:id/status
│   │   │       └── bin_packing.py     # POST /web/api/v1/bin-packing
│   │   ├── services/
│   │   │   ├── ffd.py                 # First Fit Decreasing algorithm
│   │   │   └── load_service.py        # Load CRUD + status state machine
│   │   └── data/
│   │       └── xlsx_loader.py         # openpyxl reader + row mapper + cache
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_ffd.py            # FFD algorithm unit tests
│   │   │   └── test_load_service.py   # Load service unit tests
│   │   └── integration/
│   │       └── test_routes.py         # Full HTTP route tests (TestClient + stock.xlsx)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
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
│   │   │   └── app.module.js
│   │   ├── styles/
│   │   │   └── main.css
│   │   └── index.html
│   ├── webpack.config.js
│   ├── package.json
│   └── Dockerfile
├── Shipping Manager.html             # Visual design reference (do not modify)
├── stock.xlsx                        # Inventory source file (mounted into backend container)
├── docker-compose.yml
└── CLAUDE.md
```

---

## API Contract

All endpoints are prefixed `/web/api/v1/`.

### `GET /stock-labels`
Returns all labels loaded from `stock.xlsx`. Read-only; no query parameters — all filtering is client-side.

**Response:** `Array<StockLabel>`

### `POST /bin-packing`
Runs FFD on available/reserved labels and returns bin plans.

**Request body:**
```json
{
  "truck_capacity_tons": 27,
  "max_iterations": 1000,
  "filters": { "warehouse_code": "A12", "customer": "ACME" }
}
```

**Response:** `Array<BinPlan>` where each plan has:
```json
{ "_id": "GEN-...", "items": [...], "totalTons": 18.3, "totalPcs": 42, "partial": false, "destination": "" }
```
Note: `totalTons` / `totalPcs` use camelCase — the AngularJS templates bind to these names directly.

### `POST /loads`
Confirms a generated plan as a load.

**Request body:** `{ "truck_capacity_tons": 27, "destination": "Porto de Santos", "items": ["PROG001", "PROG002"] }`

**Response:** `Load` object (no `items` field) + `item_count`. Status is `pending`.

### `GET /loads`
Returns all loads (no `items` field). All aggregation is client-side.

### `GET /loads/:id/items`
Returns resolved `StockLabel` objects for a load.

### `PATCH /loads/:id/status`
Advances the load through the state machine. No body required.

**State machine:** `pending → in_transit → dispatched → delivered`. Returns 422 when no further transition exists.

---

## Data Model

### Stock Label fields (from `stock.xlsx`)

| Python key | Excel column | Notes |
|------------|-------------|-------|
| `progressivo` | `progressivo` | Primary key — barcode |
| `item_code` | `Item` | |
| `description` | `Descricao` | |
| `customer` | `Cliente Ped` | |
| `country` | `País` | |
| `order_number` | `Pedido` | null if no order |
| `is_standard_bundle` | `Fardo Padrão` | `"Sim"` → `True` |
| `embarque_id` | `Embarque Etiq` | null when value is `"0"` or empty |
| `volume_tons` | `Volume Geral` | **divided by 1000** — source is kg |
| `piece_count` | `Qt PC` | |
| `order_condition` | `Pedido Condição` | mapped via `_CONDITION_MAP` |
| `exit_date` | `Data Saida Pedido` | ISO date string or null |
| `warehouse_code` | `Wharehouse` | |
| `status` | derived | see derivation below |

**Status derivation:**
- `embarque_id` present → `in_transit_to_terminal`
- `order_number` present → `reserved`
- otherwise → `available_in_stock`

### `label_status` enum
`available_in_stock` | `reserved` | `in_load` | `in_transit_to_terminal` | `available_in_terminal` | `in_transit_to_client` | `delivered` | `idle` | `damaged`

### `load_status` state machine
`pending → in_transit → dispatched → delivered` (any → `cancelled` not yet implemented in API)

---

## Services

### `src/services/ffd.py` — FFD algorithm
```python
ffd(labels: list[dict], truck_capacity_tons: float, max_iterations: int = 1000) -> list[dict]
```
- Filters eligible items (`volume_tons > 0` and `≤ truck_capacity_tons`)
- Sorts descending by `volume_tons`
- Packs into bins; each bin dict: `_id`, `items`, `totalTons`, `totalPcs`, `partial`, `destination`
- Stops after `max_iterations` items processed

### `src/services/load_service.py` — Load CRUD + state machine
Module-level `_store: dict[str, dict]` — in-memory, cleared on restart. Key functions:
- `create_load(...)` → creates load, returns it without `items`
- `advance_status(load_id)` → advances state machine; raises `ValueError` on illegal transition; returns `None` if not found
- `clear_store()` — used in tests (`autouse` fixture)

### `src/data/xlsx_loader.py` — Excel reader
Module-level `_cache` — populated on first call to `load_labels()`, held for the process lifetime. Call `invalidate_cache()` to force reload. `openpyxl` with `read_only=True, data_only=True`.

---

## Common Hurdles

### `volume_tons` is in kg in the Excel file
**Problem:** `Volume Geral` stores kg, not metric tons.
**Fix:** divide by 1000 in `_map_row`. The integration test `test_volume_tons_is_metric_tons` guards against regression.

### `actual_length_m` is `None` for ~30% of labels
**Problem:** Plates, fittings, and other non-pipe items don't have a length.
**Fix:** In `ffd`, treat `actual_length_m = None` as "no length constraint."

### Bin plan response uses camelCase keys
**Problem:** Python convention is snake_case, but the AngularJS templates bind directly to `plan.totalTons`, `plan.totalPcs`, `plan._id`.
**Fix:** `ffd()` returns dicts with those exact camelCase keys. Do not rename them.

### Load state is lost on restart
**Problem:** `_store` is in-process memory.
**Fix (future):** replace `load_service.py`'s store with SQLite via `sqlite3` or SQLAlchemy. The service interface (`create_load`, `advance_status`, etc.) stays the same.

### CORS in development
**Problem:** Webpack dev server origin is different from the backend.
**Fix:** Set `CORS_ORIGINS=http://localhost:4200,http://localhost` in the environment. Never hardcode `*`.

### AngularJS $digest loop and large datasets
**Problem:** Two-way binding on a full stock label list causes slow `$digest` cycles.
**Fix:** Use `track by` in `ng-repeat` (`track by item.progressivo`), apply client-side filters via service methods.

---

## Design Patterns

- **Thin route layer** — `src/api/v1/` handlers parse the request, call one service function, return the result. No business logic in routes.
- **Service functions** — business logic and state machine transitions live in `src/services/`. Routes and data layer never call each other directly.
- **Data layer** — `src/data/xlsx_loader.py` is the only place that touches openpyxl. Services never import openpyxl.
- **State machine for loads** — `_TRANSITIONS` dict in `load_service.py` defines all valid moves; `ValueError` for illegal transitions.
- **TDD** — write the failing pytest test first; implement the minimum code to pass; refactor. Red → Green → Refactor on every change.
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
│  [Search…]  [Status ▾]  [Warehouse ▾]  [Std Bundle ▾]  [Condition ▾] │
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
| Status | Select | All · Available In Stock · In Load · In Transit to Terminal · Available In Terminal · In Transit to Client · Delivered |
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

**Data fetching:** single `GET /api/v1/loads` call. All aggregation, search, filtering, and sorting happen client-side.

**Status action button (per row):** renders the next allowed transition as a button. Calls `PATCH /api/v1/loads/:id/status` on click. Valid transitions: `pending → in_transit`, `in_transit → dispatched`, `dispatched → delivered`.

**Row click → inline expand:** fetches items via `GET /api/v1/loads/:id/items` on first expand, then cached.

---

### Page: Load Generation

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Warehouse ▾]  [Client ▾]  [27 t] [31 t] [38 t]  [⟳ GENERATE]    │
├─────────────────────────────────────────────────────────────────────┤
│  Results table: Load | Items | Total Pieces | Total Tonnage |       │
│  Used Capacity | Destination | Action (CONFIRM)                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Generate button:** calls `POST /api/v1/bin-packing`. The response is an array of bin plans; the controller maps each bin into the `vm.generated` array.

**Confirm action:** calls `POST /api/v1/loads` with `status = pending`.

---

### Shared Components

| Component | File | Purpose |
|-----------|------|---------|
| `TotalCard` | `components/summary-card/total-card.html` | Large number card |
| `BreakdownCard` | `components/summary-card/breakdown-card.html` | Mini horizontal bar chart |
| `StatusBadge` | `components/status-badge/status-badge.html` | Dot + label badge for `label_status` |
| `LoadStatusBadge` | `components/status-badge/load-status-badge.html` | Dot + label badge for `load_status` |
| `CapacityBar` | `components/capacity-bar/capacity-bar.html` | Fill bar with percentage label |
| `Sidebar` | `components/sidebar/sidebar.html` | Collapsible nav sidebar |

### Status Color Map

**`label_status`:**

| Status | Color |
|--------|-------|
| available_in_stock | `--green` |
| reserved | `--yellow` |
| in_load | `--blue` |
| in_transit_to_terminal | `--accent` (orange) |
| available_in_terminal | `--yellow` |
| in_transit_to_client | `--blue` |
| delivered | `--text-muted` (gray) |
| idle | `--accent` (orange) |
| damaged | `--red` |

**`load_status`:**

| Status | Color |
|--------|-------|
| draft | `--text-dim` (dim gray) |
| pending | `--text-muted` (gray) |
| in_transit | `--accent` (orange) |
| dispatched | `--blue` |
| delivered | `--green` |
| cancelled | `--red` |

---

## CI Pipeline (runs on every commit)

```
pytest (backend)    →    Jasmine/Karma (frontend)
```

All steps must pass before merge.

---

## Post-Implementation Checklist

- [ ] All new endpoints have integration tests (happy path + at least one error case)
- [ ] All new service functions have unit tests written before implementation (TDD)
- [ ] `status` transitions for loads are validated in `load_service.py`, not in routes
- [ ] `actual_length_m = None` case is handled in any code that touches pipe dimensions
- [ ] `volume_tons` is always in metric tons (never raw kg from Excel)
- [ ] New config env vars are documented here and in `docker-compose.yml`
- [ ] Bin plan response keys remain camelCase (`totalTons`, `totalPcs`, `_id`) — AngularJS templates depend on them
- [ ] Front-end API calls go through AngularJS services — no raw `$http` in controllers
- [ ] `ng-repeat` uses `track by` on the label's natural key
- [ ] CLAUDE.md updated if architecture, schemas, or environment variables changed
- [ ] Visual output checked against `Shipping Manager.html` for design fidelity

---

## Development Workflow

```bash
# Start full stack (Python backend + AngularJS frontend)
docker compose up -d

# Run back-end tests (requires stock.xlsx at repo root)
cd backend
XLSX_PATH=../stock.xlsx .venv/bin/pytest -v

# Install/update Python dependencies
cd backend && .venv/bin/pip install -r requirements-dev.txt

# Run back-end locally (hot-reload)
cd backend && XLSX_PATH=../stock.xlsx .venv/bin/uvicorn src.main:app --reload --port 8080

# Run front-end tests
cd frontend && npm test

# Front-end dev server (Webpack)
cd frontend && npm start
```

Commit convention: one commit per feature / refactor / bug-fix / test. Use imperative mood: `add`, `fix`, `refactor`, `test`, `chore`.
