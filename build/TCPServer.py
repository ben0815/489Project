import sys
import socketserver
import signal
import time
from Error import Timeout
from Error import ParseError
from Parser import Parser


class TCPServer:
    # TCP server constructor.
    def __init__(self, port, password):
        # Make sure the port is valid.
        try:
            self.port = int(port)

            if self.port < 1024 or self.port > 65535:
                raise ValueError("Port out of bounds")

            if port[0] == '0':
                raise ValueError("Port must be a decimal value")

            Parser.set_password(password)

        except ValueError as e:
            print("Bad port:", str(e), file=sys.stderr)
            sys.exit(255)
        except ParseError:
            print("Bad admin password format.")
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

    program = ''

    # Setup SIGALRM signal used for the timeout.
    def setup(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)

    # Raise a timeout exception when SIGALRM is signaled.
    def handle_timeout(self, signum, frame):
        raise Timeout

    def handle(self):
        # Start 30 second timer. Timeout if the entire program is not received
        # within 30 seconds.
        signal.alarm(35)

        try:
            self.receive()
        except Timeout:
            print('Timeout exceeded (30 seconds). Please resend the program' \
                    ' from the beginning.')
            response = '{"status":"TIMEOUT"}'
            print("Response sent:")
            print(response)
            self.request.sendall(response.encode('utf-8'))

    # Clear program and reset alarm.
    def finish(self):
        self.program = ''
        signal.alarm(0)

    def receive(self):
        # Accept data from client until '***' is received.
        while True:
            # Input programs can be a maximum of 1,000,000 characters.
            data = self.request.recv(1000000)

            try:
                data = data.decode('utf-8')

            except AttributeError:
                print('Data may have not been encoded', file=sys.stderr)
                continue

            # Contatenate data to overall program until '***' is received.
            self.program += data
            sep = list(filter(None, data.split('\n')))

            if sep[-1].strip() == '***':
                break

        signal.alarm(0)

        print('Received program:')
        print(self.program)
        
        if len(self.program) > 1000000:
            response = '{"status":"FAILED"}'
            print("Response sent:")
            print(response)
            self.request.sendall(response.encode('utf-8'))
        else:
            status_list = []

            # Once a complete program is received we can send it to the parser.
            status_list = Parser.parse(self.program)

            # Convert status list to appropriate response.
            response = ''

            exit = False
            for status in status_list:
                if status == '{"status":"EXITING"}':
                    exit = True

                response += status + '\n'

            # Send backt to client.
            print("Response sent:")
            print(response)
            self.request.sendall(response.encode('utf-8'))

            if exit:
                exit(0)
