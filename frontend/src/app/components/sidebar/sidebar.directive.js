import angular from 'angular';
import '../../app.module';

angular.module('shippingManager').directive('appSidebar', ['$location', function($location) {
  return {
    restrict: 'E',
    template: `
      <div class="sidebar" ng-class="{collapsed: vm.collapsed}">
        <div class="sidebar-header">
          <div class="sidebar-logo">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2.5">
              <path d="M1 3h15v13H1z"/><path d="M16 8h4l3 3v5h-7V8z"/>
              <circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>
            </svg>
          </div>
          <div class="sidebar-title">
            <div class="name">ShipManager</div>
            <div class="version">v2.0.0</div>
          </div>
          <button class="sidebar-toggle" ng-click="vm.collapsed = !vm.collapsed" title="Toggle sidebar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6"  x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
        </div>
        <nav>
          <div class="nav-section-label">NAVIGATION</div>
          <a ng-repeat="item in vm.nav"
             class="nav-item"
             ng-class="{active: vm.isActive(item.path)}"
             ng-href="#{{item.path}}">
            <span class="nav-icon" ng-bind-html="item.icon"></span>
            <span class="nav-label">{{item.label}}</span>
          </a>
        </nav>
        <div class="sidebar-footer">
          <div class="footer-label">LAST SYNC</div>
          <div class="footer-value">{{vm.syncTime}}</div>
        </div>
      </div>
    `,
    controllerAs: 'vm',
    controller: ['$sce', function($sce) {
      var vm = this;
      vm.collapsed = false;
      vm.syncTime = new Date().toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });

      vm.nav = [
        {
          path: '/stock', label: 'Stock',
          icon: $sce.trustAsHtml(
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<rect x="2" y="3" width="20" height="14" rx="1"/><path d="M8 21h8M12 17v4"/></svg>'
          ),
        },
        {
          path: '/loads', label: 'Loads',
          icon: $sce.trustAsHtml(
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<path d="M1 3h15v13H1z"/><path d="M16 8h4l3 3v5h-7V8z"/>' +
            '<circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
          ),
        },
        {
          path: '/load-generation', label: 'Load Generation',
          icon: $sce.trustAsHtml(
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>'
          ),
        },
      ];

      vm.isActive = function(path) {
        return $location.path() === path;
      };
    }],
  };
}]);
