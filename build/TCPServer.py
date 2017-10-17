import sys
import socketserver

class TCPServer:
    def __init__(self, port):
        # Make sure the port is valid.
        try:
            self.port = int(port)

            if self.port < 1024 or self.port > 65535:
                raise ValueError("Port out of bounds")

            if port[0] == '0':
                raise ValueError("Port must be a decimal value")

        except ValueError as e:
            print("Bad port:", str(e), file=sys.stderr)
            sys.exit(255)

    # Start a new TCP server with the given port.
    def start(self):
        server = socketserver.TCPServer(('localhost', int(self.port)), TCPHandler)
        print('Starting TCP server on port', self.port)


# TCP handler class used as an argument to the TCP server. This allows us to
# overload handling functions to send the incoming data to our parser.
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Handle")
