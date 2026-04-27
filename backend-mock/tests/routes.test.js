const { test, describe, beforeEach } = require('node:test');
const assert   = require('node:assert/strict');
const request  = require('supertest');
const app      = require('../src/app');
const { loadsStore } = require('../src/routes/loads');

beforeEach(() => loadsStore.clear());

// ── helpers ──────────────────────────────────────────────────────────────────

async function firstPlan(capacityTons = 27) {
  const res = await request(app)
    .post('/web/api/v1/bin-packing')
    .send({ truck_capacity_tons: capacityTons });
  return res.body[0];
}

// Returns the supertest chain (not async) so .expect() can be chained by callers.
function createLoad(plan, destination = 'Porto de Santos', capacityTons = 27) {
  return request(app)
    .post('/web/api/v1/loads')
    .send({
      truck_capacity_tons: capacityTons,
      destination,
      items: plan.items.slice(0, 3).map(i => i.progressivo),
    });
}

// ── stock-labels ──────────────────────────────────────────────────────────────

describe('GET /web/api/v1/stock-labels', () => {
  test('returns 200 with a non-empty array', async () => {
    const res = await request(app).get('/web/api/v1/stock-labels').expect(200);
    assert.ok(Array.isArray(res.body) && res.body.length > 0);
  });

  test('each label has the expected fields', async () => {
    const res   = await request(app).get('/web/api/v1/stock-labels').expect(200);
    const label = res.body[0];
    for (const f of ['progressivo', 'item_code', 'volume_tons', 'status', 'warehouse_code']) {
      assert.ok(f in label, `missing field: ${f}`);
    }
  });

  test('volume_tons is in metric tons (single bundle < 10 t)', async () => {
    const res = await request(app).get('/web/api/v1/stock-labels').expect(200);
    assert.ok(res.body.every(l => l.volume_tons < 10), 'volume_tons looks like kg, not tons');
  });

  test('status is a known enum value', async () => {
    const valid = new Set(['available_in_stock','reserved','in_transit_to_terminal',
                           'available_in_terminal','in_transit_to_client','delivered','idle','damaged']);
    const res   = await request(app).get('/web/api/v1/stock-labels').expect(200);
    for (const l of res.body) {
      assert.ok(valid.has(l.status), `unknown status: ${l.status}`);
    }
  });
});

// ── bin-packing ───────────────────────────────────────────────────────────────

describe('POST /web/api/v1/bin-packing', () => {
  test('returns 400 when truck_capacity_tons is missing', async () => {
    await request(app).post('/web/api/v1/bin-packing').send({}).expect(400);
  });

  test('returns load plans within capacity', async () => {
    const res = await request(app)
      .post('/web/api/v1/bin-packing')
      .send({ truck_capacity_tons: 27 })
      .expect(200);
    assert.ok(Array.isArray(res.body) && res.body.length > 0);
    for (const plan of res.body) {
      assert.ok(plan.totalTons <= 27 + 0.001, `plan exceeds capacity: ${plan.totalTons}`);
      assert.ok(plan.items.length > 0);
    }
  });

  test('applies customer filter', async () => {
    const full = await request(app)
      .post('/web/api/v1/bin-packing')
      .send({ truck_capacity_tons: 27 })
      .expect(200);
    const customer = full.body[0]?.items[0]?.customer;
    if (!customer) return;

    const filtered = await request(app)
      .post('/web/api/v1/bin-packing')
      .send({ truck_capacity_tons: 27, filters: { customer } })
      .expect(200);
    for (const plan of filtered.body) {
      for (const item of plan.items) {
        assert.equal(item.customer, customer);
      }
    }
  });

  test('returns fewer plans when max_iterations is low', async () => {
    const full = await request(app)
      .post('/web/api/v1/bin-packing')
      .send({ truck_capacity_tons: 27, max_iterations: 1000 });
    const limited = await request(app)
      .post('/web/api/v1/bin-packing')
      .send({ truck_capacity_tons: 27, max_iterations: 5 });
    assert.ok(limited.body.length <= full.body.length);
  });
});

// ── loads — create ────────────────────────────────────────────────────────────

describe('POST /web/api/v1/loads', () => {
  test('returns 400 when required fields are missing', async () => {
    await request(app).post('/web/api/v1/loads').send({}).expect(400);
  });

  test('creates a load with status pending', async () => {
    const plan = await firstPlan();
    const res  = await createLoad(plan).expect(201);
    assert.equal(res.body.status, 'pending');
    assert.ok(res.body.id);
    assert.equal(res.body.destination, 'Porto de Santos');
    assert.ok(res.body.total_weight_tons > 0);
  });

  test('total_weight_tons sums the resolved items', async () => {
    const plan    = await firstPlan();
    const picked  = plan.items.slice(0, 2);
    const expected = parseFloat((picked[0].volume_tons + picked[1].volume_tons).toFixed(4));
    const res = await request(app)
      .post('/web/api/v1/loads')
      .send({ truck_capacity_tons: 27, destination: 'Test', items: picked.map(i => i.progressivo) })
      .expect(201);
    assert.ok(Math.abs(res.body.total_weight_tons - expected) < 0.001);
  });
});

// ── loads — list ──────────────────────────────────────────────────────────────

describe('GET /web/api/v1/loads', () => {
  test('returns empty array when no loads exist', async () => {
    const res = await request(app).get('/web/api/v1/loads').expect(200);
    assert.deepEqual(res.body, []);
  });

  test('returns created loads', async () => {
    const plan = await firstPlan();
    await createLoad(plan);
    const res = await request(app).get('/web/api/v1/loads').expect(200);
    assert.equal(res.body.length, 1);
    assert.equal(res.body[0].status, 'pending');
  });
});

// ── loads — items ─────────────────────────────────────────────────────────────

describe('GET /web/api/v1/loads/:id/items', () => {
  test('returns 404 for unknown id', async () => {
    await request(app).get('/web/api/v1/loads/no-such-id/items').expect(404);
  });

  test('returns items matching the submitted progressivos', async () => {
    const plan       = await firstPlan();
    const picked     = plan.items.slice(0, 2);
    const createRes  = await request(app)
      .post('/web/api/v1/loads')
      .send({ truck_capacity_tons: 27, destination: 'Test', items: picked.map(i => i.progressivo) });
    const res = await request(app)
      .get(`/web/api/v1/loads/${createRes.body.id}/items`)
      .expect(200);
    assert.equal(res.body.length, picked.length);
    const returnedIds = new Set(res.body.map(i => i.progressivo));
    for (const p of picked) assert.ok(returnedIds.has(p.progressivo));
  });
});

// ── loads — status transition ─────────────────────────────────────────────────

describe('PATCH /web/api/v1/loads/:id/status', () => {
  test('returns 404 for unknown id', async () => {
    await request(app).patch('/web/api/v1/loads/no-such-id/status').expect(404);
  });

  test('pending → in_transit', async () => {
    const plan = await firstPlan();
    const { body: { id } } = await createLoad(plan);
    const res = await request(app).patch(`/web/api/v1/loads/${id}/status`).expect(200);
    assert.equal(res.body.status, 'in_transit');
    assert.ok(res.body.dispatched_at);
  });

  test('in_transit → dispatched', async () => {
    const plan = await firstPlan();
    const { body: { id } } = await createLoad(plan);
    await request(app).patch(`/web/api/v1/loads/${id}/status`);
    const res = await request(app).patch(`/web/api/v1/loads/${id}/status`).expect(200);
    assert.equal(res.body.status, 'dispatched');
  });

  test('dispatched → delivered', async () => {
    const plan = await firstPlan();
    const { body: { id } } = await createLoad(plan);
    await request(app).patch(`/web/api/v1/loads/${id}/status`);
    await request(app).patch(`/web/api/v1/loads/${id}/status`);
    const res = await request(app).patch(`/web/api/v1/loads/${id}/status`).expect(200);
    assert.equal(res.body.status, 'delivered');
    assert.ok(res.body.delivered_at);
  });

  test('returns 422 when no further transition exists (delivered)', async () => {
    const plan = await firstPlan();
    const { body: { id } } = await createLoad(plan);
    for (let i = 0; i < 3; i++) {
      await request(app).patch(`/web/api/v1/loads/${id}/status`);
    }
    await request(app).patch(`/web/api/v1/loads/${id}/status`).expect(422);
  });
});
