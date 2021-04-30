(function () {
  'use strict';

  angular.module('MyApp', [])

  .controller('MyAppController', ['$scope', '$log', '$http',
    function($scope, $log, $http) {
      $scope.getResults = function() {
        $log.log("test");
      };
    }
  ]);

}());