# -*- coding: utf-8 -*-
from pyramid.scripts import pserve
import optparse
import logging
import os


class Cmd(pserve.PServeCommand):

    parser = optparse.OptionParser()
    parser.add_option(
        '--bind',
        dest='bind',
        metavar='ADDRESS',
        default='127.0.0.1:5000',
        help="ip:port or ip")

    parser.add_option(
        '--no-reload',
        dest='no_reload',
        action='store_true',
        help="Do not use auto-restart file monitor")

    def __init__(self, app):
        self.app = app
        self.options, self.args = self.parser.parse_args()
        self.quiet = 0
        self.verbose = 1

    def run(self):
        if not self.options.no_reload:
            if os.environ.get(self._reloader_environ_key):
                if self.verbose > 1:
                    self.out('Running reloading file monitor')
                pserve.install_reloader(1, [])
            else:
                return self.restart_with_reloader()

        def serve():
            from waitress.server import create_server
            try:
                host, port = self.options.bind.split(':')
                server = create_server(self.app.wsgi_app,
                                       host=host, port=int(port))
                self.out((
                    'Serving on http://{0.host}:{0.port}/...'
                ).format(server.adj))
                server.run()
            except (SystemExit, KeyboardInterrupt):
                self.out('Exiting')

        logging.basicConfig(level=logging.DEBUG)
        serve()
