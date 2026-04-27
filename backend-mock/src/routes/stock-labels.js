const express = require('express');
const { loadLabels } = require('../data');

const router = express.Router();

router.get('/', (_req, res) => {
  res.json(loadLabels());
});

module.exports = router;
