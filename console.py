import code
import SocketServer
import threading
import sys

foo = 1

class MyConsole(code.InteractiveConsole):
    def __init__(self, rfile, wfile, locals=None, filename="<console>"):
        code.InteractiveConsole.__init__(self, locals, filename)
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
            # http://stackoverflow.com/questions/701802/how-do-i-execute-a-string-containing-python-code-in-python
            context = self.locals if self.locals else globals()
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

class TCPRequestHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        self.wfile.flush()
        console = MyConsole(self.rfile, self.wfile)
        console.interact()


class ForkingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass




if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "0.0.0.0", 6669

    server = ForkingTCPServer((HOST, PORT), TCPRequestHandler)
    print "running on", server.server_address

    server.serve_forever()
