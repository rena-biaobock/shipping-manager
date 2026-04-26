import angular from 'angular';
import 'angular-mocks';
import '../app.module';
import './bin-packing.service';

describe('BinPackingService', function() {
  var BinPackingService, $httpBackend, API_BASE_URL;

  beforeEach(angular.mock.module('shippingManager'));

  beforeEach(inject(function(_BinPackingService_, _$httpBackend_, _API_BASE_URL_) {
    BinPackingService = _BinPackingService_;
    $httpBackend = _$httpBackend_;
    API_BASE_URL = _API_BASE_URL_;
  }));

  afterEach(function() {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  describe('canConfirmLoad', function() {
    it('returns true when destination is set and items is non-empty', function() {
      expect(BinPackingService.canConfirmLoad({
        destination: 'Porto de Santos', items: [{ progressivo: 'LBL-001' }],
      })).toBe(true);
    });

    it('returns false when destination is empty string', function() {
      expect(BinPackingService.canConfirmLoad({
        destination: '', items: [{ progressivo: 'LBL-001' }],
      })).toBe(false);
    });

    it('returns false when destination is whitespace only', function() {
      expect(BinPackingService.canConfirmLoad({
        destination: '   ', items: [{ progressivo: 'LBL-001' }],
      })).toBe(false);
    });

    it('returns false when items is empty', function() {
      expect(BinPackingService.canConfirmLoad({
        destination: 'Porto', items: [],
      })).toBe(false);
    });

    it('returns false when items is undefined', function() {
      expect(BinPackingService.canConfirmLoad({
        destination: 'Porto',
      })).toBe(false);
    });
  });

  describe('generate', function() {
    it('POSTs to /bin-packing with truck_capacity_tons and filters', function() {
      $httpBackend.expectPOST(API_BASE_URL + '/bin-packing', {
        truck_capacity_tons: 27,
        max_iterations: 1000,
        filters: { warehouse_code: null, customer: null },
      }).respond(200, { items: [], total_weight_tons: 0, partial: false });

      BinPackingService.generate({}, 27, 1000);
      $httpBackend.flush();
    });

    it('maps warehouse filter to warehouse_code', function() {
      $httpBackend.expectPOST(API_BASE_URL + '/bin-packing', {
        truck_capacity_tons: 31,
        max_iterations: 1000,
        filters: { warehouse_code: 'A01', customer: null },
      }).respond(200, { items: [], total_weight_tons: 0, partial: false });

      BinPackingService.generate({ warehouse: 'A01' }, 31, 1000);
      $httpBackend.flush();
    });

    it('uses default 1000 max_iterations when not supplied', function() {
      $httpBackend.expectPOST(API_BASE_URL + '/bin-packing', {
        truck_capacity_tons: 38,
        max_iterations: 1000,
        filters: { warehouse_code: null, customer: null },
      }).respond(200, { items: [], total_weight_tons: 0, partial: false });

      BinPackingService.generate({}, 38);
      $httpBackend.flush();
    });
  });

  describe('createLoad', function() {
    it('POSTs to /loads with progressivo list', function() {
      var items = [{ progressivo: 'LBL-001' }, { progressivo: 'LBL-002' }];
      $httpBackend.expectPOST(API_BASE_URL + '/loads', {
        truck_capacity_tons: 27,
        destination: 'Porto de Santos',
        items: ['LBL-001', 'LBL-002'],
      }).respond(201, { id: 'LD-NEW' });

      BinPackingService.createLoad(27, 'Porto de Santos', items);
      $httpBackend.flush();
    });
  });
});
