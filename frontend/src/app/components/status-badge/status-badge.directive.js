import angular from 'angular';
import '../../app.module';

var LABEL_STATUS_MAP = {
  available_in_stock:       { label: 'IN STOCK',    color: 'var(--green)'      },
  reserved:                 { label: 'RESERVED',    color: 'var(--yellow)'     },
  in_load:                  { label: 'IN LOAD',     color: 'var(--blue)'       },
  in_transit_to_terminal:   { label: 'TO TERMINAL', color: 'var(--accent)'     },
  available_in_terminal:    { label: 'IN TERMINAL', color: 'var(--yellow)'     },
  in_transit_to_client:     { label: 'TO CLIENT',   color: 'var(--blue)',  pulse: true },
  delivered:                { label: 'DELIVERED',   color: 'var(--text-muted)' },
  idle:                     { label: 'IDLE',        color: 'var(--accent)'     },
  damaged:                  { label: 'DAMAGED',     color: 'var(--red)'        },
};

var LOAD_STATUS_MAP = {
  draft:      { label: 'DRAFT',      color: 'var(--text-dim)'  },
  pending:    { label: 'PENDING',    color: 'var(--text-muted)' },
  in_transit: { label: 'IN TRANSIT', color: 'var(--accent)', pulse: true },
  dispatched: { label: 'DISPATCHED', color: 'var(--blue)'    },
  delivered:  { label: 'DELIVERED',  color: 'var(--green)'   },
  cancelled:  { label: 'CANCELLED',  color: 'var(--red)'     },
};

function makeBadgeDirective(statusMap) {
  return function() {
    return {
      restrict: 'E',
      scope: { status: '@' },
      template:
        '<span class="status-badge" ng-class="{pulse: vm.pulse}" ng-style="{color: vm.color}">' +
        '  <span class="dot" ng-style="{background: vm.color, \'box-shadow\': \'0 0 5px \' + vm.color}"></span>' +
        '  {{vm.label}}' +
        '</span>',
      controllerAs: 'vm',
      bindToController: true,
      controller: function() {
        var vm = this;
        vm.$onChanges = function() {
          var entry = statusMap[vm.status] || { label: vm.status, color: 'var(--text-muted)' };
          vm.label = entry.label;
          vm.color = entry.color;
          vm.pulse = !!entry.pulse;
        };
        vm.$onChanges();
      },
    };
  };
}

angular.module('shippingManager')
  .directive('labelStatusBadge', makeBadgeDirective(LABEL_STATUS_MAP))
  .directive('loadStatusBadge',  makeBadgeDirective(LOAD_STATUS_MAP));
