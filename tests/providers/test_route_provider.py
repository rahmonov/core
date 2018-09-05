from masonite.app import App
from masonite.routes import Route, Get
from masonite.request import Request
from masonite.providers.RouteProvider import RouteProvider
from masonite.view import View
from masonite.helpers.routes import get, compile_routes_to_dictionary
from masonite.testsuite.TestSuite import generate_wsgi
from app.http.controllers.ControllerTest import ControllerTest
from config import middleware, application


class TestRouteProvider:

    def setup_method(self):
        self.app = App()
        self.app.bind('Container', self.app)
        self.app.bind('Environ', generate_wsgi())
        self.app.bind('Application', application)
        self.app.bind('CompiledRoutes', [])
        self.app.bind('Route', Route(self.app.make('Environ')))
        self.app.bind('Request', Request(self.app.make('Environ')).load_app(self.app))
        self.app.bind('Headers', [])
        self.app.bind('HttpMiddleware', middleware.HTTP_MIDDLEWARE)
        view = View(self.app)
        self.app.bind('View', view.render)
        self.provider = RouteProvider()
        self.provider.app = self.app

     
    def test_controller_that_returns_a_view(self):
        self.app.make('Route').url = '/view'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/view', ControllerTest.test)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Response') == 'test'

    def test_controller_does_not_return_with_non_matching_end_slash(self):
        self.app.make('Route').url = '/view'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/view/', ControllerTest.returns_a_view)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Response') == 'Route not found. Error 404'


    def test_provider_runs_through_routes(self):
        self.app.make('Route').url = '/test'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/test', ControllerTest.show)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').header('Content-Type') == 'text/html; charset=utf-8'


    def test_sets_request_params(self):
        self.app.make('Route').url = '/test/1'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([
            get('/test/@id', ControllerTest.show),
            get('/test/id/1', ControllerTest.show),
            get('/test/id/2', ControllerTest.show),
            get('/test/id/5', ControllerTest.show),
            get('/test/id/6', ControllerTest.show),
            get('/test', ControllerTest.show),
            ])
        )

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').param('id') == '1'
    
    def test_url_with_dots_finds_route(self):
        self.app.make('Route').url = '/test/user.endpoint'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/test/@endpoint', ControllerTest.show)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').param('endpoint') == 'user.endpoint'
    
    def test_url_with_dashes_finds_route(self):
        self.app.make('Route').url = '/test/user-endpoint'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/test/@endpoint', ControllerTest.show)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').param('endpoint') == 'user-endpoint'
    
    def test_route_subdomain_ignores_routes(self):
        self.app.make('Route').url = '/test'
        self.app.make('Environ')['HTTP_HOST'] = 'subb.domain.com'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/test', ControllerTest.show)]))

        request = self.app.make('Request')
        request.activate_subdomains()

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Response') == 'Route not found. Error 404'
    
    def test_controller_returns_json_response_for_dict(self):
        self.app.make('Route').url = '/view'
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([get('/view', ControllerTest.returns_a_dict)]))

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Response') == '{"id": 1}'
        assert self.app.make('Request').header('Content-Type') == 'application/json; charset=utf-8'

    def test_route_runs_str_middleware(self):
        self.app.make('Route').url = '/view'
        self.app.bind('RouteMiddleware', middleware.ROUTE_MIDDLEWARE)
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([
            get('/view', ControllerTest.returns_a_dict).middleware('test')
            ])
        )

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').path == 'test/middleware/before/ran'

    def test_route_runs_middleware_with_list(self):
        self.app.make('Route').url = '/view'
        self.app.bind('RouteMiddleware', middleware.ROUTE_MIDDLEWARE)
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([
            get('/view', ControllerTest.returns_a_dict).middleware('middleware.test')
            ])
        )

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').path == 'test/middleware/before/ran'
        assert self.app.make('Request').attribute == True

    def test_route_compiling_to_regex(self):
        self.app.make('Route').url = '/view/'
        self.app.bind('RouteMiddleware', middleware.ROUTE_MIDDLEWARE)
        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([
            get('/view/', ControllerTest.returns_a_dict).middleware('middleware.test')
        ])
        )

        self.provider.boot(
            self.app.make('Route'),
            self.app.make('Request')
        )

        assert self.app.make('Request').path == 'test/middleware/before/ran'
        assert self.app.make('Request').attribute == True

class Middleware:

    def before(): pass

    def after(): pass
