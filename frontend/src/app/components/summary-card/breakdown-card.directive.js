import angular from 'angular';
import '../../app.module';

angular.module('shippingManager').directive('breakdownCard', function() {
  return {
    restrict: 'E',
    scope: { label: '@', rows: '<', accent: '@' },
    template:
      '<div class="breakdown-card" ng-style="{\'border-top-color\': vm.accentColor}">' +
      '  <div class="card-label">{{vm.label}}</div>' +
      '  <div class="breakdown-rows">' +
      '    <div class="breakdown-row" ng-repeat="row in vm.rows">' +
      '      <div class="breakdown-key" title="{{row.key}}">{{row.key}}</div>' +
      '      <div class="breakdown-bar-wrap">' +
      '        <div class="breakdown-bar"' +
      '             ng-style="{width: vm.pct(row) + \'%\', background: vm.accentColor}"></div>' +
      '      </div>' +
      '      <div class="breakdown-val">{{row.value | number:1}} t</div>' +
      '    </div>' +
      '  </div>' +
      '</div>',
    controllerAs: 'vm',
    bindToController: true,
    controller: function() {
      var vm = this;
      vm.$onChanges = function() {
        vm.accentColor = vm.accent || 'var(--blue)';
        vm.maxVal = vm.rows && vm.rows.length
          ? Math.max.apply(null, vm.rows.map(function(r) { return r.value; }))
          : 1;
      };
      vm.$onChanges();
      vm.pct = function(row) {
        var max = vm.maxVal || 1;
        return (row.value / max) * 100;
      };
    },
  };
});
