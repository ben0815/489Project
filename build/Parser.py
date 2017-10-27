import re
import json
from Error import ParseError
from Error import SecurityError
from Database import Database
import collections

token_map = {'principal' : 'PRINCIPAL', 'as' : 'AS', 'password' : 'PASSWORD', 'do' : 'DO',
      '***' : 'END', 'exit' : 'EXIT', 'return' : 'RETURN', '{' : 'LPAR', '}' : 'RPAR',
      '[' : 'LBRACK', ']' : 'RBRACK', 'create' : 'CREATE', 'change' : 'CHANGE', 'password' :
      'PASSWORD', 'set' : 'SET', 'append' : 'APPEND', 'to' : 'TO', 'with' : 'WITH', '=' :
      'EQUALS', '.' : 'DOT', ',' : 'COMMA', '->' : 'ARROW', 'local' : 'LOCAL', 'foreach' :
      'FOR', 'in' : 'IN', 'replacewith' : 'REPLACE', 'delegation' : 'DELEGATION', 'delete' :
      'DELETE', 'default' : 'DEFAULT', 'read' : 'RIGHT', 'write' : 'RIGHT', 'delegate' : 'RIGHT', 'all' : 'ALL', 'delegator' : 'DELEGATOR'}

punctuation = ['=', '[', ']', '.', '-', '>', '{', '{', ',']

def isStringFormat(value):
    if len(value) > 65535: # max length
        return False
    if re.match('^\"[A-Za-z0-9_ ,;\.?!-]*\"$', value) is None: # reasonably tested, could test more
        return False
    return True

def isIdentifierFormat(value):
    if str in token_map: # cannot be the same as a key word
        return False
    if len(value) > 255: # max length
        return False
    if re.match('^[A-Za-z][A-Za-z0-9_]*$', value) is None: # reasonably tested, could test more
        return False
    return True

def isCommentFormat(value):
    if re.match('^//[A-Za-z0-9_ ,;\.?!-]*$', value) is None:
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
                if not expect((i + 1), tokens, 'NEWLINE'):
                    i += 1
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
    values = collections.OrderedDict()
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
        
        if isinstance(temp, list) or isinstance(temp, collections.OrderedDict):
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
        
        if 1 < len(line) and line[i + 1] == '/' and line[i] == '/':
            continue
            
        while i < len(line):
            if line[i] != ' ':
                break
            else:
                i += 1
                
        if (i + 1) < len(line) and line[i + 1] == '/' and line[i] == '/':
            raise ParseError("Comments on their own line must not be preceded by whitespace.")
        
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
    def set_password(password):
        if not isStringFormat('"' + password + '"'):
            raise ParseError
        else:
            database.set_admin_password(password)
            
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
                database.roll_back()
                return ['{"status":"FAILED"}']

            i += 1
            # 'create principal p s'
            if expect(i, tokens, 'CREATE'):
                i += 1
                if not expect(i, tokens, 'PRINCIPAL'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                
                p = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'STRING'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                s = tokens[i][1]
                
                try:
                    message = database.create_principal(user, p, s)
                except ParseError:
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    database.roll_back()
                    return ['{"status":"DENIED"}']
                
                status_list.append(message)
                i += 1

            # 'change password p s'
            elif expect(i, tokens, 'CHANGE'):
                i += 1
                if not expect(i, tokens, 'PASSWORD'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                
                p = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'STRING'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                s = tokens[i][1]
                
                try:
                    message = database.change_password(user, p, s)
                except ParseError as e:
                    print(str(e))
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError as e:
                    print(str(e))
                    database.roll_back()
                    return ['{"status":"DENIED"}']
                
                status_list.append(message)
                i += 1

            # 'append to x with <expr>'
            elif expect(i, tokens, 'APPEND'):
                i += 1
                if not expect(i, tokens, 'TO'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                x = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'WITH'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                
                try:
                    database.check_append_permission(user, x)
                    
                    status, i, value = getExpr(i, tokens, user)
                
                    if not status:
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                        
                    message = database.append_command(user, x, value)
                except ParseError as e:
                    print(str(e))
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError as e:
                    print(str(e))
                    database.roll_back()
                    return ['{"status":"DENIED"}']                

                status_list.append(message)
                i += 1

            # 'local x = expr'
            elif expect(i, tokens, 'LOCAL'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                
                x = tokens[i][1]
                
                i += 1
                if not expect(i, tokens, 'EQUALS'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                try:
                    status, i, value = getExpr(i, tokens, user)
                    
                    if not status:
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                        
                    message = database.set_local(x, value)
                except ParseError:
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    database.roll_back()
                    return ['{"status":"DENIED"}']

                status_list.append(message)
                i += 1

            # 'foreach y in x replacewith <expr>'
            elif expect(i, tokens, 'FOR'):
                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                y = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'IN'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                x = tokens[i][1]

                i += 1
                if not expect(i, tokens, 'REPLACE'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                i += 1
                
                try:
                    database.check_for_each(user, x, y)
                    the_list = database.get_identifier_value(user, x)
                    
                    if not isinstance(the_list, list):
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                        
                    for j in range(0,len(the_list)):
                        database.temporary_set(user, y, the_list[j])
                        status, end_expr, value = getExpr(i, tokens, user)
                        if not status:
                            database.roll_back()
                            return ['{"status":"FAILED"}']
                            
                        if isinstance(value, list):
                            database.roll_back()
                            return ['{"status":"FAILED"}']
                            
                        the_list[j] = value
                        
                    database.set_command(user, x, the_list)    
                        
                    database.temporary_remove(user, y)
                except ParseError:
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    database.roll_back()
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
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                        
                    target = tokens[i][1]

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                    
                    q = tokens[i][1]
                    
                    i += 1
                    if not expect(i, tokens, 'RIGHT') and not expect(i, tokens, 'APPEND'):
                        database.roll_back()
                        print("T")
                        return ['{"status":"FAILED"}']
                        
                    right = tokens[i][1]    

                    i += 1
                    if not expect(i, tokens, 'ARROW'):
                        database.roll_back()
                        return ['{"status":"FAILED"}']

                    i += 1
                    if not expect(i, tokens, 'IDENTIFIER'):
                        database.roll_back()
                        return ['{"status":"FAILED"}']

                    p = tokens[i][1]
                    
                    try:
                        message = database.set_delegation(user, q, right[0], target, p)
                    except ParseError as e:
                        print(str(e))
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                    except SecurityError as e:
                        print(str(e))
                        database.roll_back()
                        return ['{"status":"DENIED"}']
                        
                    status_list.append(message)
                    i += 1

                elif expect(i, tokens, 'IDENTIFIER'):
                    x = tokens[i][1]
                    
                    i += 1
                    if not expect(i, tokens, 'EQUALS'):
                        database.roll_back()
                        return ['{"status":"FAILED"}']

                    i += 1
                    try:
                        status, i, value = getExpr(i, tokens, user)

                        if not status:
                            database.roll_back()
                            print("TEST")
                            return ['{"status":"FAILED"}']
                        
                        message = database.set_command(user, x, value)
                    except ParseError as e:
                        print(str(e))
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                    except SecurityError as e:
                        print(str(e))
                        database.roll_back()
                        return ['{"status":"DENIED"}']                            

                    status_list.append(message)
                    i += 1

                else:
                    database.roll_back()
                    return ['{"status":"FAILED"}']

            # 'delete delegation <tgt> q <right> -> p'
            elif expect(i, tokens, 'DELETE'):
                i += 1
                if not expect(i, tokens, 'DELEGATION'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'RIGHT') and not expect(i, tokens, 'APPEND'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'ARROW'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                status_list.append('{"status":"DELETE_DELEGATION"}')
                i += 1

            # 'default delegator = p'
            elif expect(i, tokens, 'DEFAULT'):
                i += 1
                if not expect(i, tokens, 'DELEGATOR'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'EQUALS'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']

                i += 1
                if not expect(i, tokens, 'IDENTIFIER'):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                    
                p = tokens[i][1]
                
                try:
                    message = database.set_default_delegator(user, p)
                except ParseError:
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    database.roll_back()
                    return ['{"status":"DENIED"}']

                status_list.append(message)
                i += 1
            
            # 'exit \n' command
            # TODO: exit security
            elif expect(i, tokens, 'EXIT'):
                i += 1
                
                if not expect(i, tokens, 'NEWLINE'):
                    return ['{"status":"FAILED"}']                     
                
                i += 1    
                if not expect(i, tokens, 'END'):
                    return ['{"status":"FAILED"}']       
                
                i += 1
                
                if i != len(tokens):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                
                if user != "admin":
                    return ['{"status":"DENIED"}']
                
                status_list.append('{"status":"EXITING"}')

            # 'return <expr> \n' command
            elif expect(i, tokens, 'RETURN'):
                i += 1
                
                try:
                    status, i, value = getExpr(i, tokens, user)

                    if not status:
                        database.roll_back()
                        return ['{"status":"FAILED"}']
                except ParseError:
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                except SecurityError:
                    database.roll_back()
                    return ['{"status":"DENIED"}']
                i += 1    
                if not expect(i, tokens, 'NEWLINE'):
                    return ['{"status":"FAILED"}']                     
                
                i += 1    
                if not expect(i, tokens, 'END'):
                    return ['{"status":"FAILED"}']       
                
                i += 1
                
                if i != len(tokens):
                    database.roll_back()
                    return ['{"status":"FAILED"}']
                if isinstance(value, str):
                    status_list.append('{"status":"RETURNING","output":"' + str(value) + '"}')
                else:
                    status_list.append('{"status":"RETURNING","output":"' + json.dumps(value) + '"}')

            else:
                database.roll_back()
                return ['{"status":"FAILED"}']
        
        database.clear_local()
        return status_list
