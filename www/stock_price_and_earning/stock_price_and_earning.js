(function(){
  'use strict';
  function StockPriceAndEarningCtrl(JsonFileUrl) {
    var vm = this;

    function successCallBack(data) {
      vm.data = data;
      vm.d3Data = [];
      var groupedData = {};

      angular.forEach(vm.data, function(element, key) {
        var d3Datum = {
          x: element.stock_purchased_at,
          y: element.stock_sold_at,
          size: element.price_change_perc * 10,
          shape: 'circle'
        };

        if (element.industry in groupedData) {
          groupedData[element.industry].push(d3Datum);
        } else {
          groupedData[element.industry] = [d3Datum];
        }
      });

      angular.forEach(groupedData, function(elementList, industryName) {
        vm.d3Data.push({
          key: industryName,
          values: groupedData[industryName]
        });
      });
    }

    function getData() {
      JsonFileUrl.query(successCallBack);
    }

    function setD3ChartOptions() {
      vm.options = {
        chart: {
          type: 'scatterChart',
          height: 450,
          color: d3.scale.category10().range(),
          scatter: {
            onlyCircles: false
          },
          showDistX: true,
          showDistY: true,
          duration: 350,
          xAxis: {
            axisLabel: 'Stock Purchased At (Earning Release Date - N)',
            tickFormat: function(d){
              return d3.format('2d')(d);
            }
          },
          yAxis: {
            axisLabel: 'Stock Sold At (Earning Release Date + N)',
            tickFormat: function(d){
              return d3.format('2d')(d);
            },
            axisLabelDistance: -5
          },
          zoom: {
            //NOTE: All attributes below are optional
            enabled: true,
            scaleExtent: [1, 10],
            useFixedDomain: false,
            useNiceScale: false,
            horizontalOff: false,
            verticalOff: false,
            unzoomEventType: 'dblclick.zoom'
          }
        }
      };
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
      setD3ChartOptions();
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
