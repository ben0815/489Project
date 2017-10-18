# Tested on Python 2.7.12
# Code for an extremely basic lexer. Needs minor tweaks to satisfy the spec details.

tokens = {'principal' : 'PRINCIPAL', 'as' : 'AS', 'password' : 'PASSWORD', 'do' : 'DO',
	  '***' : 'END', 'exit' : 'EXIT', 'return' : 'RETURN', '{' : 'LPAR', '}' : 'RPAR',
	  '[' : 'LBRACK', ']' : 'RBRACK', 'create' : 'CREATE', 'change' : 'CHANGE', 'password' :
	  'PASSWORD', 'set' : 'SET', 'append' : 'APPEND', 'to' : 'TO', 'with' : 'WITH', '=' :
	  'EQUALS', '.' : 'DOT', ',' : 'COMMA', '->' : 'ARROW', 'local' : 'LOCAL', 'foreach' :
	  'FOR', 'in' : 'IN', 'replacewith' : 'REPLACE', 'delegation' : 'DELEGATION', 'delete' :
	  'DELETE', 'default' : 'DEFAULT', 'read' : 'RIGHT', 'write' : 'RIGHT', 'append' :
	  'RIGHT', 'delegate' : 'RIGHT'}

def lexer(text):
    text = text.splitlines()
    lexed = []

    for line in text:
        lexed.append(['NEWLINE', '\n'])
        # TODO: Split on just spaces, not tabs
        word = ''
        i = 0

        # TODO: Verify that identifiers follow the spec. Alpha followed by alphanumeric
        # and underscore.
        while i < len(line):
            # Eat whitespace or append a new token
            if line[i] == ' ':
                if word != '':
                    if word in tokens:
                        lexed.append([tokens[word], word])
                        word = ''
                        i += 1
                    else:
                        lexed.append(['IDENTIFIER', word])
                        word = ''
                        i += 1
                else:
                    i += 1
            # If current char is token, append previous state and new token.
            elif line[i] in tokens:
                if word != '':
                    if word in tokens:
                        lexed.append([tokens[word], word])
                    else:
                        lexed.append(['IDENTIFIER', word])

                lexed.append([tokens[line[i]], line[i]])
                word = ''
                i += 1
            # If current char is quotation, find next quotation.
            elif line[i] == '"':
                i += 1
                while line[i] != '"':
                    word += line[i]
                    i += 1
                    if i == len(line):
                        print('FAILED')
                        return

                i += 1
                lexed.append(['STRING', word])
                word = ''
            else:
                word += line[i]
                i += 1

        # Get the last token
        if word != '':
            if word in tokens:
                lexed.append([tokens[word], word])
                word = ''
            else:
                lexed.append(['IDENTIFIER', word])
                word = ''
    print(lexed)

# Testing using one of the examples pulled from the project spec
lexer('as        principal admin password "admin" do\ncreate principal bob "B0BPWxxd"\nset x = "my string"\nset y ={f1=x,f2="field2"}\nset     delegation x admin read-> bob\nreturn y . f1\n***')
