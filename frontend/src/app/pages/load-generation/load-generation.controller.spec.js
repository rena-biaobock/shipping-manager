import angular from 'angular';
import 'angular-mocks';
import '../../app.module';
import '../../services/stock.service';
import '../../services/bin-packing.service';
import './load-generation.controller';

describe('LoadGenController', function() {
  var $controller, $rootScope, $q, StockService, BinPackingService;

  var sampleLabels = [
    { warehouse_code: 'WH-A', customer: 'Alpha Corp', progressivo: 'LBL-001', volume_tons: 10 },
    { warehouse_code: 'WH-B', customer: 'Beta Ltd',   progressivo: 'LBL-002', volume_tons: 15 },
    { warehouse_code: 'WH-A', customer: 'Alpha Corp', progressivo: 'LBL-003', volume_tons: 8 },
  ];

  var sampleBins = [
    { _id: 'GEN-001', items: [sampleLabels[0]], totalTons: 10.0, totalPcs: 3, partial: false },
    { _id: 'GEN-002', items: [sampleLabels[1]], totalTons: 15.0, totalPcs: 2, partial: true },
  ];

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_$controller_, _$rootScope_, _$q_, _StockService_, _BinPackingService_) {
    $controller   = _$controller_;
    $rootScope    = _$rootScope_;
    $q            = _$q_;
    StockService  = _StockService_;
    BinPackingService = _BinPackingService_;
  }));

  function makeVm(labels, bins) {
    spyOn(StockService,      'getLabels')    .and.returnValue($q.resolve({ data: labels || sampleLabels }));
    spyOn(BinPackingService, 'generate')     .and.returnValue($q.resolve({ data: bins   || sampleBins  }));
    spyOn(BinPackingService, 'createLoad')   .and.returnValue($q.resolve({ data: { id: 'LD-NEW' } }));
    var vm = $controller('LoadGenController');
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
      expect(vm.warehouses).toEqual(['WH-A', 'WH-B']);
    });

    it('deduplicates warehouse_code entries', function() {
      var vm = makeVm([
        { warehouse_code: 'WH-A', customer: 'X' },
        { warehouse_code: 'WH-A', customer: 'Y' },
      ]);
      expect(vm.warehouses.length).toBe(1);
      expect(vm.warehouses[0]).toBe('WH-A');
    });

    it('excludes null/empty warehouse_code values', function() {
      var vm = makeVm([
        { warehouse_code: 'WH-A', customer: 'X' },
        { warehouse_code: null,   customer: 'Y' },
        { warehouse_code: '',     customer: 'Z' },
      ]);
      expect(vm.warehouses).toEqual(['WH-A']);
    });

    it('populates vm.customers with sorted unique customer names', function() {
      var vm = makeVm();
      expect(vm.customers).toEqual(['Alpha Corp', 'Beta Ltd']);
    });

    it('deduplicates customer entries', function() {
      var vm = makeVm([
        { warehouse_code: 'WH-A', customer: 'Same' },
        { warehouse_code: 'WH-B', customer: 'Same' },
      ]);
      expect(vm.customers.length).toBe(1);
    });

    it('excludes null/empty customer values', function() {
      var vm = makeVm([
        { warehouse_code: 'WH-A', customer: 'Real' },
        { warehouse_code: 'WH-B', customer: null },
      ]);
      expect(vm.customers).toEqual(['Real']);
    });

    it('defaults vm.filters.warehouse to "all"', function() {
      var vm = makeVm();
      expect(vm.filters.warehouse).toBe('all');
    });

    it('defaults vm.filters.customer to "all"', function() {
      var vm = makeVm();
      expect(vm.filters.customer).toBe('all');
    });

    it('defaults vm.maxTons to 31', function() {
      var vm = makeVm();
      expect(vm.maxTons).toBe(31);
    });

    it('exposes capacities array [27, 31, 38]', function() {
      var vm = makeVm();
      expect(vm.capacities).toEqual([27, 31, 38]);
    });

    it('starts with no generated plans', function() {
      var vm = makeVm();
      expect(vm.generated).toEqual([]);
    });
  });

  describe('generate()', function() {
    it('passes null warehouse and customer when both filters are "all"', function() {
      var vm = makeVm();
      vm.generate();
      $rootScope.$digest();
      expect(BinPackingService.generate).toHaveBeenCalledWith(
        { warehouse: null, customer: null }, 31, 1000
      );
    });

    it('passes selected warehouse when not "all"', function() {
      var vm = makeVm();
      vm.filters.warehouse = 'WH-A';
      vm.generate();
      $rootScope.$digest();
      expect(BinPackingService.generate).toHaveBeenCalledWith(
        { warehouse: 'WH-A', customer: null }, 31, 1000
      );
    });

    it('passes selected customer when not "all"', function() {
      var vm = makeVm();
      vm.filters.customer = 'Alpha Corp';
      vm.generate();
      $rootScope.$digest();
      expect(BinPackingService.generate).toHaveBeenCalledWith(
        { warehouse: null, customer: 'Alpha Corp' }, 31, 1000
      );
    });

    it('passes currently selected maxTons', function() {
      var vm = makeVm();
      vm.maxTons = 27;
      vm.generate();
      $rootScope.$digest();
      expect(BinPackingService.generate).toHaveBeenCalledWith(
        jasmine.any(Object), 27, 1000
      );
    });

    it('populates vm.generated from the response', function() {
      var vm = makeVm();
      vm.generate();
      $rootScope.$digest();
      expect(vm.generated.length).toBe(2);
      expect(vm.generated[0]._id).toBe('GEN-001');
      expect(vm.generated[1]._id).toBe('GEN-002');
    });

    it('maps bin items into each generated plan', function() {
      var vm = makeVm();
      vm.generate();
      $rootScope.$digest();
      expect(vm.generated[0].items.length).toBe(1);
      expect(vm.generated[0].totalTons).toBe(10.0);
    });

    it('resets vm.generated on each new generate call', function() {
      var vm = makeVm();
      vm.generate();
      $rootScope.$digest();
      BinPackingService.generate.and.returnValue($q.resolve({ data: [] }));
      vm.generate();
      $rootScope.$digest();
      expect(vm.generated.length).toBe(0);
    });

    it('sets vm.generating to true synchronously when called', function() {
      var deferred = $q.defer();
      spyOn(StockService, 'getLabels').and.returnValue($q.resolve({ data: sampleLabels }));
      spyOn(BinPackingService, 'generate').and.returnValue(deferred.promise);
      spyOn(BinPackingService, 'createLoad');
      var vm = $controller('LoadGenController');
      $rootScope.$digest();

      vm.generate();
      expect(vm.generating).toBe(true);
    });

    it('clears vm.generating after successful response', function() {
      var vm = makeVm();
      vm.generate();
      $rootScope.$digest();
      expect(vm.generating).toBe(false);
    });

    it('sets vm.error on API failure', function() {
      spyOn(StockService, 'getLabels').and.returnValue($q.resolve({ data: sampleLabels }));
      spyOn(BinPackingService, 'generate').and.callFake(function() { return $q.reject('server error'); });
      spyOn(BinPackingService, 'createLoad');
      var vm = $controller('LoadGenController');
      $rootScope.$digest();

      vm.generate();
      $rootScope.$digest();
      expect(vm.error).toBe('Failed to generate load plan.');
    });

    it('clears vm.generating on API failure', function() {
      spyOn(StockService, 'getLabels').and.returnValue($q.resolve({ data: sampleLabels }));
      spyOn(BinPackingService, 'generate').and.callFake(function() { return $q.reject('error'); });
      spyOn(BinPackingService, 'createLoad');
      var vm = $controller('LoadGenController');
      $rootScope.$digest();

      vm.generate();
      $rootScope.$digest();
      expect(vm.generating).toBe(false);
    });
  });

  describe('confirm()', function() {
    it('does nothing when canConfirmLoad returns false', function() {
      var vm = makeVm();
      spyOn(BinPackingService, 'canConfirmLoad').and.returnValue(false);
      vm.confirm({ _id: 'GEN-001', destination: '', items: [] });
      expect(BinPackingService.createLoad).not.toHaveBeenCalled();
    });

    it('calls BinPackingService.createLoad with maxTons, destination and items', function() {
      var vm = makeVm();
      spyOn(BinPackingService, 'canConfirmLoad').and.returnValue(true);
      var plan = { _id: 'GEN-001', destination: 'Porto de Santos', items: [sampleLabels[0]] };
      vm.confirm(plan);
      $rootScope.$digest();
      expect(BinPackingService.createLoad).toHaveBeenCalledWith(
        vm.maxTons, 'Porto de Santos', [sampleLabels[0]]
      );
    });

    it('marks the plan as confirmed on success', function() {
      var vm = makeVm();
      spyOn(BinPackingService, 'canConfirmLoad').and.returnValue(true);
      var plan = { _id: 'GEN-001', destination: 'Porto de Santos', items: [sampleLabels[0]] };
      vm.confirm(plan);
      $rootScope.$digest();
      expect(vm.confirmed['GEN-001']).toBe(true);
    });

    it('sets vm.error when createLoad fails', function() {
      spyOn(StockService, 'getLabels').and.returnValue($q.resolve({ data: sampleLabels }));
      spyOn(BinPackingService, 'generate').and.returnValue($q.resolve({ data: sampleBins }));
      spyOn(BinPackingService, 'createLoad').and.callFake(function() { return $q.reject('error'); });
      spyOn(BinPackingService, 'canConfirmLoad').and.returnValue(true);
      var vm = $controller('LoadGenController');
      $rootScope.$digest();

      vm.confirm({ _id: 'GEN-001', destination: 'Porto', items: [sampleLabels[0]] });
      $rootScope.$digest();
      expect(vm.error).toBe('Failed to confirm load.');
    });
  });

  describe('canConfirm()', function() {
    it('delegates to BinPackingService.canConfirmLoad', function() {
      var vm = makeVm();
      spyOn(BinPackingService, 'canConfirmLoad').and.returnValue(true);
      var plan = { destination: 'Porto', items: [sampleLabels[0]] };
      var result = vm.canConfirm(plan);
      expect(BinPackingService.canConfirmLoad).toHaveBeenCalledWith(plan);
      expect(result).toBe(true);
    });
  });
});
