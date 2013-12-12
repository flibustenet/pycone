# -*- coding: utf-8 -*-
from cone import *  # NOQA


@route('/')
def index(request):
    return dict()


@route
@renderer('templates/index.html')
def about(request):
    return dict(x='y')


@get('/hello/{name}/')
@json
def hello(request):
    print(request.matchdict)
    return dict(name=request.matchdict)


@resource
class Users(object):

    def __init__(self, request):
        self.request = request

    def get_collection(self):
        return dict(users=[dict(pk=1, username='gawel')])

    def get(self, pk):
        return dict(pk=int(pk), username='gawel')

    def post(self, pk, data=None):
        return dict(status='ok', data=data)


@controller
class Contact(object):

    def __init__(self, request):
        self.request = request

    @view_attr
    def contact(self):
        return {}

    @contact.post
    def post_contact(self, data=None, **kw):
        if data['email']:
            return exc.HTTPFound(location=self.request.route_url('index'))
        return {}


def main():
    run()

if __name__ == '__main__':
    main()
