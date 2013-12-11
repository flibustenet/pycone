# -*- coding: utf-8 -*-
import sys
import os


def application_directory(config):
    module_name = config.registry.settings['cone.__module__']
    return os.path.dirname(sys.modules[module_name].__file__)


def templates_path(config):
    module_name = config.registry.settings['cone.__module__']
    return module_name + ':templates'


def includeme(config):
    settings = config.registry.settings
    if settings.get('debug'):
        settings['debug_templates'] = True
        settings['reload_templates'] = True
    config.add_directive('application_directory', application_directory)
    config.add_directive('templates_path', templates_path)
