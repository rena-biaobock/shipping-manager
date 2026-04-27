import angular from 'angular';
import '../app.module';

angular.module('shippingManager').service('BinPackingService', ['$http', 'API_BASE_URL',
  function BinPackingService($http, API_BASE_URL) {
    this.generate = function(filters, truckCapacityTons, maxIterations) {
      return $http.post(API_BASE_URL + '/bin-packing/', {
        truck_capacity_tons: truckCapacityTons,
        max_iterations: maxIterations || 1000,
        filters: {
          warehouse_code: filters.warehouse || null,
          customer: filters.customer || null,
        },
      });
    };

    this.createLoad = function(truckCapacityTons, destination, items) {
      return $http.post(API_BASE_URL + '/loads/', {
        truck_capacity_tons: truckCapacityTons,
        destination: destination,
        items: items.map(function(i) { return i.progressivo; }),
      });
    };

    this.canConfirmLoad = function(plan) {
      var hasDestination = !!(plan.destination && plan.destination.trim());
      var hasItems = !!(plan.items && plan.items.length > 0);
      return hasDestination && hasItems;
    };
  },
]);
