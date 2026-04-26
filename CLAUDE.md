# CLAUDE.md

Guidance for Claude Code when working in this repository.

---

## Architecture Overview

`shipping-manager` is a web application for a steel pipe industry to control stock and automate truck load planning via a Bin-Packing algorithm.

```
┌─────────────────┐     REST/JSON     ┌──────────────────┐
│  AngularJS      │ ◄───────────────► │ Progress PASOE   │
│  (Dashboard)    │                   │  (REST API)      │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                    ┌──────────┴──────────┐
                                    │                     │
                              ┌─────▼──────┐     ┌───────▼──────┐
                              │ OpenEdge   │     │  Background  │
                              │    DB      │     │   Agents     │
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
| Language | Progress ABL (OpenEdge 12.x) |
| App server | PASOE (Progress Application Server for OpenEdge) |
| Database | OpenEdge RDBMS (schema defined via `.df` files) |
| Schema migration | `.df` delta files applied with `proutil -C updatedb` |
| REST layer | PASOE Web Handlers (`OpenEdge.Web.WebHandler` subclasses) |
| JSON | `OpenEdge.Core.Json.*` / `Progress.Json.ObjectModel.*` |
| Auth | JWT validated via custom `IWebAuthFilter` implementation |
| Background jobs | PASOE scheduled background agents (`.p` procedures) |
| Testing | ABLUnit |
| Style | ABLint |

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
| Database | OpenEdge RDBMS 12.x |
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Architectural Decisions

Full rationale is in [README.md](./README.md). Summary of non-obvious choices:

| Decision | Choice | Why |
|----------|--------|-----|
| Back-end platform | Progress OpenEdge / PASOE | Company already runs OpenEdge; PASOE exposes ABL business logic as REST with minimal plumbing. |
| Database | OpenEdge RDBMS | Native to the Progress stack; schema versioned via `.df` files; no JDBC/ODBC bridge needed. |
| REST layer | PASOE Web Handlers | First-class ABL class hierarchy; request/response objects + JSON serialization built in. |
| Schema migration | `.df` delta files | Progress-standard approach; `proutil -C updatedb` applies deltas atomically. |
| Background jobs | PASOE scheduled agents | Runs inside the same server process; can call any ABL business class directly. |
| Auth | JWT via `IWebAuthFilter` | Stateless tokens; filter intercepts every request before it reaches the handler. |
| Testing | ABLUnit | Native ABL unit test runner; integrates with PDSOE and CI via Ant. |
| Style linting | ABLint | Static analysis for ABL; catches common issues (missing `NO-ERROR`, undeclared variables). |
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

### Back-end (`backend/conf/openedge.properties`)
```properties
# App
psc.as.appdir=shipping_manager
psc.as.oe.url=http://localhost:8080

# Database
psc.as.db.1=-db /data/shipping_manager -H localhost -S 8090
psc.as.db.connect.wait=30

# CORS — comma-separated allowed origins
shipping.cors.allowed-origins=http://localhost:8080

# JWT
shipping.jwt.secret=changeme
shipping.jwt.expire-minutes=60

# Pagination
shipping.page.default-size=25
shipping.page.max-size=100

# Idle threshold (days without a scan before a label is flagged as idle)
shipping.idle.threshold-days=30
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
│   │   ├── api/v1/                       # PASOE Web Handlers (REST endpoints)
│   │   │   ├── StockLabelsHandler.cls    # GET /stock-labels, PATCH status/location
│   │   │   ├── LoadsHandler.cls          # GET /loads, GET /loads/:id/items, POST, PATCH /:id/status
│   │   │   └── BinPackingHandler.cls     # POST /bin-packing
│   │   ├── business/                     # Business logic / services
│   │   │   ├── StockService.cls
│   │   │   ├── LoadService.cls
│   │   │   └── BinPackingService.cls
│   │   ├── data/                         # Data access (table queries)
│   │   │   ├── StockLabelRepository.cls
│   │   │   ├── LoadRepository.cls
│   │   │   └── LoadItemRepository.cls
│   │   ├── model/                        # ABL data-transfer classes (request/response)
│   │   │   ├── StockLabelModel.cls
│   │   │   ├── LoadModel.cls
│   │   │   └── BinPackingModel.cls
│   │   ├── auth/
│   │   │   └── JwtAuthFilter.cls         # IWebAuthFilter implementation
│   │   └── jobs/                         # Scheduled background agents
│   │       ├── StockSnapshotAgent.p      # Daily 02:00
│   │       ├── IdleWatchdogAgent.p       # Every 15 min
│   │       └── ReportGeneratorAgent.p    # Monday 06:00
│   ├── schema/
│   │   ├── shipping_manager.df           # Full OpenEdge DB schema
│   │   └── migrations/                  # Delta .df files per version
│   │       └── v2.0.0.df
│   ├── tests/
│   │   ├── unit/                         # ABLUnit test cases
│   │   │   ├── TestStockService.cls
│   │   │   ├── TestLoadService.cls
│   │   │   └── TestBinPackingService.cls
│   │   └── integration/                  # End-to-end handler tests
│   ├── conf/
│   │   └── openedge.properties           # PASOE configuration
│   ├── WEB-INF/
│   │   └── web.xml                       # Servlet + route mapping
│   ├── build.xml                         # Ant build file (compile, test, package)
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

Schema is defined in `backend/schema/shipping_manager.df` (OpenEdge Data Definition file). The logical structure below is for reference; the `.df` file is authoritative.

### `products` — steel pipe / component catalogue
One row per unique product code (`item_code`). The `description` field encodes pipe specs as `{OD}x{wall}x{length}-{standard}-{class} {threading} {treatment}` (e.g. `60,30x3,00x6000-NBR5580-CL Rir BSP Galv`).

```
id                CHARACTER(36)   /* GUID, primary key */
item_code         CHARACTER(32)   /* UNIQUE, source: "Item" */
description       CHARACTER(512)  /* source: "Descricao" */
nominal_length_m  DECIMAL(8,2)    /* 6.0 or 12.0 for pipes */
standard          CHARACTER(64)   /* NBR5580, API5L, ASTM A572, … */
active            LOGICAL INITIAL TRUE
created_at        DATETIME-TZ
updated_at        DATETIME-TZ
```

### `stock_labels` — physical inventory labels (one row = one barcode tag)
Each label represents a physical bundle of one product sitting in a warehouse location.

```
progressivo         CHARACTER(64)   /* primary key — source: "progressivo" (barcode) */
product_id          CHARACTER(36)   /* FK → products.id */
customer_item_ref   CHARACTER(128)  /* source: "Cliente Item" */
actual_length_m     DECIMAL(8,3)    /* source: "Comprimento Real" (? for plates/fittings) */
warehouse_code      CHARACTER(32)   /* source: "Deposito" (e.g. '2', 'A12', 'B08') */
address             CHARACTER(32)   /* source: "Endereço" (rack/bin, e.g. 'E10', 'J16') */
location_detail     CHARACTER(128)  /* source: "Localizacao" */
market_type         CHARACTER(2)    /* MI | ME */
is_standard_bundle  LOGICAL         /* source: "Fardo Padrão" */
volume_tons         DECIMAL(10,4)   /* source: "Volume Geral" (metric tons) */
piece_count         INTEGER         /* source: "Qt PC" */
status              CHARACTER(32)   /* see valid values below */
order_id            CHARACTER(36)   /* FK → orders.id; ? when no order */
embarque_id         CHARACTER(32)   /* source: "Embarque Fifo" / "Embarque Etiq" */
nf                  CHARACTER(64)   /* Nota Fiscal number */
invoice             CHARACTER(64)   /* commercial invoice number (export) */
scan_count          INTEGER INITIAL 0  /* source: "Qtd Escaneamentos" */
last_scanned_at     DATETIME-TZ     /* source: "Ultimo Escaneamento" (converted from Excel serial) */
days_without_scan   INTEGER         /* source: "Dias sem Escanear" (denormalised) */
avg_days_idle       INTEGER         /* source: "Média dias Parado" */
created_at          DATETIME-TZ
updated_at          DATETIME-TZ
```

**`label_status` enum:** `available_in_stock` | `reserved` | `in_load` | `in_transit_to_terminal` | `available_in_terminal` | `in_transit_to_client` | `delivered` | `idle` | `damaged`

Derivation from source data:
- `available_in_stock` — `Tem Pedido? = Não`, no embarque; physically in warehouse
- `reserved` — `Tem Pedido? = Sim`, no embarque yet; allocated to an order but not yet in a load
- `in_load` — allocated to a confirmed load plan; set automatically when a load is confirmed (US-05, US-15)
- `in_transit_to_terminal` — load dispatched toward the port/terminal
- `available_in_terminal` — label arrived at terminal, awaiting vessel or onward transport
- `in_transit_to_client` — on board vessel or truck en route to client
- `delivered` — confirmed received by client
- `idle` — flagged by watchdog when `Dias sem Escanear ≥ IDLE_SCAN_THRESHOLD_DAYS`
- `damaged` — manually flagged by operator

### `orders` — customer orders
```
id               CHARACTER(36)   /* GUID primary key */
order_number     CHARACTER(64)   /* UNIQUE — source: "Pedido" */
client_order_ref CHARACTER(64)   /* source: "Ped Cli" */
customer         CHARACTER(255)  /* source: "Cliente" */
country          CHARACTER(64)   /* Brasil | Paraguai | Uruguai | Bolivia | Argentina */
market_type      CHARACTER(2)    /* MI | ME */
condition        CHARACTER(32)   /* see valid values below */
exit_date        DATE            /* source: "Data Saida Pedido" */
created_at       DATETIME-TZ
updated_at       DATETIME-TZ
```

**`condition` valid values:** `fixo_futuro` | `pedido_ate_hoje` | `antecipa_futuro` | `fixo_mes_atual` | `antecipa_mes_atual`

**`market_type` valid values:** `MI` (Mercado Interno / domestic) | `ME` (Mercado Externo / export)

### `loads` — truck load plans

Trucks are not tracked as entities. The user selects a fixed capacity class when creating a load. The truck plate is optional free text for reference only.

```
id                  CHARACTER(36)   /* GUID primary key */
truck_capacity_tons DECIMAL(10,3)   /* user-selected: 27 | 31 | 38 (metric tons) */
truck_plate         CHARACTER(32)   /* optional, free text */
status              CHARACTER(32)   /* see valid values below */
destination         CHARACTER(255)
customer            CHARACTER(255)
total_weight_tons   DECIMAL(10,3)   /* sum of assigned load_items.volume_tons */
created_at          DATETIME-TZ
dispatched_at       DATETIME-TZ
delivered_at        DATETIME-TZ
updated_at          DATETIME-TZ
```

**`status` valid values:** `draft` | `pending` | `in_transit` | `dispatched` | `delivered` | `cancelled`

State machine:
- `draft` → `pending` — planner confirms the load on the Load Generation page (sets destination)
- `pending` → `in_transit` — operator marks departure on the Loads page
- `in_transit` → `dispatched` — operator marks arrival at destination on the Loads page
- `dispatched` → `delivered` — operator marks final delivery confirmation
- any → `cancelled` — operator cancels at any stage before delivery

### `load_items` — labels assigned to a load
```
id             CHARACTER(36)  /* GUID primary key */
load_id        CHARACTER(36)  /* FK → loads.id */
stock_label_id CHARACTER(64)  /* FK → stock_labels.progressivo */
```

---

## Services, Jobs, and Models

### Back-end Services (ABL classes in `src/business/`)
| Class | Responsibility |
|-------|---------------|
| `StockService.cls` | CRUD labels, validate `status` transitions, filter by warehouse/product/status |
| `LoadService.cls` | Create/confirm/dispatch loads, aggregate `volume_tons` against `truck_capacity_tons`, manage load status state machine (`draft → pending → in_transit → dispatched → delivered`); transitions `stock_labels.status` to `in_load` when a load is confirmed |
| `BinPackingService.cls` | Given a set of available labels + a capacity class (27/31/38 t), return an optimal load plan. Primary packing metric: `volume_tons`. Primary dimensional constraint: `actual_length_m`. Available filters: `warehouse_code`, `customer`, `truck_capacity_tons`. Algorithm: FFD on `volume_tons`, verify `actual_length_m` when present, check total ≤ `truck_capacity_tons`. Returns best partial plan flagged as `partial = TRUE` when cap is hit. |

### Background Agents (ABL procedures in `src/jobs/`)
| Procedure | Schedule | Purpose |
|-----------|----------|---------|
| `StockSnapshotAgent.p` | Daily 02:00 | Snapshot label counts and total `volume_tons` per `warehouse_code` + status to a history table |
| `IdleWatchdogAgent.p` | Every 15 min | Set `status = 'idle'` on labels where `days_without_scan ≥ IDLE_THRESHOLD_DAYS` |
| `ReportGeneratorAgent.p` | Monday 06:00 | Generate weekly stock + load summary (CSV + PDF) |

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

### Excel serial date to ABL DATETIME-TZ (`Ultimo Escaneamento`)
**Problem:** Excel stores dates as floats (days since 1900-01-01, with a leap-year bug). The `Ultimo Escaneamento` column arrives as e.g. `46099.656`.
**Fix:**
```abl
FUNCTION ExcelSerialToDatetime RETURNS DATETIME-TZ (INPUT pdSerial AS DECIMAL):
    DEFINE VARIABLE dtBase AS DATE NO-UNDO.
    dtBase = DATE(12, 30, 1899).
    RETURN ADD-INTERVAL(DATETIME-TZ(dtBase, 0), INTEGER(pdSerial) - 1, "days").
END FUNCTION.
```

### Unknown field value / `?` (unknown) in OpenEdge
**Problem:** OpenEdge uses `?` (unknown/null) instead of SQL NULL; comparisons with `=` always evaluate to FALSE against `?`.
**Fix:** Always use `= ?` (not `= ""`) to test for unknown, and initialize decimal fields to `?` (not `0`) when the value is absent. In JSON serialisation, map `?` to JSON `null` explicitly.

### `.df` schema migration on a live database
**Problem:** `proutil -C updatedb` applies the delta `.df` without downtime only for additive changes (new fields, new tables). Renaming or dropping requires emptying affected areas first.
**Fix:** Keep migrations purely additive. Mark obsolete fields with a `/* DEPRECATED */` comment in the `.df` and remove them only in a maintenance window with a confirmed empty record set.

### PASOE CORS in development
**Problem:** Webpack dev server (`:8080`) calls PASOE on the same port; browser blocks cross-origin preflight.
**Fix:** Add a `CORSFilter` servlet filter in `WEB-INF/web.xml` that sets `Access-Control-Allow-Origin` to the value from `openedge.properties`. Never hardcode `*` as the origin.

### `actual_length_m` is `?` for ~30 % of labels
**Problem:** Plates, fittings, and other non-pipe items don't have a length.
**Fix:** In `BinPackingService`, treat `actual_length_m = ?` (unknown) as "no length constraint" — only enforce the truck's length constraint when the field is not `?`.

### Bin-Packing accuracy vs. performance
**Problem:** 3D bin-packing is NP-hard; brute-force is too slow for large orders.
**Fix:** Use FFD on `volume_tons` (dominant metric), then verify `actual_length_m ≤ truck-max-length` per label and cumulative `volume_tons ≤ truck-max-weight-tons`. Expose a `max-iterations` cap and return the best partial solution when the cap is hit, clearly flagging it as `partial = TRUE`.

### AngularJS $digest loop and large datasets
**Problem:** Two-way binding on a full stock label list causes slow `$digest` cycles when the dataset is large.
**Fix:** Use `track by` in `ng-repeat` (`track by item.progressivo`), and apply client-side filters via a service method rather than chained AngularJS filters. Run `$scope.$applyAsync()` instead of `$scope.$apply()` when resolving `$http` promises manually.

---

## Design Patterns

- **Repository pattern** — all OpenEdge table queries live in `src/data/` classes; business services depend on repository interfaces, never query tables directly.
- **Service layer** — business logic and state machine transitions live in `src/business/` classes, never in Web Handler procedures.
- **Web Handler thin layer** — handlers in `src/api/v1/` parse the JSON request, call one service method, and serialise the response. No business logic there.
- **State machine for status** — valid transitions declared as a `DEFINE TEMP-TABLE` constant structure; service raises an `AppError` for illegal moves.
- **Feature flags via properties** — use `openedge.properties` fields to toggle experimental features (e.g. `shipping.enable-3d-visualiser=false`).
- **TDD** — write the failing ABLUnit test first; implement the minimum code to pass; refactor. Red → Green → Refactor on every change.
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

**Summary cards (top row):**

| Card | Type | Value |
|------|------|-------|
| Total Tonnage | `TotalCard` | SUM of `total_weight_tons` across all loads + total load count |
| Tonnage by Country | `BreakdownCard` | Mini bar chart: country (from load items) → SUM `volume_tons` |
| Tonnage by Client | `BreakdownCard` | Mini bar chart: customer (from load items) → SUM `volume_tons` |
| Tonnage by Status | `BreakdownCard` | Mini bar chart: `load_status` → SUM `total_weight_tons` |
| Tonnage by Destination | `BreakdownCard` | Mini bar chart: `destination` → SUM `total_weight_tons` |

**Data fetching:** single `GET /api/v1/loads` call. All aggregation, search, filtering, and sorting happen client-side.

**Search (client-side, substring, case-insensitive):** matches `id`, `destination`, `status`

**Filters (client-side):**

| Filter | Type | Options |
|--------|------|---------|
| Status | Select | All · Pending · In Transit · Dispatched · Delivered · Cancelled |
| Destination | Select | All · (distinct `destination` values from loaded data) |

**Sort:** table is sortable by Date (`created_at`) and Total Tonnage (`total_weight_tons`) — ascending/descending toggle on column header click.

**Table columns:**

| Column | Field | Notes |
|--------|-------|-------|
| Load ID | `id` | mono, accent color |
| Date | `created_at` | date only, mono, muted; sortable |
| Destination | `destination` | |
| Total Tonnage | `total_weight_tons` | mono, right-aligned; sortable |
| Capacity | `truck_capacity_tons` | mono, right-aligned |
| Used Capacity | computed | `CapacityBar` — mini bar showing fill % |
| Status | `status` | `LoadStatusBadge` + inline action button |

**Status action button (per row):** renders the next allowed transition as a button next to the badge. Calls `PATCH /api/v1/loads/:id/status` on click. Valid operator-triggered transitions: `pending → in_transit`, `in_transit → dispatched`, `dispatched → delivered`. Delivered and cancelled loads show no action button. Confirmation is required before dispatching (prevents accidental clicks).

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

**Confirm action:** calls `POST /api/v1/loads` to create the load with `status = pending`. All stock labels in the load transition automatically to `in_load` (server-side, in a single transaction). Confirmed rows become read-only with a green CONFIRMED badge.

**Empty / pre-generation state:** before the first Generate click, the results area shows an empty state: icon + heading "No loads generated yet" + instruction "Select your filters above and click Generate to plan truck loads." No table is rendered.

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
ABLint          →     ABLUnit        →     Jasmine/Karma
(ABL style)        (back-end tests)     (front-end tests)
```

All steps must pass before merge. ABLint suppressions require a comment explaining why.

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

- [ ] All new tables/fields have a delta `.df` file in `schema/migrations/`
- [ ] All new endpoints have integration tests (happy path + at least one error case)
- [ ] All new service methods have ABLUnit tests written before implementation (TDD)
- [ ] `status` transitions for labels and loads are validated in the service layer
- [ ] `actual_length_m = ?` (unknown) case is handled in any code that touches pipe dimensions
- [ ] Excel serial date fields are always converted via `ExcelSerialToDatetime()` before persisting
- [ ] New config properties are documented here and added to `conf/openedge.properties.example`
- [ ] ABLint returns no new findings
- [ ] Front-end API calls go through AngularJS services — no raw `$http` in controllers
- [ ] `ng-repeat` uses `track by` on the label's natural key
- [ ] Dashboard summary cards updated to reflect any new stock or load states
- [ ] CLAUDE.md updated if architecture, schemas, or environment variables changed
- [ ] Visual output checked against `Shipping Manager.html` for design fidelity

---

## Development Workflow

```bash
# Start PASOE + OpenEdge DB (Docker)
docker compose up -d

# Compile ABL sources
cd backend && ant compile

# Run ABLUnit tests
cd backend && ant test

# Apply a schema delta to the running database
cd backend && $DLC/bin/proutil shipping_manager -C updatedb -df schema/migrations/v2.0.0.df

# Start PASOE in development mode (auto-reload)
cd backend && ant start-pasoe

# Run front-end tests
cd frontend && npm test

# Front-end dev server (Webpack)
cd frontend && npm start
```

Commit convention: one commit per feature / refactor / bug-fix / test. Use imperative mood: `add`, `fix`, `refactor`, `test`, `chore`.
