import re
from Error import ParseError
from Error import SecurityError
from Database import Database

token_map = {'principal' : 'PRINCIPAL', 'as' : 'AS', 'password' : 'PASSWORD', 'do' : 'DO',
      '***' : 'END', 'exit' : 'EXIT', 'return' : 'RETURN', '{' : 'LPAR', '}' : 'RPAR',
      '[' : 'LBRACK', ']' : 'RBRACK', 'create' : 'CREATE', 'change' : 'CHANGE', 'password' :
      'PASSWORD', 'set' : 'SET', 'append' : 'APPEND', 'to' : 'TO', 'with' : 'WITH', '=' :
      'EQUALS', '.' : 'DOT', ',' : 'COMMA', '->' : 'ARROW', 'local' : 'LOCAL', 'foreach' :
      'FOR', 'in' : 'IN', 'replacewith' : 'REPLACE', 'delegation' : 'DELEGATION', 'delete' :
      'DELETE', 'default' : 'DEFAULT', 'read' : 'RIGHT', 'write' : 'RIGHT', 'delegate' : 'RIGHT', 'all' : 'ALL'}

punctuation = ['=', '[', ']', '.', '-', '>', '{', '{', ',']

#TODO: Create function for expect, instead of ugly if-statements.
#TODO: Need to check that i is still less than len(tokens) even if expect is a success
#TODO: Actually store the expressions (thinking separate entity for lists, dicts, and variables)
#TODO: Implement all the little details of the spec. Actually check for FAILEDs and DENIEDs
#TODO: Test the Parser more rigorously
#TODO: will strings be passed to isStringFormat already have double quotes removed? I assumed no./ 

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

def isCommentFormat(str):
    if re.match('[\/][\/][A-Za-z0-9_ ,;\.?!-]*$', str) is None:
        return False
    return True

def expect(i, tokens, expected):
    if i < len(tokens) and tokens[i][0] != expected:
        return False
    elif i >= len(tokens):
        return False
    else:
        return True

def getValue(i, tokens, user):
    if expect(i, tokens, 'IDENTIFIER'):
        x = tokens[i][1]
        i += 1
        if expect(i, tokens, 'DOT'):
            i += 1
            # x.y
            if expect(i, tokens, 'IDENTIFIER'):
                y = tokens[i][1]
                return True, i, database.get_record_value(user, x, y)
            else:
                return False, i, None
        elif expect(i, tokens, 'RPAR') or expect(i, tokens, 'COMMA'):
            return True, i, database.get_identifier_value(user, x)
        else:
            return True, (i - 1), database.get_identifier_value(user, x)
    # s
    elif expect(i, tokens, 'STRING'):
        s = tokens[i][1]
        return True, i, s
    else:
        return False, i, None

def getFieldVals(i, tokens, user):
    values = {}
    i += 1
    while i < len(tokens):
        if not expect(i, tokens, 'IDENTIFIER'):
            return False, i, None
        
        ident = tokens[i][1]
        
        if ident in values:
            raise ParseError    
        
        i += 1
        if not expect(i, tokens, 'EQUALS'):
            return False, i, None
            
        i += 1
        status, i, temp = getValue(i, tokens, user)
        
        if expect(i, tokens, 'STRING'):
            i += 1
        
        if not status:
            return False, i, None
        
        if isinstance(temp, list) or isinstance(temp, dict):
            raise ParseError
        
        values[ident] = temp     

        if expect(i, tokens, 'RPAR'):
            return True, i, values
        elif not expect(i, tokens, 'COMMA'):
            return False, i, None
        else:
            i += 1
    
    return False, i, None

def getExpr(i, tokens, user):
    if expect(i, tokens, 'LBRACK'):
        i += 1
        if not expect(i, tokens, 'RBRACK'):
            return False, i, None
        return True, i, []
    elif expect(i, tokens, 'IDENTIFIER') or expect(i, tokens, 'STRING'):
        return getValue(i, tokens, user)
    elif expect(i, tokens, 'LPAR'):
        return getFieldVals(i, tokens, user)
    else:
        return False, i, None

def lexer(text):
    text = text.splitlines()
    lexed = []

    for line in text:
        i = 0
        
        #if 1 < len(line) and line[i + 1] == '/' and line[i] == '/':
        #    print('hello')
        #    break
        
        lexed.append(['NEWLINE', '\n'])
        # TODO: Split on just spaces, not tabs
        word = ""
        

        # TODO: Verify that identifiers follow the spec. Alpha followed by alphanumeric
        # and underscore.
        while i < len(line):
            if line[i] == '/':
                if (i + 1) < len(line) and line[i + 1] == '/':
                    break

            # Eat whitespace or append a new token
            if line[i] == ' ':
                if word != "":
                    if word in token_map:
                        lexed.append([token_map[word], word])
                        word = ""
                        i += 1
                    else:
                        if not isIdentifierFormat(word):
                            raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                        lexed.append(['IDENTIFIER', word])
                        word = ""
                        i += 1
                else:
                    i += 1
            # If current char is token, append previous state and new token.
            elif line[i] in token_map:
                if word != "":
                    if word in token_map:
                        lexed.append([token_map[word], word])
                    else:
                        if not isIdentifierFormat(word):
                            raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                        lexed.append(['IDENTIFIER', word])

                lexed.append([token_map[line[i]], line[i]])
                word = ""
                i += 1
            # If current char is quotation, find next quotation.
            elif line[i] == '"':
                i += 1
                if i == len(line):
                        return []
                while line[i] != '"':
                    word += line[i]
                    i += 1
                    if i == len(line):
                        return []

                i += 1
                if not isStringFormat('"' + word + '"'):
                    raise ParseError("Identifier must contain only alphanumeric characters or underscores, be no greater than 255 characters, and not be one of the reserved keywords.")
                    
                lexed.append(['STRING', word])
                word = ""
            elif word in token_map and (i + 1) < len(line) and line[i + 1] in punctuation:
                lexed.append([token_map[word], word])
                word = ""
            else:
                word += line[i]
                i += 1

        # Get the last token
        if word != "":
            if word in token_map:
                lexed.append([token_map[word], word])
                word = ""
            else:
                lexed.append(['IDENTIFIER', word])
                word = ""
    return lexed
    
database = Database() 

class Parser:
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
        else:
            try:
                database.as_principal(tokens[2][1], tokens[4][1])
            except ParseError:
                return ['{"status":"FAILED"}']
            except SecurityError:
                return ['{"status":"DENIED"}']
            
            user = tokens[2][1]

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
                
                try:
                    status, i, value = getExpr(i, tokens, user)

                    if not status:
                        return ['{"status":"FAILED"}']
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']

                status_list.append('{"status":"RETURNING","output":"' + str(value) + '"}')
                i += 1

            # 'create principal p s'
            elif expect(i, tokens, 'CREATE'):
                i += 1
                if not expect(i, tokens, 'PRINCIPAL'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                
                p = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'STRING'):
                    return ['{"status":"FAILED"}']

                s = tokens[i][1]
                
                try:
                    message = database.create_principal(user, p, s)
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']
                
                status_list.append(message)
                i += 1

            # 'change password p s'
            elif expect(i, tokens, 'CHANGE'):
                i += 1
                if not expect(i, tokens, 'PASSWORD'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                
                p = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'STRING'):
                    return ['{"status":"FAILED"}']
                    
                s = tokens[i][1]
                
                try:
                    message = database.change_password(user, p, s)
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']
                
                status_list.append(message)
                i += 1

            # 'append to x with <expr>'
            elif expect(i, tokens, 'APPEND'):
                i += 1
                if not expect(i, tokens, 'TO'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                    
                x = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'WITH'):
                    return ['{"status":"FAILED"}']

                i += 1
                
                try:
                    status, i, value = getExpr(i, tokens, user)
                
                    if not status:
                        return ['{"status":"FAILED"}']
                    
                    message = database.append_command(user, x, value)
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']                

                status_list.append(message)
                i += 1

            # 'local x = expr'
            elif expect(i, tokens, 'LOCAL'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                
                x = tokens[i][1]
                
                i += 1
                if not expect(i, tokens, 'EQUALS'):
                    return ['{"status":"FAILED"}']

                i += 1
                try:
                    status, i, value = getExpr(i, tokens, user)
                    
                    if not status:
                        return ['{"status":"FAILED"}']
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']
                     
                message = database.set_local(x, value)

                status_list.append(message)
                i += 1

            # 'foreach y in x replacewith <expr>'
            elif expect(i, tokens, 'FOR'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                    
                y = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'IN'):
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    return ['{"status":"FAILED"}']
                    
                x = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'REPLACE'):
                    return ['{"status":"FAILED"}']
                    
                i += 1
                
                try:
                    database.check_for_each(user, x, y)
                    the_list = database.get_identifier_value(user, x)
                    
                    if not isinstance(the_list, list):
                        return ['{"status":"FAILED"}']
                        
                    for j in range(0,len(the_list)):
                        database.temporary_set(user, y, the_list[j])
                        status, end_expr, value = getExpr(i, tokens, user)
                        if not status:
                            return ['{"status":"FAILED"}']
                        the_list[j] = value
                        
                    database.set_command(user, x, the_list)    
                        
                    database.temporary_remove(user, y)
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']               

                i = end_expr
                status_list.append('{"status":"FOREACH"}')
                i += 1

            # 'set delegation <tgt> q <right> -> p' or 'set x = <expr>'
            elif expect(i, tokens, 'SET'):
                i += 1
                if expect(i, tokens, 'DELEGATION'):
                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']
                        
                    target = tokens[i][1]

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']
                    
                    q = tokens[i][1]
                    
                    i += 1
                    if not expect(i, tokens, 'RIGHT') or not expect(i, tokens, 'APPEND'):
                        return ['{"status":"FAILED"}']
                        
                    right = tokens[i][1]    

                    i += 1
                    if not expect(i, tokens, 'ARROW'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        return ['{"status":"FAILED"}']

                    p = tokens[i][1]
                    
                    try:
                        message = database.set_delegation(user, q, right[0], target, p)
                    except ParseError:
                        return ['{"status":"FAILED"}']
                    except SecurityError:
                        return ['{"status":"DENIED"}']
                        
                    status_list.append(message)
                    i += 1

                elif expect(i, tokens, 'IDENTIFIER'):
                    x = tokens[i][1]
                    
                    i += 1
                    if not expect(i, tokens, 'EQUALS'):
                        return ['{"status":"FAILED"}']

                    i += 1
                    try:
                        status, i, value = getExpr(i, tokens, user)

                        if not status:
                            return ['{"status":"FAILED"}']
                        
                        message = database.set_command(user, x, value)
                    except ParseError:
                        return ['{"status":"FAILED"}']
                    except SecurityError:
                        return ['{"status":"DENIED"}']                            

                    status_list.append(message)
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
                if not expect(i, tokens, 'RIGHT') or not expect(i, tokens, 'APPEND'):
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
                    
                p = tokens[i][1]
                
                try:
                    message = database.default_delegator(user, p)
                except ParseError:
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    return ['{"status":"DENIED"}']

                status_list.append(message)
                i += 1

            elif i < len(tokens) and tokens[i][0] == 'END':
                i += 1
                if i != len(tokens):
                    return ['{"status":"FAILED"}']

            else:
                return ['{"status":"FAILED"}']

        return status_list
