#!/usr/bin/env python3

import sys
from TCPServer import TCPServer
from Parser import Parser

def main():
    # if len(sys.argv) <= 1 or len(sys.argv) > 3:
    #    print("Usage: ./server <port> [<password>]", file=sys.stderr)
    #    sys.exit(255)

    # Get port and password from command line arguments.
    # port = sys.argv[1]

    # password = "admin"
    # if len(sys.argv) is 3:
    #    password = sys.argv[2]

    # Startup the server.
    # server = TCPServer(port)

    # server.start()
    
    
    x = Parser()
    print(x.parse('as        principal admin password "admin" do\ncreate principal bob "settler"\nset x = testing\nset     delegation x admin read-> bob\nreturn y . f1\n***'))


if __name__ == '__main__':
    main()
