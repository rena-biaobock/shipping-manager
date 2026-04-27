const express = require('express');
const crypto  = require('crypto');
const { loadLabels } = require('../data');

const router     = express.Router();
const loadsStore = new Map();

const TRANSITIONS = {
  pending:     'in_transit',
  in_transit:  'dispatched',
  dispatched:  'delivered',
};

router.get('/', (_req, res) => {
  const list = [...loadsStore.values()].map(({ items: _, ...rest }) => rest);
  res.json(list);
});

router.get('/:id/items', (req, res) => {
  const load = loadsStore.get(req.params.id);
  if (!load) return res.status(404).json({ error: 'Load not found' });
  res.json(load.items);
});

router.post('/', (req, res) => {
  const { truck_capacity_tons, destination, items } = req.body || {};
  if (!destination || !truck_capacity_tons || !Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'destination, truck_capacity_tons, and items[] are required' });
  }

  const labelMap      = new Map(loadLabels().map(l => [l.progressivo, l]));
  const resolvedItems = items.map(p => labelMap.get(String(p))).filter(Boolean);
  const totalWeightTons = parseFloat(
    resolvedItems.reduce((s, l) => s + l.volume_tons, 0).toFixed(4)
  );

  const id   = crypto.randomUUID();
  const load = {
    id,
    truck_capacity_tons,
    destination,
    status:            'pending',
    total_weight_tons: totalWeightTons,
    created_at:        new Date().toISOString(),
    dispatched_at:     null,
    delivered_at:      null,
    items:             resolvedItems,
  };

  loadsStore.set(id, load);
  const { items: _, ...body } = load;
  res.status(201).json({ ...body, item_count: resolvedItems.length });
});

router.patch('/:id/status', (req, res) => {
  const load = loadsStore.get(req.params.id);
  if (!load) return res.status(404).json({ error: 'Load not found' });

  const next = TRANSITIONS[load.status];
  if (!next) return res.status(422).json({ error: `No valid transition from '${load.status}'` });

  load.status = next;
  if (next === 'in_transit') load.dispatched_at = new Date().toISOString();
  if (next === 'delivered')  load.delivered_at  = new Date().toISOString();

  const { items: _, ...body } = load;
  res.json(body);
});

module.exports = { router, loadsStore };
