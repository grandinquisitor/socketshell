#!/usr/bin/env python

"""
ShellServer (or SocketShell?)

Live, multi-user threaded remote python shell.

Interact with live python code as it is running, or fight with other users and try to crash each other's threads.

Usage:

>>> s = ShellServer('localhost', 6666)
>>> print s.server_address
>>> s.serve_forever()


$ telnet localhost 6666
Python 2.5.1 (r251:54863, Jun 17 2009, 20:37:34) 
[GCC 4.0.1 (Apple Inc. build 5465)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
(MyConsole)
>>>

AsyncShellServer runs in its own thread. ShellServer runs in the current thread.

see console.py for a command-line toy server.
"""

__version__ = 'DEV'

import sys
import threading
import SocketServer
import code

class _MyConsole(code.InteractiveConsole):
    def __init__(self, rfile, wfile, filename="<console>"):
        code.InteractiveConsole.__init__(self, None, filename)
        self.rfile = rfile
        self.wfile = wfile

    def write(self, data):
        self.wfile.write(data)
        self.wfile.flush()

    def raw_input(self, prompt=""):
        self.write(prompt)
        self.wfile.flush()
        input = self.rfile.next().rstrip("\n\r")
        return input

    # not sure if I even need this
    @staticmethod
    def _softspace(file, newvalue):
        oldvalue = 0
        try:
            oldvalue = file.softspace
        except AttributeError:
            pass
        try:
            file.softspace = newvalue
        except (AttributeError, TypeError):
            # "attribute-less object" or "read-only attributes"
            pass
        return oldvalue


    def runcode(self, code):
        try:
            # uh, sys is threadsafe, right?
            sys.stdout = self.wfile
            sys.stderr = self.wfile
            exec code in globals()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            if self._softspace(self.wfile, 0):
                print >>self.wfile


class _Tee(object):
    """
    wrapper object that takes two file-like objects and tees all calls to write() and next() from one to the other
    """

    def __init__(self, inputfile, outputfile, format=None):
        self.inputfile = inputfile
        self.outputfile = outputfile
        self.format = format or (lambda x: x)
        self.linebuf = ''

    def __getattribute__(self, attrname):
        try:
            return object.__getattribute__(self, attrname)
        except AttributeError:
            return getattr(object.__getattribute__(self, 'inputfile'), attrname)

    def write(self, data):
        self.outputfile.write(self.format(data))
        return self.inputfile.write(data)

    def next(self):
        line = self.inputfile.next()
        self.outputfile.write(self.format(line))
        return line

class _MyTCPRequestHandler(SocketServer.StreamRequestHandler):

    def __init__(self, request, client_address, server, logging=False):
        self.logging = logging
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)

    @classmethod
    def factoryfactory(cls, logging=True):
        """
        farcical thing that lets us add arguments to the constructor even though we don't have control of how/where it is called
        """
        def factory(request, client_address, server):
            instance = cls(request, client_address, server, logging)
            return instance

        return factory


    @staticmethod
    def _get_formatter(addr, dir):
        def formatter(line):
           return '-- ' + client_address_str + ' ' + dir + ' ' + line.rstrip() + "\n"


    def handle(self):

        client_address_str = ':'.join(map(str, self.client_address))
        server_address_str = ':'.join(map(str, self.connection.getsockname()))

        if self.logging:
            print >>sys.stderr, "-- client", client_address_str, "connected"
            inputoutput = (
                _Tee(self.rfile, sys.stderr, self._get_formatter(client_address_str, '<')),
                _Tee(self.wfile, sys.stderr, self._get_formatter(client_address_str, '>'))
                )

        else:
            inputoutput = (self.rfile, self.wfile)

        # self.wfile.flush()
            
        console = _MyConsole(*inputoutput)

        banner = "%s\n<<%s %s on %s serving %s>>" % \
            (sys.version, 
            self.server.__class__.__name__, hex(id(self.server)),
            server_address_str,
            client_address_str
            )
        

        try:
            console.interact(banner=banner)

        except StopIteration:
            if self.logging:
                print >>sys.stderr, "-- client", client_address_str, "closed"
        except SocketServer.socket.error, e:
            if self.logging:
                print >>sys.stderr, "-- client", client_address_str, "disconnected"


class ShellServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    ShellServer class

    Usage Example:

    >>> s = ShellServer('localhost', 0)
    >>> print s.server_address
    >>> s.serve_forever()
    """

    def __init__(self, host='127.0.0.1', port=None, logging=True):
        """
        port is required, host is optional. host defaults to localhost. if port == 0 it will choose an available port itself. the ultimate server address used is accessible at self.server_address .
        """

        if port is None: raise TypeError

        SocketServer.TCPServer.__init__(self, (host, port), _MyTCPRequestHandler.factoryfactory(logging=logging))


    def start(self):
        self.serve_forever()


class AsyncShellServer(threading.Thread, ShellServer):
    """
    A ShellServer class that will run in the background without blocking the current thread

    Usage Example:

    >>> s = AsyncShellServer('localhost', 0)
    >>> print s.server_address
    >>> s.setDaemon(True)
    >>> s.start()
    >>> 

    Set daemon=True on the constructor or call setDaemon(True) on the object 
    to have the server thread exit when the main thread exits if inactive.
    See the documentation on threading.Thread, of which this class is a subclass.
    """

    def __init__(self, host='127.0.0.1', port=None, logging=True, daemon=None):
        ShellServer.__init__(self, port, host)
        threading.Thread.__init__(self, target=self.serve_forever)
        if daemon is not None:
            self.setDaemon(daemon)


def main():
    from optparse import OptionParser

    _prog_name = 'shellserver console'

    parser = OptionParser(
        usage="%prog [options] port",
        version="%%prog (%s) %s" % (_prog_name, __version__),
        add_help_option=False)

    parser.add_option('--help', action='help', help='show this message')

    parser.add_option('-q', 
                    dest='quiet',
                    help='suppress startup messages',
                    action='store_true')

    parser.add_option('-h', '--host',
                    dest="hostname",
                    default='127.0.0.1',
                    help="hostname to bind to. use 0.0.0.0 for any.\n[default: %default]",
                    metavar="HOST")

    parser.add_option("-p", '--port', 
                    dest="port",
                    help="port to use. use 0 for self-assigned port [default].",
                    type='int',
                    default=0,
                    metavar="PORT")

    (flags, args) = parser.parse_args()

    if args:
        if len(args) > 1:
            parser.error("unrecognized options: %r" % args)
        elif flags.port and args:
            parser.error("conflicting port settings: %r and %r" % (flags.port, args))
        else:
            try:
                port = int(args[0])
            except ValueError:
                parser.error("invalid integer value: %r" % (args[0],))

    else:
        port = flags.port

    host = flags.hostname

    server = ShellServer(host, port, logging=not flags.quiet)

    if not flags.quiet:
        print >>sys.stderr, "running on", ':'.join(map(str, server.server_address))

    server.start()

