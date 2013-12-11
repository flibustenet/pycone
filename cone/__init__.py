# -*- coding: utf-8 -*-
from pyramid import httpexceptions as exc
from .application import Cone
import types
import sys

__all__ = [
    'exc',
    'Cone', 'run', 'default_app', 'test', 'test_app', 'wsgi_app',
    'resource', 'controller', 'view_attr',
    'route', 'get', 'post', 'delete', 'put',
    'predicates', 'renderer', 'json',
]


class ModuleWrapper(types.ModuleType):
    """wrap cone and add extra attributes from default app"""

    def __init__(self, mod, name):
        self.__name__ = name
        self.__module__ = name
        for attr in ["__builtins__", "__doc__",
                     "__package__", "__file__"]:
            setattr(self, attr, getattr(mod, attr, None))
        self.__path__ = getattr(mod, '__path__', [])
        self.__test__ = getattr(mod, '__test__', {})
        self.mod = mod
        self.default_app = None

    def __getattr__(self, attr):
        if attr == '__all__':
            if self.__name__ == 'cone':
                return [str(c) for c in __all__]
            else:  # pragma: no cover
                raise ImportError('You cant import things that does not exist')
        if hasattr(self.mod, attr):
            return getattr(self.mod, attr)
        else:
            if self.default_app is None:
                module_name = sys._getframe(1).f_globals['__name__']
                if 'nose' in module_name:
                    raise AttributeError(attr)
                settings = {'cone.__module__': module_name}
                self.default_app = Cone(settings)
            return getattr(self.default_app, attr)

    __getitem__ = __getattr__

sys.modules['cone'] = ModuleWrapper(sys.modules[__name__], __name__)
