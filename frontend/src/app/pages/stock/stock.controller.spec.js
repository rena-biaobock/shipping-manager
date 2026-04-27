import angular from 'angular';
import 'angular-mocks';
import '../../app.module';
import '../../services/stock.service';
import './stock.controller';

describe('StockController', function() {
  var $controller, $rootScope, $q, StockService;

  var sampleLabels = [
    {
      progressivo: 'LBL-001', item_code: 'PIPE-001', description: 'Steel pipe 3"',
      customer: 'Alpha Corp', country: 'Brazil', order_number: 'ORD-100',
      status: 'available_in_stock', warehouse_code: 'A01',
      is_standard_bundle: true, order_condition: 'fixo_mes_atual',
      exit_date: '2026-05-10', volume_tons: '1.5', piece_count: 10,
    },
    {
      progressivo: 'LBL-002', item_code: 'PIPE-002', description: 'Steel pipe 4"',
      customer: 'Beta Ltd', country: 'Argentina', order_number: null,
      status: 'reserved', warehouse_code: 'B02',
      is_standard_bundle: false, order_condition: 'pedido_ate_hoje',
      exit_date: '2026-06-01', volume_tons: '2.0', piece_count: 5,
    },
    {
      progressivo: 'LBL-003', item_code: 'PIPE-003', description: 'Fitting',
      customer: 'Alpha Corp', country: 'Brazil', order_number: null,
      status: 'idle', warehouse_code: 'A01',
      is_standard_bundle: false, order_condition: null,
      exit_date: null, volume_tons: '0.8', piece_count: 3,
    },
  ];

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_$controller_, _$rootScope_, _$q_, _StockService_) {
    $controller  = _$controller_;
    $rootScope   = _$rootScope_;
    $q           = _$q_;
    StockService = _StockService_;
  }));

  function makeVm(labels) {
    spyOn(StockService, 'getLabels').and.returnValue($q.resolve({ data: labels || sampleLabels }));
    var vm = $controller('StockController');
    $rootScope.$digest();
    return vm;
  }

  describe('initialisation', function() {
    it('calls StockService.getLabels on init', function() {
      makeVm();
      expect(StockService.getLabels).toHaveBeenCalled();
    });

    it('populates vm.warehouses with sorted unique warehouse_code values', function() {
      var vm = makeVm();
      expect(vm.warehouses).toEqual(['A01', 'B02']);
    });

    it('deduplicates warehouse_code entries', function() {
      var vm = makeVm([
        { warehouse_code: 'A01', customer: 'X', volume_tons: '1.0', piece_count: 1 },
        { warehouse_code: 'A01', customer: 'Y', volume_tons: '1.0', piece_count: 1 },
      ]);
      expect(vm.warehouses.length).toBe(1);
      expect(vm.warehouses[0]).toBe('A01');
    });

    it('excludes null/empty warehouse_code from vm.warehouses', function() {
      var vm = makeVm([
        { warehouse_code: 'A01', customer: 'X', volume_tons: '1.0', piece_count: 1 },
        { warehouse_code: null,  customer: 'Y', volume_tons: '1.0', piece_count: 1 },
        { warehouse_code: '',    customer: 'Z', volume_tons: '1.0', piece_count: 1 },
      ]);
      expect(vm.warehouses).toEqual(['A01']);
    });

    it('defaults filters to all/empty', function() {
      var vm = makeVm();
      expect(vm.filters.status).toBe('all');
      expect(vm.filters.warehouse).toBe('all');
      expect(vm.filters.stdBundle).toBe('all');
      expect(vm.filters.condition).toBe('all');
      expect(vm.filters.exitDateFrom).toBe('');
      expect(vm.filters.exitDateTo).toBe('');
    });

    it('sets vm.loading to false after data loads', function() {
      var vm = makeVm();
      expect(vm.loading).toBe(false);
    });

    it('populates vm.labels with fetched data', function() {
      var vm = makeVm();
      expect(vm.labels.length).toBe(3);
    });

    it('sets vm.error on service failure', function() {
      spyOn(StockService, 'getLabels').and.returnValue($q.reject());
      var vm = $controller('StockController');
      $rootScope.$digest();
      expect(vm.error).toBeTruthy();
      expect(vm.loading).toBe(false);
    });
  });

  describe('applyFilters', function() {
    it('sets vm.filtered to all labels with default filters', function() {
      var vm = makeVm();
      expect(vm.filtered.length).toBe(3);
    });

    it('computes vm.totalTons from filtered list', function() {
      var vm = makeVm();
      expect(vm.totalTons).toBeCloseTo(4.3, 1);
    });

    it('computes vm.totalPcs from filtered list', function() {
      var vm = makeVm();
      expect(vm.totalPcs).toBe(18);
    });

    it('resets to page 1 when filters change', function() {
      var vm = makeVm();
      vm.currentPage = 3;
      vm.applyFilters();
      expect(vm.currentPage).toBe(1);
    });
  });

  describe('pagination', function() {
    it('goToPage updates currentPage and refreshes vm.page', function() {
      var bigList = [];
      for (var i = 0; i < 30; i++) {
        bigList.push({ progressivo: 'L-' + i, warehouse_code: 'A', customer: 'X',
                       status: 'idle', volume_tons: '1.0', piece_count: 1 });
      }
      var vm = makeVm(bigList);
      vm.goToPage(2);
      expect(vm.currentPage).toBe(2);
      expect(vm.page.length).toBe(5);
    });

    it('goToPage ignores out-of-range pages', function() {
      var vm = makeVm();
      vm.goToPage(0);
      expect(vm.currentPage).toBe(1);
      vm.goToPage(999);
      expect(vm.currentPage).toBe(1);
    });
  });

  describe('fmtTons', function() {
    it('formats a number with one decimal and t suffix', function() {
      var vm = makeVm();
      expect(vm.fmtTons(12.345)).toBe('12.3 t');
    });

    it('returns 0 t for null/undefined', function() {
      var vm = makeVm();
      expect(vm.fmtTons(null)).toBe('0 t');
    });
  });
});
