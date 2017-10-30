#!/usr/bin/env python3

import socket
import sys


def main():
    host = 'localhost'
    port = 8082

    if len(sys.argv) > 1:
         port = int(sys.argv[1])

    #data =  "as principal admin password \"admin\" do\ncreate principal alice \"alice\"\nset x = {y=\"string\", z=\"string2\"}\nset delegation x admin delegate -> alice\nreturn []\n***\n"
    
    #data = "as principal admin password \"admin\" do\n create principal bob \"bob\"\nreturn \"success\"\n***"
    
    #data = "as principal bob password \"bob\" do\n return x\n ***        \n"	
	
    #data = "as principal admin password \"admin\" do               \n default delegator = alice     \n return \"success\"\n    ***"
    #data = "as principal admin password \"admin\" do\n create principal billy \"billy\"\n return \"success\"\n***"
    data = "as principal billy password \"billy\" do\n return x\n ***        \n"	
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((host, port))
        sock.sendall(data.encode('utf-8'))

        received = sock.recv(1000000)

    finally:
        sock.close()

    print('Sent:', data)
    print('Received:', received.decode('utf-8'))

if __name__ == '__main__':
    main()
