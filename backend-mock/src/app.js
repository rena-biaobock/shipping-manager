const express         = require('express');
const stockLabels     = require('./routes/stock-labels');
const { router: loads } = require('./routes/loads');
const binPacking      = require('./routes/bin-packing');

const app = express();

app.use(express.json());

app.use((req, res, next) => {
  const allowed = (process.env.CORS_ORIGINS || 'http://localhost,http://localhost:4200').split(',');
  const origin  = req.headers.origin;
  if (origin && (allowed.includes(origin) || allowed.includes('*'))) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.use('/web/api/v1/stock-labels', stockLabels);
app.use('/web/api/v1/loads',        loads);
app.use('/web/api/v1/bin-packing',  binPacking);

module.exports = app;
