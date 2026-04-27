import angular from 'angular';
import 'angular-mocks';
import '../../app.module';
import '../../services/loads.service';
import './loads.controller';

describe('LoadsController', function() {
  var $controller, $rootScope, $q, LoadsService;

  var sampleLoads = [
    { id: 'LD-001', destination: 'Porto de Santos', status: 'pending',
      total_weight_tons: '18.5', truck_capacity_tons: 27, created_at: '2026-04-01' },
    { id: 'LD-002', destination: 'Rio de Janeiro',  status: 'in_transit',
      total_weight_tons: '25.0', truck_capacity_tons: 27, created_at: '2026-04-02' },
    { id: 'LD-003', destination: 'Porto de Santos', status: 'delivered',
      total_weight_tons: '10.0', truck_capacity_tons: 31, created_at: '2026-03-15' },
  ];

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_$controller_, _$rootScope_, _$q_, _LoadsService_) {
    $controller  = _$controller_;
    $rootScope   = _$rootScope_;
    $q           = _$q_;
    LoadsService = _LoadsService_;
  }));

  function makeVm(loads) {
    spyOn(LoadsService, 'getLoads').and.returnValue($q.resolve({ data: loads || sampleLoads }));
    var vm = $controller('LoadsController');
    $rootScope.$digest();
    return vm;
  }

  describe('initialisation', function() {
    it('calls LoadsService.getLoads on init', function() {
      makeVm();
      expect(LoadsService.getLoads).toHaveBeenCalled();
    });

    it('populates vm.loads with fetched data', function() {
      var vm = makeVm();
      expect(vm.loads.length).toBe(3);
    });

    it('sets vm.loading to false after data loads', function() {
      var vm = makeVm();
      expect(vm.loading).toBe(false);
    });

    it('sets vm.error on service failure', function() {
      spyOn(LoadsService, 'getLoads').and.returnValue($q.reject());
      var vm = $controller('LoadsController');
      $rootScope.$digest();
      expect(vm.error).toBeTruthy();
      expect(vm.loading).toBe(false);
    });

    it('populates vm.destinations with sorted unique values', function() {
      var vm = makeVm();
      expect(vm.destinations).toEqual(['Porto de Santos', 'Rio de Janeiro']);
    });

    it('does not expose loadTotalPcs on vm', function() {
      var vm = makeVm();
      expect(vm.loadTotalPcs).toBeUndefined();
    });

    it('does not expose loadTotalTons on vm', function() {
      var vm = makeVm();
      expect(vm.loadTotalTons).toBeUndefined();
    });
  });

  describe('applyFilters', function() {
    it('sets vm.filtered to all loads with default filters', function() {
      var vm = makeVm();
      expect(vm.filtered.length).toBe(3);
    });

    it('computes vm.totalTons from filtered list', function() {
      var vm = makeVm();
      expect(vm.totalTons).toBeCloseTo(53.5, 1);
    });

    it('resets to page 1 when filters change', function() {
      var vm = makeVm();
      vm.currentPage = 2;
      vm.applyFilters();
      expect(vm.currentPage).toBe(1);
    });
  });

  describe('setSort', function() {
    it('sets sortField on first call', function() {
      var vm = makeVm();
      vm.setSort('total_weight_tons');
      expect(vm.sortField).toBe('total_weight_tons');
    });

    it('toggles sortAsc when called with same field', function() {
      var vm = makeVm();
      vm.setSort('total_weight_tons');
      var first = vm.sortAsc;
      vm.setSort('total_weight_tons');
      expect(vm.sortAsc).toBe(!first);
    });

    it('resets sortAsc to false when switching fields', function() {
      var vm = makeVm();
      vm.sortAsc = true;
      vm.setSort('total_weight_tons');
      expect(vm.sortAsc).toBe(false);
    });
  });

  describe('toggleExpand', function() {
    it('expands a collapsed load', function() {
      spyOn(LoadsService, 'getLoadItems').and.returnValue($q.resolve({ data: [] }));
      var vm = makeVm();
      var load = vm.loads[0];
      vm.toggleExpand(load);
      expect(vm.expanded[load.id]).toBe(true);
    });

    it('collapses an expanded load', function() {
      spyOn(LoadsService, 'getLoadItems').and.returnValue($q.resolve({ data: [] }));
      var vm = makeVm();
      var load = vm.loads[0];
      vm.toggleExpand(load);
      vm.toggleExpand(load);
      expect(vm.expanded[load.id]).toBe(false);
    });

    it('fetches items on first expand', function() {
      spyOn(LoadsService, 'getLoadItems').and.returnValue($q.resolve({ data: [] }));
      var vm = makeVm();
      var load = vm.loads[0];
      vm.toggleExpand(load);
      expect(LoadsService.getLoadItems).toHaveBeenCalledWith(load.id);
    });

    it('does not re-fetch items if already cached', function() {
      spyOn(LoadsService, 'getLoadItems').and.returnValue($q.resolve({ data: [] }));
      var vm = makeVm();
      var load = vm.loads[0];
      vm.toggleExpand(load);
      $rootScope.$digest();
      vm.toggleExpand(load);
      vm.toggleExpand(load);
      expect(LoadsService.getLoadItems.calls.count()).toBe(1);
    });
  });

  describe('nextTransitionLabel', function() {
    it('returns label for pending load', function() {
      var vm = makeVm();
      var label = vm.nextTransitionLabel({ status: 'pending' });
      expect(label).toBe('IN TRANSIT');
    });

    it('returns null for delivered load', function() {
      var vm = makeVm();
      expect(vm.nextTransitionLabel({ status: 'delivered' })).toBeNull();
    });
  });

  describe('applyTransition', function() {
    it('updates load status after successful transition', function() {
      spyOn(LoadsService, 'updateStatus').and.returnValue($q.resolve({}));
      var vm = makeVm();
      var load = vm.loads[0];
      vm.applyTransition(load);
      $rootScope.$digest();
      expect(load.status).toBe('in_transit');
    });

    it('does nothing when no transition is available', function() {
      spyOn(LoadsService, 'updateStatus').and.returnValue($q.resolve({}));
      var vm = makeVm();
      var load = { id: 'LD-X', status: 'delivered' };
      vm.applyTransition(load);
      expect(LoadsService.updateStatus).not.toHaveBeenCalled();
    });
  });

  describe('pagination', function() {
    it('goToPage ignores out-of-range page numbers', function() {
      var vm = makeVm();
      vm.goToPage(0);
      expect(vm.currentPage).toBe(1);
    });
  });

  describe('fmtTons', function() {
    it('formats with one decimal and t suffix', function() {
      var vm = makeVm();
      expect(vm.fmtTons(5.678)).toBe('5.7 t');
    });

    it('returns 0 t for null', function() {
      var vm = makeVm();
      expect(vm.fmtTons(null)).toBe('0 t');
    });
  });
});
