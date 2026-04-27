import angular from 'angular';
import '../app.module';

angular.module('shippingManager').service('LoadsService', ['$http', 'API_BASE_URL',
  function LoadsService($http, API_BASE_URL) {
    this.getLoads = function() {
      return $http.get(API_BASE_URL + '/loads');
    };

    this.getLoadItems = function(loadId) {
      return $http.get(API_BASE_URL + '/loads/' + loadId + '/items');
    };

    this.updateStatus = function(loadId, newStatus) {
      return $http.patch(API_BASE_URL + '/loads/' + loadId + '/status', { status: newStatus });
    };

    this.filterLoads = function(loads, filters) {
      return loads.filter(function(load) {
        if (filters.status && filters.status !== 'all' && load.status !== filters.status) {
          return false;
        }
        if (filters.destination && filters.destination !== 'all' && load.destination !== filters.destination) {
          return false;
        }
        return true;
      });
    };

    this.searchLoads = function(loads, query) {
      if (!query) return loads;
      var q = query.toLowerCase();
      return loads.filter(function(load) {
        return ['id', 'destination', 'status'].some(function(f) {
          return load[f] && load[f].toLowerCase().indexOf(q) !== -1;
        });
      });
    };

    this.sumWeightTons = function(loads) {
      return loads.reduce(function(sum, load) {
        return sum + (parseFloat(load.total_weight_tons) || 0);
      }, 0);
    };

    this.paginateLoads = function(loads, page, pageSize) {
      var total = loads.length;
      var totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
      var currentPage = Math.min(Math.max(page, 1), totalPages || 1);
      var start = (currentPage - 1) * pageSize;
      return {
        items: loads.slice(start, start + pageSize),
        currentPage: currentPage,
        totalPages: totalPages,
        totalItems: total,
      };
    };

    var TRANSITIONS = {
      pending: 'in_transit',
      in_transit: 'dispatched',
      dispatched: 'delivered',
    };

    this.getAvailableTransition = function(load) {
      return TRANSITIONS[load.status] || null;
    };
  },
]);
