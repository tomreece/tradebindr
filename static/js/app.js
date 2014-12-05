angular.module('tradebindr', ['ngRoute', 'tradebindrControllers', 'tradebindrDirectives', 'tradebindrFilters'])

  .config(['$routeProvider',
    function($routeProvider) {
      $routeProvider
        .when('/', {
          templateUrl: '/static/partials/login.html',
          controller: 'loginController'
        })
        .when('/main', {
          templateUrl: '/static/partials/main.html',
          controller: 'mainController'
        })
        .otherwise({ redirectTo: '/' });
    }])

  .factory('authHttpResponseInterceptor', ['$q', '$location', function($q, $location) {
    return {
      response: function(response) {
        return response || $q.when(response);
      },
      responseError: function(rejection) {
        if (rejection.status === 401) {
          //console.log("Response Error 401",rejection);
          window.location = "/";
        }
        return $q.reject(rejection);
      }
    }
  }])

  .config(['$httpProvider',function($httpProvider) {
    //Http Intercpetor to check auth failures for xhr requests
    $httpProvider.interceptors.push('authHttpResponseInterceptor');
    // Initialize $httpProvider.defaults.headers.get if it's not there
    if (!$httpProvider.defaults.headers.get) {
        $httpProvider.defaults.headers.get = {};
    }
    // Set some default request headers to avoid IE caching of Ajax requests
  //  $httpProvider.defaults.headers.get['If-Modified-Since'] = '0';
  //  $httpProvider.defaults.headers.get['Cache-Control'] = 'no-cache';
  //  $httpProvider.defaults.headers.get['Pragma'] = 'no-cache';
  }]);
