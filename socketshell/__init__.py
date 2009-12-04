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

    Set daemon=True on the constructor or call setDaemon(True) on the object to have the server thread exit when the main thread exits if inactive. See the documentation on threading.Thread, of which this class is a subclass.
    """

    def __init__(self, host='127.0.0.1', port=None, logging=True, daemon=None):
        ShellServer.__init__(self, port, host)
        threading.Thread.__init__(self, target=self.serve_forever)
        if daemon is not None:
            self.setDaemon(daemon)

