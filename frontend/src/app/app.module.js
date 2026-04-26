import angular from 'angular';
import ngRoute from 'angular-route';

angular.module('shippingManager', ['ngRoute'])
  .constant('API_BASE_URL', process.env.API_BASE_URL)
  .config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
      $locationProvider.hashPrefix('');
      $routeProvider
        .when('/stock', {
          template: require('./pages/stock/stock.html'),
          controller: 'StockController',
          controllerAs: 'vm',
        })
        .when('/loads', {
          template: require('./pages/loads/loads.html'),
          controller: 'LoadsController',
          controllerAs: 'vm',
        })
        .when('/load-generation', {
          template: require('./pages/load-generation/load-generation.html'),
          controller: 'LoadGenController',
          controllerAs: 'vm',
        })
        .otherwise({ redirectTo: '/stock' });
    },
  ]);
