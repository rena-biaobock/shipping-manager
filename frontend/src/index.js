import angular from 'angular';
import 'angular-route';
import './styles/main.css';

import './app/app.module';
import './app/services/stock.service';
import './app/services/loads.service';
import './app/services/bin-packing.service';
import './app/components/sidebar/sidebar.directive';
import './app/components/summary-card/total-card.directive';
import './app/components/summary-card/breakdown-card.directive';
import './app/components/capacity-bar/capacity-bar.directive';
import './app/components/status-badge/status-badge.directive';
import './app/pages/stock/stock.controller';
import './app/pages/loads/loads.controller';
import './app/pages/load-generation/load-generation.controller';

angular.element(document).ready(function() {
  angular.bootstrap(document, ['shippingManager']);
});
