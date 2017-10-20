import sys
import socketserver
import signal
from Parser import Parser


class TCPServer:
    # TCP server constructor.
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

        signal.signal(signal.SIGTERM, self.handle_sigterm)

    # Start a new TCP server with the given port.
    def start(self):
        try:
            self.server = socketserver.TCPServer(('localhost', int(self.port)),
                TCPHandler)

        except OSError as e:
            print('Error:', str(e), file=sys.stderr)
            exit(63)

        print('Server started on port', self.port)

        self.server.serve_forever()

    # Handle SIGTERM signals gracefully. For our purposes the server should
    # exit with return code 0 when it receives a SIGTERM signal.
    def handle_sigterm(self, signum, frame):
        print('Handling SIGTERM. Closing server and exiting with return code 0.')
        self.server.server_close()
        exit(0)


# TCP handler class used as an argument to the TCP server. This allows us to
# overload handling functions to send the incoming data to our parser.
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Input programs can be a maximum of 1,000,000 characters.
        data = self.request.recv(1000000).strip()

        try:
            data = data.decode('utf-8')

        except AttributeError:
            print('Data may have not been encoded', file=sys.stderr)

        print('Received program:', data)

        status_list = Parser.parse(data)

        # Convert status list to appropriate response.
        response = ''
        for status in status_list:
            response += status + '\n'

        self.request.sendall(response.encode('utf-8'))
