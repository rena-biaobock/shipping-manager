import angular from 'angular';
import '../../app.module';

angular.module('shippingManager').directive('totalCard', function() {
  return {
    restrict: 'E',
    scope: { label: '@', value: '@', sub: '@', accent: '@' },
    template:
      '<div class="total-card" ng-style="{\'border-top-color\': vm.accentColor}">' +
      '  <div class="card-bg" ng-style="{background: vm.accentColor}"></div>' +
      '  <div class="card-label">{{vm.label}}</div>' +
      '  <div class="card-value">{{vm.value}}</div>' +
      '  <div class="card-sub" ng-if="vm.sub">{{vm.sub}}</div>' +
      '</div>',
    controllerAs: 'vm',
    bindToController: true,
    controller: function() {
      var vm = this;
      vm.$onChanges = function() {
        vm.accentColor = vm.accent || 'var(--accent)';
      };
      vm.$onChanges();
    },
  };
});
