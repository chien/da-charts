(function(){
  'use strict';

  function JsonFileUrl($resource) {
    return $resource('https://dl.dropboxusercontent.com/u/18823852/gamma/kyper-1-test-data.json', null, {
      query: {
        method: 'GET',
        isArray: true,
      }
    });
  }

  JsonFileUrl.$inject = ["$resource"];
  angular.module("DAChart").factory("JsonFileUrl", JsonFileUrl);

})();

