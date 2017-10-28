"""
We can throw these errors and catch them higher up. 

I wanted to make separate classes because a Parse Error returns a status code of "FAILED" and SecurityError returns a status code of "DENIED", so we can just check the type of the error to know which one is thrown. Let me know if we want to change this, I use ParseError in Parser.py so if we delete/change this file we will need to change a few things.

"""


class ParseError(Exception):
	pass
	
class SecurityError(Exception):
	pass

class Timeout(Excception):
	pass
