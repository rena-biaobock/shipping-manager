import angular from 'angular';
import '../../app.module';

angular.module('shippingManager').directive('capacityBar', function() {
  return {
    restrict: 'E',
    scope: { used: '<', total: '<' },
    template:
      '<div class="capacity-bar">' +
      '  <div class="bar-track">' +
      '    <div class="bar-fill" ng-style="{width: vm.pct + \'%\', background: vm.color}"></div>' +
      '  </div>' +
      '  <span class="bar-pct">{{vm.pct | number:3}}%</span>' +
      '</div>',
    controllerAs: 'vm',
    bindToController: true,
    controller: function() {
      var vm = this;
      vm.$onChanges = function() {
        var total = vm.total || 0;
        var used  = vm.used  || 0;
        vm.pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
        vm.color = vm.pct > 90 ? 'var(--red)' : vm.pct > 70 ? 'var(--yellow)' : 'var(--green)';
      };
      vm.$onChanges();
    },
  };
});
