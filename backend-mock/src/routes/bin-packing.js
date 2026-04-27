const express = require('express');
const { loadLabels } = require('../data');
const { ffd }        = require('../ffd');

const router = express.Router();

router.post('/', (req, res) => {
  const { truck_capacity_tons, filters = {}, max_iterations } = req.body || {};
  if (!truck_capacity_tons || truck_capacity_tons <= 0) {
    return res.status(400).json({ error: 'truck_capacity_tons is required and must be positive' });
  }

  let labels = loadLabels().filter(
    l => l.status === 'available_in_stock' || l.status === 'reserved'
  );

  if (filters.warehouse_code) {
    labels = labels.filter(l => l.warehouse_code === filters.warehouse_code);
  }
  if (filters.customer) {
    labels = labels.filter(l => l.customer === filters.customer);
  }

  const plans = ffd(labels, truck_capacity_tons, max_iterations || 1000);
  res.json(plans);
});

module.exports = router;
