(function(){
  'use strict';

  // Declare app level module which depends on views, and components
  angular.module('DAChart', [
    'ngRoute',
    'ngResource',
    'ngCookies',
    'base64',
    'DAChart.stock_price_and_earning',
    'DAChart.version'
  ]).
  config(['$routeProvider', function($routeProvider) {
    $routeProvider.otherwise({redirectTo: '/stock_price_and_earning'});
  }]);

})();
