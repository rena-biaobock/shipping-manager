const XLSX = require('xlsx');
const path = require('path');

const XLSX_PATH = process.env.XLSX_PATH || path.join(__dirname, '../../stock.xlsx');

const CONDITION_MAP = {
  'antecipa futuro':       'antecipa_futuro',
  'fixo futuro':           'fixo_futuro',
  'pedido até hoje':       'pedido_ate_hoje',
  'pedido ate hoje':       'pedido_ate_hoje',
  'fixo mês atual':        'fixo_mes_atual',
  'fixo mes atual':        'fixo_mes_atual',
  'antecipa mês atual':    'antecipa_mes_atual',
  'antecipa mes atual':    'antecipa_mes_atual',
};

function mapRow(row) {
  const embarqueRaw = String(row['Embarque Etiq'] ?? '0').trim();
  const embarqueId  = embarqueRaw !== '0' ? embarqueRaw : null;
  const hasPedido   = !!(row['Pedido']);

  let status;
  if (embarqueId) {
    status = 'in_transit_to_terminal';
  } else if (hasPedido) {
    status = 'reserved';
  } else {
    status = 'available_in_stock';
  }

  let exitDate = null;
  if (row['Data Saida Pedido']) {
    const d = new Date(row['Data Saida Pedido']);
    if (!isNaN(d)) exitDate = d.toISOString().slice(0, 10);
  }

  const condKey = (row['Pedido Condição'] || '').toLowerCase();

  return {
    progressivo:        String(row['progressivo'] || ''),
    item_code:          String(row['Item'] || ''),
    description:        String(row['Descricao'] || ''),
    customer:           String(row['Cliente Ped'] || ''),
    country:            String(row['País'] || ''),
    order_number:       row['Pedido'] ? String(row['Pedido']) : null,
    is_standard_bundle: row['Fardo Padrão'] === 'Sim',
    embarque_id:        embarqueId,
    // Volume Geral is in kg in the source file → convert to metric tons
    volume_tons:        (parseFloat(row['Volume Geral']) || 0) / 1000,
    piece_count:        parseInt(String(row['Qt PC'] || '0'), 10) || 0,
    order_condition:    CONDITION_MAP[condKey] ?? (condKey.replace(/\s+/g, '_') || null),
    exit_date:          exitDate,
    warehouse_code:     String(row['Wharehouse'] || ''),
    status,
    actual_length_m:    null,
    address:            null,
    nf:                 null,
    invoice:            null,
    scan_count:         0,
    last_scanned_at:    null,
    days_without_scan:  null,
    avg_days_idle:      null,
  };
}

let _cache = null;

function loadLabels() {
  if (_cache) return _cache;
  const wb   = XLSX.readFile(XLSX_PATH);
  const ws   = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(ws, { defval: null });
  _cache = rows.map(mapRow).filter(r => r.progressivo);
  return _cache;
}

function invalidateCache() {
  _cache = null;
}

module.exports = { loadLabels, invalidateCache };
