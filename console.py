import code
import SocketServer
import threading
import sys

foo = 1

class MyConsole(code.InteractiveConsole):
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

class MyTCPRequestHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        self.wfile.flush()
        console = MyConsole(self.rfile, self.wfile)
        console.interact()


class ShellServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, host, port):
        SocketServer.TCPServer.__init__(self, (host, port), MyTCPRequestHandler)


class AsyncShellServer(threading.Thread, ShellServer):
    def __init__(self, host, port):
        ShellServer.__init__(self, host, port)
        threading.Thread.__init__(self, target=self.serve_forever)
        self.setDaemon(True)



if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "0.0.0.0", 6669

    server = ShellServer(HOST, PORT)
    print "running on", server.server_address

    server.serve_forever()
