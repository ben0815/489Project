import re
from Error import ParseError

token_map = {'principal' : 'PRINCIPAL', 'as' : 'AS', 'password' : 'PASSWORD', 'do' : 'DO',
      '***' : 'END', 'exit' : 'EXIT', 'return' : 'RETURN', '{' : 'LPAR', '}' : 'RPAR',
      '[' : 'LBRACK', ']' : 'RBRACK', 'create' : 'CREATE', 'change' : 'CHANGE', 'password' :
      'PASSWORD', 'set' : 'SET', 'append' : 'APPEND', 'to' : 'TO', 'with' : 'WITH', '=' :
      'EQUALS', '.' : 'DOT', ',' : 'COMMA', '->' : 'ARROW', 'local' : 'LOCAL', 'foreach' :
      'FOR', 'in' : 'IN', 'replacewith' : 'REPLACE', 'delegation' : 'DELEGATION', 'delete' :
      'DELETE', 'default' : 'DEFAULT', 'read' : 'RIGHT', 'write' : 'RIGHT', 'append' :
      'RIGHT', 'delegate' : 'RIGHT', 'all' : 'ALL'}

punctuation = ['=', '[', ']', '.', '-', '>', '{', '{', ',']

#TODO: Create function for expect, instead of ugly if-statements.
#TODO: Need to check that i is still less than len(tokens) even if expect is a success
#TODO: Actually store the expressions (thinking separate entity for lists, dicts, and variables)
#TODO: Implement all the little details of the spec. Actually check for FAILEDs and DENIEDs
#TODO: Test the Parser more rigorously
#TODO: will strings be passed to isStringFormat already have double quotes removed? I assumed no.

def isStringFormat(str):
    if len(str) > 65535: # max length
        return False
    if re.match('^\"[A-Za-z0-9_ ,;\.?!-]*\"$', str) is None: # reasonably tested, could test more
        return False
    return True

def isIdentifierFormat(str):
    if str in token_map: # cannot be the same as a key word
        return False
    if len(str) > 255: # max length
        return False
    if re.match('^[A-Za-z][A-Za-z0-9_]*$', str) is None: # reasonably tested, could test more
        return False
    return True

def expect(i, tokens, expected):
    if i < len(tokens) and tokens[i][0] != expected:
        return False
    elif i >= len(tokens):
        return False
    else:
        return True

def getValue(i, tokens):
    if expect(i, tokens, 'IDENTIFIER'):
        x = tokens[i][1]
        i += 1
        if expect(i, tokens, 'DOT'):
            i += 1
            # x.y
            if expect(i, tokens, 'IDENTIFIER'):
                y = tokens[i][1]
                return True, i, x + '.' + y
            else:
                return False, i, None
        elif expect(i, tokens, 'RPAR'):
            return True, i, x
        else:
            return True, (i - 1), x
    # s
    elif expect(i, tokens, 'STRING'):
        s = tokens[i][1]
        return True, i, s
    else:
        return False, i, None

def getFieldVals(i, tokens):
    value = ''
    i += 1
    while i < len(tokens):
        if not expect(i, tokens, 'IDENTIFIER'):
            return False, i, None
        i += 1
        if not expect(i, tokens, 'EQUALS'):
            return False, i, None
        i += 1
        status, i, temp = getValue(i, tokens)

        if not status:
            return False, i, None

        value += temp

        if expect(i, tokens, 'RPAR'):
            return True, i, value
        elif not expect(i, tokens, 'COMMA'):
            return False, i, None
    
    return False, i, None

def getExpr(i, tokens):
    if expect(i, tokens, 'LBRACK'):
        i += 1
        if not expect(i, tokens, 'RBRACK'):
            return False, i, None
        return True, i, '[]'
    elif expect(i, tokens, 'IDENTIFIER') or expect(i, tokens, 'STRING'):
        return getValue(i, tokens)
    elif expect(i, tokens, 'LPAR'):
        return getFieldVals(i, tokens)
    else:
        return False, i, None

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
                    if word in token_map:
                        lexed.append([token_map[word], word])
                        word = ''
                        i += 1
                    else:
                        #if not isIdentifierFormat(word):
                        #    raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                        lexed.append(['IDENTIFIER', word])
                        word = ''
                        i += 1
                else:
                    i += 1
            # If current char is token, append previous state and new token.
            elif line[i] in token_map:
                if word != '':
                    if word in token_map:
                        lexed.append([token_map[word], word])
                    else:
                        #if not isIdentifierFormat(word):
                        #    raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                        lexed.append(['IDENTIFIER', word])

                lexed.append([token_map[line[i]], line[i]])
                word = ''
                i += 1
            # If current char is quotation, find next quotation.
            elif line[i] == '"':
                i += 1
                while line[i] != '"':
                    word += line[i]
                    i += 1
                    if i == len(line):
                        return []

                i += 1
                #if not isStringFormat(word):
                #    raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                    
                lexed.append(['STRING', word])
                word = ''
            elif word in token_map and (i + 1) < len(line) and line[i + 1] in punctuation:
                lexed.append([token_map[word], word])
                word = ''
            else:
                word += line[i]
                i += 1

        # Get the last token
        if word != '':
            if word in token_map:
                lexed.append([token_map[word], word])
                word = ''
            else:
                lexed.append(['IDENTIFIER', word])
                word = ''
    return lexed

class Parser:

    #@staticmethod
    #def parse(command):
    #    status_list = []
    #    try:
    #        tokens = lexer(command)
    #    except ParseError:
    #        status_list.append("FAILED") # I think this is all we need to do
    #        return status_list

        # Remove the first element (guaranteed to be NEWLINE token)
    #    tokens.pop(0)

    #    if not is_formatted_correct(tokens):
    #        return status_list

    # def is_formatted_correct(tokens):
    # idea is to have a function to make sure the program is syntactically correct
    # and we dont make parse(command) a megafunction
    # Check that first line is 'as principal p password s do \n'
        # if not (len(tokens) > 6 and tokens[0][0] == 'AS' and tokens[1][0] == 'PRINCIPAL' and tokens[2][0] == 'IDENTIFIER' and tokens[3][0] == 'PASSWORD' and tokens[4][0] == 'STRING' and tokens[5][0] == 'DO' and tokens[6][0] == 'NEWLINE'):
            # status_list.append('{"status":"FAILED"}')
            # return False

    @staticmethod
    def parse(command):
        status_list = []

        try:
            tokens = lexer(command)     
        except ParseError:
            return ['{"status":"FAILED"}']

        # Check if lexer failed
        if len(tokens) < 1:
            return ['{"status":"FAILED"}']
        
        tokens.pop(0)

        # Check that first line is 'as principal p password s do'
        if not (len(tokens) > 5 and tokens[0][0] == 'AS' and tokens[1][0] == 'PRINCIPAL' and tokens[2][0] == 'IDENTIFIER' and tokens[3][0] == 'PASSWORD' and tokens[4][0] == 'STRING' and tokens[5][0] == 'DO'):
            return ['{"status":"FAILED"}']

        # Check that the last line is '***'
        if tokens[len(tokens) - 1 ][0] != 'END':
            return ['{"status":"FAILED"}']

        # Now execute the commands
        i = 6
        while i < len(tokens):
            if not expect(i, tokens, 'NEWLINE'):
                return ['{"status":"FAILED"}']

            i += 1
            # 'exit \n' command
            # TODO: exit security
            if expect(i, tokens, 'EXIT'):
                status_list.append('{"status":"EXITING"}')
                i += 1

            # 'return <expr> \n' command
            elif expect(i, tokens, 'RETURN'):
                i += 1
                status, i, value = getExpr(i, tokens)

                if not status:
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"RETURNING","output":"' + value + '"}')
                i += 1

            # 'create principal p s'
            elif expect(i, tokens, 'CREATE'):
                i += 1
                if not expect(i, tokens, 'PRINCIPAL'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'STRING'):
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"CREATE_PRINCIPAL"}')
                i += 1

            # 'change password p s'
            elif expect(i, tokens, 'CHANGE'):
                i += 1
                if not expect(i, tokens, 'PASSWORD'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'STRING'):
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"CHANGE_PASSWORD"}')
                i += 1

            # 'append to x with <expr>'
            elif expect(i, tokens, 'APPEND'):
                i += 1
                if not expect(i, tokens, 'TO'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'WITH'):
                    return ['{"status":"FAILED"}']

                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"APPEND"}')
                i += 1

            # 'local x = expr'
            elif expect(i, tokens, 'LOCAL'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'EQUALS'):
                    return ['{"status":"FAILED"}']

                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"LOCAL"}')
                i += 1

            # 'foreach y in x replacewith <expr>'
            elif expect(i, tokens, 'FOR'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IN'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'REPLACE'):
                    return ['{"status":"FAILED"}']

                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"FOREACH"}')
                i += 1

            # 'set delegation <tgt> q <right> -> p' or 'set x = <expr>'
            elif expect(i, tokens, 'SET'):
                i += 1
                if expect(i, tokens, 'DELEGATION'):
                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'RIGHT'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'ARROW'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']

                    status_list.append('{"status":"SET_DELEGATION"}')
                    i += 1

                elif expect(i, tokens, 'IDENTIFIER'):
                    i += 1
                    if not expect(i, tokens, 'EQUALS'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    status, i, value = getExpr(i, tokens)

                    if not status:
                        return ['{"status":"FAILED"}']

                    status_list.append('{"status":"SET"}')
                    i += 1

                else:
                    return ['{"status":"FAILED"}']

            # 'delete delegation <tgt> q <right> -> p'
            elif expect(i, tokens, 'DELETE'):
                i += 1
                if not expect(i, tokens, 'DELEGATION'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'RIGHT'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'ARROW'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"DELETE_DELEGATION"}')
                i += 1

            # 'default delegator = p'
            elif expect(i, tokens, 'DEFAULT'):
                i += 1
                if not expect(i, tokens, 'DELEGATOR'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'EQUALS'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"DEFAULT_DELEGATOR"}')
                i += 1

            elif i < len(tokens) and tokens[i][0] == 'END':
                i += 1
                if i != len(tokens):
                    return ['{"status":"FAILED"}']

            else:
                return ['{"status":"FAILED"}']

        return status_list
