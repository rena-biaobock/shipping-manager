import angular from 'angular';
import '../../app.module';
import '../../services/stock.service';
import '../../services/bin-packing.service';

angular.module('shippingManager').controller('LoadGenController',
  ['StockService', 'BinPackingService', function LoadGenController(StockService, BinPackingService) {
    var vm = this;

    vm.warehouses  = [];
    vm.customers   = [];
    vm.filters     = { warehouse: 'all', customer: 'all' };
    vm.maxTons     = 31;
    vm.capacities  = [27, 31, 38];

    vm.generated  = [];
    vm.confirmed  = {};
    vm.generating = false;
    vm.error      = null;

    vm.fmtNum  = function(n) { return new Intl.NumberFormat('en-US').format(n); };
    vm.fmtTons = function(n) { return vm.fmtNum((+n || 0).toFixed(1)) + ' t'; };

    StockService.getLabels().then(function(res) {
      var labels = res.data;
      vm.warehouses = Array.from(new Set(labels.map(function(l) { return l.warehouse_code; }).filter(Boolean))).sort();
      vm.customers  = Array.from(new Set(labels.map(function(l) { return l.customer; }).filter(Boolean))).sort();
    });

    vm.generate = function() {
      vm.generating = true;
      vm.error      = null;
      vm.generated  = [];
      vm.confirmed  = {};

      var apiFilters = {
        warehouse: vm.filters.warehouse !== 'all' ? vm.filters.warehouse : null,
        customer:  vm.filters.customer  !== 'all' ? vm.filters.customer  : null,
      };

      BinPackingService.generate(apiFilters, vm.maxTons, 1000)
        .then(function(res) {
          vm.generated = res.data.map(function(bin) {
            return { _id: bin._id, destination: '', items: bin.items,
              totalTons: bin.totalTons, totalPcs: bin.totalPcs, partial: bin.partial };
          });
          vm.generating = false;
        })
        .catch(function() {
          vm.error = 'Failed to generate load plan.';
          vm.generating = false;
        });
    };

    vm.canConfirm = function(plan) {
      return BinPackingService.canConfirmLoad(plan);
    };

    vm.confirm = function(plan) {
      if (!vm.canConfirm(plan)) return;
      BinPackingService.createLoad(vm.maxTons, plan.destination, plan.items)
        .then(function() {
          vm.confirmed[plan._id] = true;
        })
        .catch(function() {
          vm.error = 'Failed to confirm load.';
        });
    };
  }],
);
