# Shipping Manager

Stock control and truck load planning for a steel pipe industry.

- **Stock Control** — barcode-label registry with status lifecycle, two-level warehouse location, customer order assignment, and scan-based idle tracking
- **Bin-Packing** — automatic truck load generation with weight, length, market type (MI/ME), country, and order-condition filters

See [CLAUDE.md](./CLAUDE.md) for schemas, environment variables, directory structure, and development workflow.

---

## Architectural Decisions

### Back-end framework: FastAPI over Flask or Django

Flask is minimal but gives you nothing — you wire up validation, serialisation, and async support yourself. Django is the opposite extreme: it brings an ORM, admin, templating, and auth, most of which you'd fight against in a pure API. FastAPI sits in the middle: async-native, automatic OpenAPI docs, and Pydantic validation built in. For a dashboard that does a lot of filtering and a CPU-bound bin-packing algorithm, async request handling and clean schema validation matter more than Django's batteries.

### Database: PostgreSQL over MySQL or SQLite

SQLite can't handle concurrent writes safely — fine for dev, unusable in production with Celery workers hitting the DB simultaneously. MySQL is valid but PostgreSQL has two things this project specifically needs: `JSONB` (for storing bin-packing position data without a separate table) and strong support for `ENUM` types and partial indexes. The `label_status` and `order_condition` enums benefit from DB-level enforcement, not just application-level.

### Redis for both cache and Celery broker

The project has two async needs: background jobs (stock snapshot, idle watchdog, report generator) and caching expensive bin-packing results or heavy filter queries. Redis handles both. Running a separate message broker (RabbitMQ) alongside a separate cache (Memcached) for a system this size would be over-engineering. One Redis instance covers both, and Docker Compose makes it trivial to add.

### SQLAlchemy 2.x async over sync SQLAlchemy or Tortoise ORM

FastAPI is async. If you use synchronous SQLAlchemy, every DB call blocks the event loop and you lose the concurrency benefit entirely. SQLAlchemy 2.x introduced a proper async API (`AsyncSession`, `async with`, `await session.execute()`). Tortoise ORM is async-native too, but its migration tooling (Aerich) is less mature than Alembic and its ecosystem is smaller. SQLAlchemy + Alembic is the established combination with the most production history.

### Alembic for migrations

It's the standard for SQLAlchemy projects. The `--autogenerate` flag compares your ORM models to the current DB schema and writes the migration for you. The alternative — writing raw SQL migrations by hand — is slower and error-prone for schema-heavy work like this.

### Pydantic v2 for validation

FastAPI requires Pydantic. v2 was chosen over v1 because it's significantly faster (rewritten in Rust) and it's now the default. No reason to start a new project on a deprecated version.

### Celery for background jobs

The project has three scheduled jobs and potentially on-demand heavy computation (bin-packing for large datasets). Celery with Redis as broker is the standard Python answer for this. The alternative — running cron directly on the server — works but gives you no retry logic, no visibility into job state, and no way to trigger jobs on demand from the API. Celery gives you all three.

### JWT for auth

The system is a single-tenant internal dashboard, not a multi-tenant SaaS. JWT is stateless, works well with FastAPI, and doesn't require a session store. OAuth2 would be overkill unless SSO with an existing corporate identity provider becomes a requirement.

### pytest + pytest-asyncio + httpx for testing

pytest is the Python testing standard. `pytest-asyncio` is required because all route handlers and services are async — without it you can't `await` inside tests. `httpx` has an `AsyncClient` that lets you test FastAPI endpoints in-process without spinning up a real server, which is faster and more reliable than `requests` against a live server.

### Black + Flake8 + isort over just Ruff

Ruff is faster and can replace all three, but it's a newer tool. The CI description named specific tools by analogy (one for style, one for vulnerabilities, one for security). Mapping to the established Python equivalents rather than consolidating into Ruff keeps each concern named and independently configurable. Ruff is a valid alternative — just a different trade-off.

### Bandit + pip-audit for security

Direct equivalents to the CI requirements. Bandit does static analysis for common Python security mistakes (hardcoded secrets, use of `eval`, `subprocess` with `shell=True`). pip-audit checks dependencies against known CVE databases. Both run fast enough to be in CI on every commit.

### shadcn/ui + Recharts for the front-end UI

The project requires a dashboard: data tables, filter panels, status badges, and charts. shadcn/ui gives you unstyled, composable primitives (built on Radix UI) that you own — no fighting a component library's opinions about spacing or colour. Recharts is the most common React charting library and integrates cleanly with TanStack Query data. Alternatives like MUI or Ant Design would work but bring heavier opinions and bundle size for an internal data-dense tool.

### Zustand over Redux or React Context

Redux is the right answer for large teams with complex shared state. This is a dashboard with two main data domains (stock and shipments). Zustand gives you global state in ~10 lines with no boilerplate, no reducers, no action creators. Context would work but causes unnecessary re-renders without careful memoisation. Zustand is the pragmatic middle ground.

### TanStack Query v5 for data fetching

The dashboard is read-heavy: lists, filters, KPI counts. TanStack Query handles caching, background refetching, pagination, and cache invalidation after mutations — all things you'd have to build manually with `useEffect` + `fetch`. It also integrates cleanly with Zustand: TanStack Query owns server state, Zustand owns UI state. SWR is a valid alternative but has a smaller feature set for mutations and cache invalidation.

### React Hook Form + Zod for forms

The bin-packing wizard and truck/order forms have validation logic. Zod schemas can be shared between the form validator and the TypeScript types — define the schema once and get both runtime validation and the compile-time type for free. React Hook Form avoids re-rendering the entire form on every keystroke, which matters for complex forms with many fields.

### Vitest over Jest

Vite is the build tool. Vitest is its native test runner — same config, same module resolution, no separate Babel/Jest transform pipeline to maintain. Jest requires `jest.config.ts`, `babel.config.js`, and ESM interop workarounds when using Vite. Vitest eliminates all of that.

### Tailwind CSS

Consistent with shadcn/ui, which is built on Tailwind. The alternative — CSS modules or styled-components — would require maintaining a separate design system. Tailwind's utility classes keep styles co-located with components, which matters for a dashboard where layout iterates frequently.

### Docker + Docker Compose

The project has four runtime dependencies: FastAPI, PostgreSQL, Redis, Celery worker. Without Docker, every developer sets these up differently and "works on my machine" bugs multiply. Docker Compose defines the entire stack in one file. The dev experience is `docker compose up -d` and everything is running.

### Repository pattern

Services shouldn't contain raw SQLAlchemy queries. If they do, testing the service logic requires either a real database or mocking SQLAlchemy internals — both are painful. Repositories isolate all DB access behind a clean interface. Services depend on that interface, not on SQLAlchemy directly, so unit tests can use simple fakes without touching the DB.

### Service layer separate from route handlers

Route handlers (FastAPI) should only do three things: parse the request, call a service, return the response. Business logic — status transitions, bin-packing constraints, order assignment rules — belongs in services. If logic lives in route handlers it can't be tested without an HTTP request, it can't be reused across endpoints, and it can't be called from Celery jobs. The service layer solves all three.

### FFD (First Fit Decreasing) for bin-packing

3D bin-packing is NP-hard. Exact solutions don't scale. FFD is a well-understood greedy heuristic: sort items by the dominant dimension descending, then fit each item into the first bin where it fits. For steel pipes, the dominant dimension is `volume_tons` (weight constraint), with `actual_length_m` as a hard per-item constraint. FFD typically achieves within 11/9 of optimal, which is acceptable for a load planning tool where the dispatcher reviews and adjusts the result. A more complex algorithm (simulated annealing, genetic algorithm) would add implementation complexity without a meaningful practical gain here.

### `progressivo` as primary key (VARCHAR), not a generated UUID

The barcode is the real-world identity of a label. Warehouse scanners produce it; it's already unique and stable. Generating a surrogate UUID alongside it would create two identities for the same physical object. Any scan event, import, or integration would need to resolve barcode → UUID before doing anything — unnecessary indirection. The PK *is* the barcode.

### `volume_tons` instead of `weight_kg`

`Volume Geral` in the source data ranged from near 0 to 9,230. Cross-checking a sample label (694 pieces of a 60.3mm pipe at `Volume Geral = 0.322`) gives ~0.46 kg per pipe — consistent only if the unit is metric tons (322 kg total), not kg (which would imply 322 kg for 694 small pipes). Naming it `weight_kg` would have been a silent unit mismatch that corrupts every bin-packing calculation.

### `actual_length_m` is nullable

18,655 of 26,873 rows (~70%) had `Comprimento Real` populated. The remaining ~30% were plates, fittings, and assemblies — items that don't have a meaningful length. Making the column `NOT NULL` would either block those items from being stored or force fake values into the DB. The bin-packing service treats `NULL` as "no length constraint" for those items.

### Product `description` kept as a single field (no parsed sub-fields)

The pipe spec is encoded as `60,30x3,00x6000-NBR5580-CL Rir BSP Galv`. It would be possible to parse out `diameter_mm`, `wall_thickness_mm`, `nominal_length_m`, `standard`, `threading`, and `treatment` into separate columns. Two reasons not to: (a) not all products follow that pattern — plates and fittings have free-form descriptions; (b) parsing rules derived from one data export could break on edge cases in the live ERP. The raw description is always correct; parsed fields derived from a fragile regex aren't. If filtering by diameter becomes a requirement, that's the moment to build and test a reliable parser.

### `order_condition` as an enum, not free text

`Pedido Condição` had five distinct values in Portuguese: `Fixo Futuro`, `Pedido até Hoje`, `Antecipa Futuro`, `Fixo Mês Atual`, `Antecipa Mês Atual`. These are business-critical for bin-packing prioritisation — `Pedido até Hoje` (due today) should load before `Fixo Futuro` (future). Free text makes ordering and filtering unreliable. The enum enforces the known vocabulary at the DB level.

### `market_type` (MI/ME) as a hard constraint on bin-packing

Domestic and export cargo cannot be mixed on the same truck in a customs-compliant operation. Making `market_type` an enum on both `stock_labels` and `shipments` makes this constraint explicit, queryable, and enforced in the service layer rather than buried in a comment.

### `embarque_id` as VARCHAR, not a boolean

The source columns `Embarque Fifo` and `Embarque Etiq` appeared to be flags at first glance. The actual data showed they were either `0` (unassigned), `-` (no data), or a 7-digit number (e.g. `2652025`) — a shipment reference from an external system. Storing it as a boolean would have discarded the shipment ID, making reconciliation with the external system impossible.
