import sys
from optparse import OptionParser

from __init__ import ShellServer, __version__ as _prog_version

_prog_name = 'shellserver console'

if __name__ == "__main__":
    parser = OptionParser(
        usage="%prog [options] port",
        version="%%prog (%s) %s" % (_prog_name, _prog_version),
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
