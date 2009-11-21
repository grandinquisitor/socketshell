"""
ShellServer (or SocketShell?)

Live, multi-user threaded remote python shell access.

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

"""


import code
import SocketServer
import threading
import sys

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

class _MyTCPRequestHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        self.wfile.flush()
        console = _MyConsole(self.rfile, self.wfile)
        console.interact()


class ShellServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    ShellServer class

    Usage Example:

    >>> s = ShellServer('localhost', 0)
    >>> print s.server_address
    >>> s.serve_forever()
    """

    def __init__(self, host, port):
        SocketServer.TCPServer.__init__(self, (host, port), _MyTCPRequestHandler)


class AsyncShellServer(threading.Thread, ShellServer):
    """
    A ShellServer class that will run in the background without
    blocking anything

    Usage Example:

    >>> s = AsyncShellServer('localhost', 0)
    >>> print s.server_address
    >>> s.setDaemon(True)
    >>> s.start()
    >>> 
    """

    def __init__(self, host, port):
        ShellServer.__init__(self, host, port)
        threading.Thread.__init__(self, target=self.serve_forever)



if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "0.0.0.0", 6669

    server = ShellServer(HOST, PORT)
    print "running on", server.server_address

    server.serve_forever()
