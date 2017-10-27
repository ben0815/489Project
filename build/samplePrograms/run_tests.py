import subprocess

print(subprocess.getoutput("netcat localhost 5000 < simple.txt")) 
