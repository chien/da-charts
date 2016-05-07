(function(){
  'use strict';
  function StockPriceAndEarningCtrl(JsonFileUrl) {
    var vm = this;

    function successCallBack(data) {
      vm.data = data;
    }

    function getData() {
      JsonFileUrl.query(successCallBack);
    }

    function activateExposedProperties() {
      getData();
    }

    function activateExposedFunctions() {
    }

    // The core init method so a dev can easily see what is going on
    function activate() {
      activateExposedProperties();
      activateExposedFunctions();
    }

    // finally initialise the controller
    activate();
  }

  StockPriceAndEarningCtrl.$inject = [ "JsonFileUrl" ];
  angular.module('DAChart').controller('StockPriceAndEarningCtrl',StockPriceAndEarningCtrl);

  angular.module('DAChart.stock_price_and_earning', ['ngRoute'])
  .config(['$routeProvider', function($routeProvider) {
    $routeProvider.when('/stock_price_and_earning', {
      templateUrl: 'stock_price_and_earning/stock_price_and_earning.html',
      controller: 'StockPriceAndEarningCtrl'
    });
  }])

})();
