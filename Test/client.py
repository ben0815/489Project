#!/usr/bin/env python3

import socket
import sys


def main():
    host = 'localhost'
    port = 8080

    if len(sys.argv) > 1:
         port = int(sys.argv[1])

    data = 'TESTING!'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        sock.sendall(data.encode('utf-8'))

        received = sock.recv(1000000)

    finally:
        sock.close()

    print('Sent:', data)
    print('Received:', received)

if __name__ == '__main__':
    main()
