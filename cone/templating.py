# -*- coding: utf-8 -*-
import pyramid_jinja2


def jinja2(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path(config.templates_path())
    config.add_renderer('.html', pyramid_jinja2.renderer_factory)
