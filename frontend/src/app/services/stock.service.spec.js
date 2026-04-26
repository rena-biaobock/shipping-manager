import angular from 'angular';
import 'angular-mocks';
import '../app.module';
import './stock.service';

describe('StockService', function() {
  var StockService;

  var sampleLabels = [
    {
      progressivo: 'LBL-001', item_code: 'PIPE-001', description: 'Steel pipe 3"',
      customer: 'Acme Corp', country: 'Brazil', order_number: 'ORD-100',
      embarque_id: null, nf: 'NF-001', invoice: null,
      status: 'available_in_stock', warehouse_code: 'A01',
      is_standard_bundle: true, order_condition: 'fixo_mes_atual',
      exit_date: '2026-05-10', volume_tons: '1.5', piece_count: 10,
    },
    {
      progressivo: 'LBL-002', item_code: 'PIPE-002', description: 'Steel pipe 4"',
      customer: 'Globex', country: 'Argentina', order_number: 'ORD-101',
      embarque_id: 'EMB-001', nf: null, invoice: 'INV-001',
      status: 'reserved', warehouse_code: 'B02',
      is_standard_bundle: false, order_condition: 'pedido_ate_hoje',
      exit_date: '2026-06-01', volume_tons: '2.0', piece_count: 5,
    },
    {
      progressivo: 'LBL-003', item_code: 'PIPE-003', description: 'Fitting',
      customer: 'Acme Corp', country: 'Brazil', order_number: null,
      embarque_id: null, nf: null, invoice: null,
      status: 'idle', warehouse_code: 'A01',
      is_standard_bundle: false, order_condition: null,
      exit_date: null, volume_tons: '0.8', piece_count: 3,
    },
  ];

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_StockService_) {
    StockService = _StockService_;
  }));

  describe('filterLabels', function() {
    it('returns all labels when status is "all"', function() {
      var result = StockService.filterLabels(sampleLabels, { status: 'all' });
      expect(result.length).toBe(3);
    });

    it('filters by status', function() {
      var result = StockService.filterLabels(sampleLabels, { status: 'reserved' });
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-002');
    });

    it('filters by warehouse', function() {
      var result = StockService.filterLabels(sampleLabels, { warehouse: 'A01' });
      expect(result.length).toBe(2);
    });

    it('returns all when warehouse is "all"', function() {
      var result = StockService.filterLabels(sampleLabels, { warehouse: 'all' });
      expect(result.length).toBe(3);
    });

    it('filters by is_standard_bundle true', function() {
      var result = StockService.filterLabels(sampleLabels, { stdBundle: 'true' });
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-001');
    });

    it('filters by is_standard_bundle false', function() {
      var result = StockService.filterLabels(sampleLabels, { stdBundle: 'false' });
      expect(result.length).toBe(2);
    });

    it('filters by order_condition', function() {
      var result = StockService.filterLabels(sampleLabels, { condition: 'fixo_mes_atual' });
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-001');
    });

    it('filters exit_date on or after exitDateFrom', function() {
      var result = StockService.filterLabels(sampleLabels, { exitDateFrom: '2026-06-01' });
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-002');
    });

    it('filters exit_date on or before exitDateTo', function() {
      var result = StockService.filterLabels(sampleLabels, { exitDateTo: '2026-05-10' });
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-001');
    });

    it('excludes null exit_date when exitDateFrom is set', function() {
      var result = StockService.filterLabels(sampleLabels, { exitDateFrom: '2026-01-01' });
      expect(result.every(function(l) { return l.exit_date !== null; })).toBe(true);
    });
  });

  describe('searchLabels', function() {
    it('returns all labels when query is empty', function() {
      expect(StockService.searchLabels(sampleLabels, '').length).toBe(3);
    });

    it('matches progressivo case-insensitively', function() {
      expect(StockService.searchLabels(sampleLabels, 'lbl-001').length).toBe(1);
    });

    it('matches customer', function() {
      var result = StockService.searchLabels(sampleLabels, 'globex');
      expect(result.length).toBe(1);
      expect(result[0].progressivo).toBe('LBL-002');
    });

    it('matches description', function() {
      expect(StockService.searchLabels(sampleLabels, 'fitting').length).toBe(1);
    });

    it('matches invoice', function() {
      expect(StockService.searchLabels(sampleLabels, 'INV-001').length).toBe(1);
    });

    it('matches nf', function() {
      expect(StockService.searchLabels(sampleLabels, 'NF-001').length).toBe(1);
    });

    it('matches embarque_id', function() {
      expect(StockService.searchLabels(sampleLabels, 'EMB-001').length).toBe(1);
    });

    it('returns empty when no match', function() {
      expect(StockService.searchLabels(sampleLabels, 'NOMATCH_XYZ').length).toBe(0);
    });
  });

  describe('aggregateByField', function() {
    it('groups by field and sums value', function() {
      var result = StockService.aggregateByField(sampleLabels, 'country', 'volume_tons');
      var brazil = result.find(function(r) { return r.key === 'Brazil'; });
      expect(brazil).toBeDefined();
      expect(brazil.value).toBeCloseTo(2.3, 1);
    });

    it('sorts descending by value', function() {
      var result = StockService.aggregateByField(sampleLabels, 'country', 'volume_tons');
      expect(result[0].value).toBeGreaterThanOrEqual(result[result.length - 1].value);
    });

    it('returns one entry per unique key', function() {
      var result = StockService.aggregateByField(sampleLabels, 'country', 'volume_tons');
      expect(result.length).toBe(2);
    });
  });
});
