import angular from 'angular';
import '../../app.module';
import '../../services/loads.service';

angular.module('shippingManager').controller('LoadsController',
  ['LoadsService', function LoadsController(LoadsService) {
    var vm = this;

    var PAGE_SIZE = 25;

    vm.loads      = [];
    vm.filtered   = [];
    vm.page       = [];
    vm.loading    = true;
    vm.error      = null;
    vm.expanded   = {};
    vm.itemsCache = {};

    vm.currentPage = 1;
    vm.totalPages  = 0;

    vm.filters   = { status: 'all', destination: 'all' };
    vm.search    = '';
    vm.sortField = 'created_at';
    vm.sortAsc   = false;
    vm.destinations = [];

    vm.totalTons = 0;
    vm.byStatus  = [];
    vm.byDest    = [];

    vm.fmtNum  = function(n) { return new Intl.NumberFormat('en-US').format(n); };
    vm.fmtTons = function(n) { return vm.fmtNum((+n || 0).toFixed(1)) + ' t'; };

    LoadsService.getLoads().then(function(res) {
      vm.loads = res.data;
      vm.destinations = Array.from(new Set(vm.loads.map(function(l) { return l.destination; }).filter(Boolean))).sort();
      vm.applyFilters();
      vm.loading = false;
    }).catch(function() {
      vm.error = 'Failed to load loads.';
      vm.loading = false;
    });

    vm.applyFilters = function() {
      var result = LoadsService.filterLoads(vm.loads, vm.filters);
      result = LoadsService.searchLoads(result, vm.search);

      result = result.slice().sort(function(a, b) {
        var va = a[vm.sortField] || '';
        var vb = b[vm.sortField] || '';
        if (vm.sortField === 'total_weight_tons') {
          va = parseFloat(va) || 0; vb = parseFloat(vb) || 0;
        }
        if (va < vb) return vm.sortAsc ? -1 : 1;
        if (va > vb) return vm.sortAsc ?  1 : -1;
        return 0;
      });

      vm.filtered  = result;
      vm.totalTons = LoadsService.sumWeightTons(result);
      vm.byStatus  = _aggregate(result, 'status', 'total_weight_tons');
      vm.byDest    = _aggregate(result, 'destination', 'total_weight_tons');

      vm.currentPage = 1;
      vm._refreshPage();
    };

    vm._refreshPage = function() {
      var paged = LoadsService.paginateLoads(vm.filtered, vm.currentPage, PAGE_SIZE);
      vm.page       = paged.items;
      vm.totalPages = paged.totalPages;
      vm.currentPage = paged.currentPage;
    };

    vm.goToPage = function(p) {
      if (p < 1 || p > vm.totalPages) return;
      vm.currentPage = p;
      vm._refreshPage();
    };

    function _aggregate(list, field, valField) {
      var map = {};
      list.forEach(function(item) {
        var k = item[field] || 'Unknown';
        map[k] = (map[k] || 0) + (parseFloat(item[valField]) || 0);
      });
      return Object.keys(map).map(function(k) { return { key: k, value: map[k] }; })
        .sort(function(a, b) { return b.value - a.value; });
    }

    vm.setSort = function(field) {
      if (vm.sortField === field) { vm.sortAsc = !vm.sortAsc; } else { vm.sortField = field; vm.sortAsc = false; }
      vm.applyFilters();
    };

    vm.toggleExpand = function(load) {
      vm.expanded[load.id] = !vm.expanded[load.id];
      if (vm.expanded[load.id] && !vm.itemsCache[load.id]) {
        LoadsService.getLoadItems(load.id).then(function(res) {
          vm.itemsCache[load.id] = res.data;
        });
      }
    };

    vm.nextTransitionLabel = function(load) {
      var t = LoadsService.getAvailableTransition(load);
      return t ? t.replace(/_/g, ' ').toUpperCase() : null;
    };

    vm.applyTransition = function(load) {
      var next = LoadsService.getAvailableTransition(load);
      if (!next) return;
      if (next === 'dispatched' && !confirm('Mark load ' + load.id + ' as dispatched?')) return;
      LoadsService.updateStatus(load.id, next).then(function() {
        load.status = next;
        vm.applyFilters();
      });
    };

    vm.loadTotalPcs = function(loadId) {
      return (vm.itemsCache[loadId] || []).reduce(function(s, i) { return s + (i.piece_count || 0); }, 0);
    };

    vm.loadTotalTons = function(loadId) {
      return (vm.itemsCache[loadId] || []).reduce(function(s, i) { return s + (parseFloat(i.volume_tons) || 0); }, 0);
    };
  }],
);
