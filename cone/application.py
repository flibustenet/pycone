# -*- coding: utf-8 -*-
from pyramid.config import Configurator
from pyramid import httpexceptions as exc
from . import directives
from functools import wraps
from functools import partial
import logging
import types
import sys

try:
    from webtest import TestApp
except ImportError:
    pass


def update_request(request):
    if request.content_type == 'application/json' and \
       request.content_length:
        request.matchdict['data'] = request.json
    elif request.method == 'POST':
        request.matchdict['data'] = request.POST


def method_wrapper(func):
    @wraps(func)
    def wrapper(self):
        update_request(self.request)
        return func(self, **self.request.matchdict)
    return wrapper


def func_wrapper(func):
    @wraps(func)
    def wrapper(request):
        update_request(request)
        return func(request, **request.matchdict)
    return wrapper


class Cone(object):

    def __init__(self, settings, config=None):
        self.includes = settings.pop('includes', ['cone.templating.jinja2'])

        if 'cone.__module__' in settings:
            module_name = settings.get('cone.__module__')
        else:
            module_name = sys._getframe(1).f_globals['__name__']
            settings['cone.__module__'] = module_name

        if not config:
            config = Configurator(settings=settings)
        self.config = config = config.with_package(module_name)
        config.include(directives)

        self.log = settings.pop('logger', logging.getLogger(module_name))
        self.include = config.include
        self.routes = set()

    def exception(self, status_int):
        def exception(request):
            raise exc.status_map[status_int]()
        return exception

    def add_route(self, name, path):
        if name in self.routes:
            return
        self.routes.add(name)
        self.log.debug('add_route {0} {1}'.format(name, path))
        self.config.add_route(name, path)

    def add_view(self, *args, **kwargs):
        if 'renderer' not in kwargs:
            kwargs['renderer'] = 'templates/%(route_name)s.html' % kwargs
        if kwargs.get('renderer') == 'json':
            kwargs.setdefault('accept', 'application/json')
        self.log.debug('add_view {0} {1}'.format(args, kwargs))
        self.config.add_view(*args, **kwargs)

    def register_resource(self, kwargs, klass):
        route_name = kwargs.setdefault('route_name',
                                       klass.__name__.lower())
        kwargs.update(getattr(klass, '_predicates', {}))
        prefix = kwargs.pop('prefix', '/' + route_name)
        kwargs.setdefault('renderer', 'json')

        def includeme(config):
            config.add_route(route_name, '/{pk}/')
            config.add_route(route_name + '_collection', '/')
        self.config.include(includeme, route_prefix=prefix.rstrip('/'))

        for attr in ('get', 'post', 'put', 'delete', 'options', 'patch'):
            meth = getattr(klass, attr, None)
            if meth is not None:
                kw = kwargs.copy()
                kw.update(getattr(meth, '_predicates', {}))
                setattr(klass, attr, method_wrapper(meth))
                kw['request_method'] = attr.upper()
                kw["route_name"] = route_name
                self.add_view(klass, attr=attr, **kw)
            mattr = attr + '_collection'
            meth = getattr(klass, mattr, None)
            if meth is not None:
                kw = kwargs.copy()
                kw.update(getattr(meth, '_predicates', {}))
                kw['request_method'] = attr.upper()
                kw["route_name"] = route_name + '_collection'
                self.add_view(klass, attr=mattr, **kw)

        # fallback: HTTPMethodNotAllowed
        self.config.add_view(self.exception(405),
                             route_name=route_name)
        self.config.add_view(self.exception(405),
                             route_name=route_name + '_collection')

        return klass

    def resource(self, *args, **kwargs):
        if args:
            return self.register_resource({}, args[0])
        return partial(self.register_resource, kwargs)

    def register_class(self, kwargs, klass):
        kwargs.update(getattr(klass, '_predicates', {}))

        attrs = [a for a in dir(klass)
                 if isinstance(getattr(klass, a), types.MethodType)]
        attrs = [a for a in attrs if a[0] != '_']
        for attr in attrs:
            meth = getattr(klass, attr, None)
            if meth is not None:
                kw = kwargs.copy()
                kw.update(getattr(meth, '_predicates', {}))
                setattr(klass, attr, method_wrapper(meth))
                kw.setdefault("route_name", attr)
                self.add_route(kw['route_name'],
                               '/' + attr + '/')
                self.add_view(klass, attr=attr, **kw)

        return klass

    def controller(self, *args, **kwargs):
        if args:
            return self.register_class({}, args[0])
        return partial(self.register_class, kwargs)

    def register_func(self, request_method, args, kwargs):
        def register_func(request_method, args, kwargs, func):
            if request_method:
                kwargs['request_method'] = request_method
            route_name = kwargs.setdefault('route_name',
                                           func.__name__.lower())
            if len(args):
                path = args.pop(0)
            else:
                path = '/' + route_name + '/'
            route_name = func.__name__
            kwargs.update(getattr(func, '_predicates', {}))
            self.add_route(route_name, path)
            kwargs['route_name'] = route_name
            self.add_view(func_wrapper(func), **kwargs)
            return func
        if args and isinstance(args[0], types.FunctionType):
            args = list(args)
            func = args.pop(0)
            return register_func(request_method, args, kwargs, func)
        else:
            return partial(register_func, request_method, list(args), kwargs)

    def route(self, *args, **kwargs):
        return self.register_func(None, args, kwargs)

    def get(self, *args, **kwargs):
        return self.register_func('GET', args, kwargs)

    def post(self, *args, **kwargs):
        return self.register_func('POST', args, kwargs)

    def put(self, *args, **kwargs):
        return self.register_func('PUT', args, kwargs)

    def delete(self, *args, **kwargs):
        return self.register_func('DELETE', args, kwargs)

    def predicates(self, **kwargs):

        def request_method(func, method, other):
            setattr(other, '_predicates', dict(
                func._predicates,
                request_method=method.upper()))
            other._predicates.setdefault('route_name', func.__name__)
            return other

        def wrapper(obj):
            kw = getattr(obj, '_predicates', {})
            kw.update(kwargs)
            if not hasattr(obj, '_predicates'):
                setattr(obj, '_predicates', kw)
            if isinstance(obj, types.FunctionType):
                for attr in ('post', 'put', 'delete'):
                    setattr(obj, attr, partial(request_method, obj, attr))
            return obj

        return wrapper

    def view_attr(self, *args, **kwargs):
        if args:
            kwargs['request_method'] = 'GET'
            return self.predicates(**kwargs)(*args)
        else:
            return self.predicates(**kwargs)

    def json(self, obj):
        return self.predicates(renderer='json', accept='application/json')(obj)

    def renderer(self, renderer=None):
        if renderer:
            return self.predicates(renderer=renderer)
        else:
            return self.predicates()

    @property
    def wsgi_app(self):
        for include in self.includes:
            self.include(include)
        return self.config.make_wsgi_app()

    @property
    def test_app(self):
        return TestApp(self.wsgi_app)

    def test(self, func):
        @wraps(func)
        def wrapper():
            return func(self.test_app)
        return wrapper

    def run(self):
        from .scripts import Cmd
        cmd = Cmd(self)
        cmd.run()
