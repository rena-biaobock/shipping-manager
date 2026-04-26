import angular from 'angular';
import '../app.module';

angular.module('shippingManager').service('StockService', ['$http', 'API_BASE_URL',
  function StockService($http, API_BASE_URL) {
    this.getLabels = function() {
      return $http.get(API_BASE_URL + '/stock-labels');
    };

    this.filterLabels = function(labels, filters) {
      return labels.filter(function(label) {
        if (filters.status && filters.status !== 'all' && label.status !== filters.status) {
          return false;
        }
        if (filters.warehouse && filters.warehouse !== 'all' && label.warehouse_code !== filters.warehouse) {
          return false;
        }
        if (filters.stdBundle !== undefined && filters.stdBundle !== 'all' && filters.stdBundle !== '') {
          var want = filters.stdBundle === 'true';
          if (label.is_standard_bundle !== want) return false;
        }
        if (filters.condition && filters.condition !== 'all' && label.order_condition !== filters.condition) {
          return false;
        }
        if (filters.exitDateFrom) {
          if (!label.exit_date || label.exit_date < filters.exitDateFrom) return false;
        }
        if (filters.exitDateTo) {
          if (!label.exit_date || label.exit_date > filters.exitDateTo) return false;
        }
        return true;
      });
    };

    var SEARCH_FIELDS = [
      'progressivo', 'item_code', 'description', 'customer',
      'country', 'order_number', 'embarque_id', 'nf', 'invoice',
    ];

    this.searchLabels = function(labels, query) {
      if (!query) return labels;
      var q = query.toLowerCase();
      return labels.filter(function(label) {
        return SEARCH_FIELDS.some(function(f) {
          return label[f] && label[f].toLowerCase().indexOf(q) !== -1;
        });
      });
    };

    this.aggregateByField = function(labels, field, valueField) {
      var map = {};
      labels.forEach(function(label) {
        var key = label[field] || 'Unknown';
        var value = parseFloat(label[valueField]) || 0;
        map[key] = (map[key] || 0) + value;
      });
      return Object.keys(map)
        .map(function(key) { return { key: key, value: map[key] }; })
        .sort(function(a, b) { return b.value - a.value; });
    };
  },
]);
