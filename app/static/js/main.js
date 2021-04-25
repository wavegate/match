(function () {
  'use strict';

  angular.module('Match0912App', [])

  .controller('Match0912Controller', ['$scope', '$log', '$http',
    function($scope, $log, $http) {
      $scope.getResults = function() {
        $log.log("test");

        var userInput = $scope.url;

        $http.post('/start', {"url": userInput}).
        	success(function(results) {
        		$log.log(results);
        	}).
        	error(function(error) {
        		$log.log(error);
        	});
      };
    }
  ]);

}());