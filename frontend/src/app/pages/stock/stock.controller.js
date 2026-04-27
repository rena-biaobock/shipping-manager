import angular from 'angular';
import '../../app.module';
import '../../services/stock.service';

angular.module('shippingManager').controller('StockController',
  ['StockService', function StockController(StockService) {
    var vm = this;

    var PAGE_SIZE = 25;

    vm.labels   = [];
    vm.filtered = [];
    vm.page     = [];
    vm.loading  = true;
    vm.error    = null;

    vm.currentPage = 1;
    vm.totalPages  = 0;
    vm.totalItems  = 0;

    vm.filters = { status: 'all', warehouse: 'all', stdBundle: 'all', condition: 'all', exitDateFrom: '', exitDateTo: '' };
    vm.search  = '';

    vm.warehouses  = [];
    vm.totalTons   = 0;
    vm.totalPcs    = 0;
    vm.byCountry   = [];
    vm.byClient    = [];
    vm.byStatus    = [];

    vm.fmtNum  = function(n) { return new Intl.NumberFormat('en-US').format(n); };
    vm.fmtTons = function(n) { return vm.fmtNum((+n || 0).toFixed(1)) + ' t'; };

    StockService.getLabels().then(function(res) {
      vm.labels = res.data;
      vm.warehouses = Array.from(new Set(vm.labels.map(function(l) { return l.warehouse_code; }).filter(Boolean))).sort();
      vm.applyFilters();
      vm.loading = false;
    }).catch(function() {
      vm.error = 'Failed to load stock labels.';
      vm.loading = false;
    });

    vm.applyFilters = function() {
      var result = StockService.filterLabels(vm.labels, vm.filters);
      result = StockService.searchLabels(result, vm.search);
      vm.filtered = result;

      vm.totalTons = result.reduce(function(s, l) { return s + (parseFloat(l.volume_tons) || 0); }, 0);
      vm.totalPcs  = result.reduce(function(s, l) { return s + (l.piece_count || 0); }, 0);
      vm.byCountry = StockService.aggregateByField(result, 'country', 'volume_tons');
      vm.byClient  = StockService.aggregateByField(result, 'customer', 'volume_tons');
      vm.byStatus  = StockService.aggregateByField(result, 'status', 'volume_tons');

      vm.currentPage = 1;
      vm._refreshPage();
    };

    vm._refreshPage = function() {
      var paged = StockService.paginateLabels(vm.filtered, vm.currentPage, PAGE_SIZE);
      vm.page       = paged.items;
      vm.totalPages = paged.totalPages;
      vm.totalItems = paged.totalItems;
      vm.currentPage = paged.currentPage;
    };

    vm.goToPage = function(p) {
      if (p < 1 || p > vm.totalPages) return;
      vm.currentPage = p;
      vm._refreshPage();
    };
  }],
);
