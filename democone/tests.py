# -*- coding: utf-8 -*-
from democone import *  # NOQA


@test
def test_html(app):
    resp = app.get('/')
    resp.mustcontain('It works!')

    resp = app.get('/about/')
    resp.mustcontain('It works!')


@test
def test_controller(app):
    resp = app.get('/contact/')
    form = resp.forms['contact']
    form.message = 'Yo!'
    form['email'] = 'gael@example.com'
    resp = form.submit().follow()


@test
def test_users(app):
    resp = app.get('/users/')
    assert len(resp.json['users']) == 1

    resp = app.get('/users/1/')
    assert resp.json['pk'] == 1, resp.json

    resp = app.post_json('/users/1/', dict(username='gawel'))
    assert resp.json['status'] == 'ok', resp.json
