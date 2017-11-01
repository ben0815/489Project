#!/usr/bin/env python3

import socket
import sys


def main():
    host = 'localhost'
    port = 8087
    
    if len(sys.argv) > 1:
         port = int(sys.argv[1])

    #data =  "as principal admin password \"admin\" do\ncreate principal alice \"alice\"\nset x = {y=\"string\", z=\"string2\"}\nset delegation x admin delegate -> alice\n***\n"
    
    #data = "as principal admin password \"admin\" do\n create principal bob \"bob\"\nreturn \"success\"\n***"
    
    #data = "as principal bob password \"bob\" do\n return x\n ***        \n"	
	
    #data = "as principal admin password \"admin\" do               \n default delegator = alice     \n return \"success\"\n    ***"
    #data = "as principal admin password \"admin\" do\n create principal billy \"billy\"\n return \"success\"\n***"
    #data =  "as principal admin password \"admin\" do\nset x = []\nappend to x with \"s\"\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nappend to x with x\nreturn x\n***\n"
    #data = "as principal admin password \"admin\" do\ncreate principal bob \"bob\"\nset x = \"HELLO\"\nset y = split(x,\"--\")\nset z = concat(y.snd,y.fst)\nset w = tolower(x)\nreturn tolower(w)\n***\n"
    #data = "as principal bob password \"bob\" do\n set q = \"test\"\nset o = split(q, x)\nreturn \"FAIL\"\n***\n"
    #data = "as principal admin password \"admin\" do\nset records = []\nappend to records with { name = \"mike\", date = \"1-1-90\" }\nappend to records with { name = \"sandy\", date = \"1-1-90\" }\nappend to records with { name = \"dave\", date = \"1-1-85\" }\nlocal names = records\nfiltereach rec in names with equal(rec.date,\"1-1-90\")\nfiltereach rec in records with notequal(rec.date,\"1-1-90\")\nappend to records with names\nreturn records\n***\n"
    #data = "as principal admin password \"admin\" do\nset x = []\nappend to x with \"hello\"\nappend to x with \"there\"\nappend to x with { x=\"oh my\" }\nset z = x\nfiltereach y in x with \"0\"\nfiltereach y in z with \"\"\nappend to x with z\nreturn x\n***\n"
    #data = "as principal admin password \"admin\" do\nset records = []\nappend to records with \"ike\"\nappend to records with \"andy\"\nappend to records with \"ally\"\nlocal names = records\nforeach rec in names replacewith concat(\"m\",rec)\nlocal splits = names\nforeach rec in splits replacewith split(rec,\"....\")\nforeach rec in splits replacewith rec.snd\nlocal filters = splits\nfiltereach rec in filters with rec\nfiltereach rec in names with notequal(rec,\"mike\")\nappend to records with names\nappend to records with splits\nappend to records with filters\nreturn records\n***\n"
    #data = "as principal admin password \"admin\" do\nset x = { f1 = \"hello\", f2 = \"there\" }\nset y = let z = concat(x.f1, \" \") in concat(z, x.f2)\nreturn y\n***"
    #data = "as principal admin password \"admin\" do\nset x = { f1 = \"hello\", f2 = \"there\" }\nset y = let z = concat(x.f1, \" \") in concat(z, x.f2)\nset z = []\nappend to z with x\nappend to z with y\nreturn z\n***\n"
    data = "as principal admin password \"admin\" do\nset records = []\nappend to records with { name = \"mike\", date = \"1-1-90\" }\nappend to records with { name = \"michelle\", date = \"1-1-85\" }\nappend to records with { name = \"dave\", date = \"1-1-85\" }\nlocal names = records\nfiltereach rec in records with let lhs = split(rec.name,\"..\") in let rhs = split(\"milosh\",\"..\") in equal(lhs.fst,rhs.fst)\nfiltereach rec in names with let r = { name = \"dave\", date = \"1-1-85\" } in equal(rec,r)\nappend to records with names\nreturn records\n***\n"
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
