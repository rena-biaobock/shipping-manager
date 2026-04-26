import angular from 'angular';
import 'angular-mocks';
import '../app.module';
import './loads.service';

describe('LoadsService', function() {
  var LoadsService;

  var sampleLoads = [
    {
      id: 'LD-001', destination: 'Porto de Santos', status: 'pending',
      total_weight_tons: '25.5', truck_capacity_tons: 27,
    },
    {
      id: 'LD-002', destination: 'Terminal RJ', status: 'in_transit',
      total_weight_tons: '30.0', truck_capacity_tons: 31,
    },
    {
      id: 'LD-003', destination: 'Porto de Santos', status: 'delivered',
      total_weight_tons: '18.2', truck_capacity_tons: 27,
    },
  ];

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_LoadsService_) {
    LoadsService = _LoadsService_;
  }));

  describe('filterLoads', function() {
    it('returns all when status is "all"', function() {
      expect(LoadsService.filterLoads(sampleLoads, { status: 'all' }).length).toBe(3);
    });

    it('filters by status', function() {
      var result = LoadsService.filterLoads(sampleLoads, { status: 'pending' });
      expect(result.length).toBe(1);
      expect(result[0].id).toBe('LD-001');
    });

    it('filters by destination', function() {
      var result = LoadsService.filterLoads(sampleLoads, { destination: 'Porto de Santos' });
      expect(result.length).toBe(2);
    });

    it('returns all when destination is "all"', function() {
      expect(LoadsService.filterLoads(sampleLoads, { destination: 'all' }).length).toBe(3);
    });

    it('applies status and destination filters together', function() {
      var result = LoadsService.filterLoads(sampleLoads, {
        status: 'delivered', destination: 'Porto de Santos',
      });
      expect(result.length).toBe(1);
      expect(result[0].id).toBe('LD-003');
    });
  });

  describe('searchLoads', function() {
    it('returns all when query is empty', function() {
      expect(LoadsService.searchLoads(sampleLoads, '').length).toBe(3);
    });

    it('matches by destination case-insensitively', function() {
      var result = LoadsService.searchLoads(sampleLoads, 'terminal');
      expect(result.length).toBe(1);
      expect(result[0].id).toBe('LD-002');
    });

    it('matches by status', function() {
      var result = LoadsService.searchLoads(sampleLoads, 'delivered');
      expect(result.length).toBe(1);
    });

    it('matches by id', function() {
      var result = LoadsService.searchLoads(sampleLoads, 'LD-001');
      expect(result.length).toBe(1);
    });

    it('returns empty when no match', function() {
      expect(LoadsService.searchLoads(sampleLoads, 'NOMATCH_XYZ').length).toBe(0);
    });
  });

  describe('sumWeightTons', function() {
    it('sums total_weight_tons as floats', function() {
      var result = LoadsService.sumWeightTons(sampleLoads);
      expect(result).toBeCloseTo(73.7, 1);
    });

    it('returns 0 for empty list', function() {
      expect(LoadsService.sumWeightTons([])).toBe(0);
    });
  });

  describe('getAvailableTransition', function() {
    it('returns in_transit for pending', function() {
      expect(LoadsService.getAvailableTransition({ status: 'pending' })).toBe('in_transit');
    });

    it('returns dispatched for in_transit', function() {
      expect(LoadsService.getAvailableTransition({ status: 'in_transit' })).toBe('dispatched');
    });

    it('returns delivered for dispatched', function() {
      expect(LoadsService.getAvailableTransition({ status: 'dispatched' })).toBe('delivered');
    });

    it('returns null for delivered', function() {
      expect(LoadsService.getAvailableTransition({ status: 'delivered' })).toBeNull();
    });

    it('returns null for cancelled', function() {
      expect(LoadsService.getAvailableTransition({ status: 'cancelled' })).toBeNull();
    });

    it('returns null for draft', function() {
      expect(LoadsService.getAvailableTransition({ status: 'draft' })).toBeNull();
    });
  });
});
