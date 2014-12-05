angular.module('tradebindrControllers', [])

.controller('appController', function($rootScope, $scope, $http) {

})

.controller('loginController', function($rootScope, $scope, $http, $location) {
    $scope.login = function() {
        //alert($scope.user.name + ' ' + $scope.user.password);
        $http.post(
            '/login',
            { name : $scope.user.name, password: $scope.user.password }
        ).success(function(data) {
            $location.path('/main');
        });
    }
})

.controller('mainController', function($rootScope, $scope, $http, $location, $window) {
    $scope.cards = null;

    var fetchUsersCards = function() {
        $http.get(
            '/user'
        ).success(function(data) {
            $scope.cards = data.cards;
        });
    }

    fetchUsersCards();

    $scope.deleteCard = function(idx) {
        cardToDelete = $scope.cards[idx];
        $http.delete(
            '/card/' + cardToDelete.id
        ).success(function(data) {
            $scope.cards.splice(idx, 1);
        });
    }

    $scope.addCard = function() {
        var cardName = $window.prompt('Card name?', '');
        $http.post(
            '/card',
            { name: cardName }
        ).success(function(data) {
            fetchUsersCards();
        });
    }
});
