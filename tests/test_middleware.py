from masonite.app import App
from masonite.request import Request
from masonite.view import View
from masonite.routes import Get, Route
from masonite.helpers.routes import compile_routes_to_dictionary
from masonite.testsuite import generate_wsgi
from masonite.auth import Csrf
from masonite.providers import RouteProvider
from app.http.middleware.TestMiddleware import TestMiddleware as MiddlewareTest
from app.http.middleware.TestHttpMiddleware import TestHttpMiddleware as MiddlewareHttpTest
from config import application

class TestMiddleware:

    def setup_method(self):
        self.app = App()
        self.app.bind('Environ', generate_wsgi())
        self.app.bind('Application', application)
        self.app.make('Environ')
        self.app.bind('Headers', [])
        self.app.bind('Request', Request(self.app.make('Environ')).load_app(self.app))
        self.app.bind('Csrf', Csrf(self.app.make('Request')))
        self.app.bind('Route', Route(self.app.make('Environ')))

        self.app.bind('ViewClass', View(self.app))

        self.app.bind('CompiledRoutes', compile_routes_to_dictionary([
            Get().route('/', 'TestController@show').middleware('test')
        ]))

        self.app.bind('HttpMiddleware', [
            MiddlewareHttpTest
        ])
        self.app.bind('RouteMiddleware', {
            'test': MiddlewareTest
        })

        self.provider = RouteProvider()
        self.provider.app = self.app
    
    def test_route_middleware_runs(self):
        self.app.resolve(self.provider.boot)
        assert self.app.make('Request').path == '/test/middleware'

    def test_http_middleware_runs(self):
        self.app.resolve(self.provider.boot)
        assert self.app.make('Request').path == '/test/middleware'
        assert self.app.make('Request').environ['HTTP_TEST'] == 'test'


