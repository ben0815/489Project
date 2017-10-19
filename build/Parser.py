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


def getValue(i, tokens):
        if i < len(tokens) and tokens[i][0] == 'IDENTIFIER':
            x = tokens[i][1]
            i += 1
            if i < len(tokens) and tokens[i][0] == 'DOT':
                i += 1
                # x.y
                if i < len(tokens) and tokens[i][0] == 'IDENTIFIER':
                    y = tokens[i][1]
                    i += 1
                    return True, i, x + '.' + y
                else:
                    return False, i, None
            # x
            elif i < len(tokens) and tokens[i][0] == 'NEWLINE':
                i += 1
                return True, i, x
            elif i < len(tokens) and tokens[i][0] == 'COMMA':
                i += 1
                return True, i, x
            elif i < len(tokens) and tokens[i][0] == 'RPAR':
                return True, i, x
            else:
                return False, i, None
        # s
        elif i < len(tokens) and tokens[i][0] == 'STRING':
            s = tokens[i][1]
            i += 1
            return True, i, s
        else:
            return False, i, None

def getFieldVals(i, tokens):
    value = ''
    i += 1
    while i < len(tokens):
        if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
            return False, i, None
        i += 1
        if i < len(tokens) and tokens[i][0] != 'EQUALS':
            return False, i, None
        i += 1
        status, i, temp = getValue(i, tokens)

        if not status:
            return False, i, None
        
        value += temp
        
        if i < len(tokens) and tokens[i][0] == 'RPAR':
            if (i + 1) < len(tokens) and tokens[i + 1][0] != 'NEWLINE':
                return False, i, None
            else:
                i += 1
                return True, i, value
    
    return False, i, None 
        
            
def getExpr(i, tokens):
    if i < len(tokens) and tokens[i][0] == 'LBRACK':
        i += 1
        if i < len(tokens) and tokens[i][0] != 'RBRACK':
            return False, i, None
        i += 1
        return True, i, 'LIST'
    elif i < len(tokens) and (tokens[i][0] == 'IDENTIFIER' or tokens[i][0] == 'STRING'):
        return getValue(i, tokens)
    elif i < len(tokens) and tokens[i][0] == 'LPAR':
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
                        print('FAILED')
                        return

                i += 1
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
    @staticmethod
    def parse(command):
        status_list = []
        tokens = lexer(command)
        # Remove the first element (guaranteed to be NEWLINE token)
        tokens.pop(0)
        # Check that first line is 'as principal p password s do \n'
        if not (len(tokens) > 6 and tokens[0][0] == 'AS' and tokens[1][0] == 'PRINCIPAL' and tokens[2][0] == 'IDENTIFIER' and tokens[3][0] == 'PASSWORD' and tokens[4][0] == 'STRING' and tokens[5][0] == 'DO' and tokens[6][0] == 'NEWLINE'):
            status_list.append('{"status":"FAILED"}')
            return status_list
        
        # Check that the last line is '***'
        if tokens[len(tokens) - 1 ][0] != 'END':
            status_list.append('{"status":"FAILED"}')
            return status_list
            
        # Now execute the commands
        i = 7
        while i < len(tokens):
            if tokens[i][0] == 'NEWLINE':
                i += 1
                continue
                
            # 'exit \n' command
            # TODO: exit security
            if tokens[i][0]  == 'EXIT':
                if (i + 1) < len(tokens) and tokens[i + 1][0] == 'NEWLINE':
                    status_list.append('{"status":"EXITING"}')
                    return status_list
                else:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
            
            # 'return <expr> \n' command
            if tokens[i][0] == 'RETURN':
                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                else:
                    status_list.append('{"status":"RETURNING","output":"' + value + '"}')    
                            
            # 'create principal p s'
            elif i < len(tokens) and tokens[i][0] == 'CREATE':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'PRINCIPAL':         
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                if i < len(tokens) and tokens[i][0] != 'STRING':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                status_list.append('{"status":"CREATE_PRINCIPAL"}')   
                i += 1
                        
            # 'change password p s'
            elif i < len(tokens) and tokens[i][0] == 'CHANGE':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'PASSWORD':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'STRING':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                status_list.append('{"status":"CHANGE_PASSWORD"}')   
                i += 1
                
            # 'append to x with <expr>'
            elif i < len(tokens) and tokens[i][0] == 'APPEND':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'TO':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                if i < len(tokens) and tokens[i][0] != 'WITH':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list 
                
                status_list.append('{"status":"APPEND"}')   
                
                
            # 'local x = expr'
            elif i < len(tokens) and tokens[i][0] == 'LOCAL':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'EQUALS':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list    
                
                status_list.append('{"status":"LOCAL"}')   
                
            # 'foreach y in x replacewith <expr>'
            elif i < len(tokens) and tokens[i][0] == 'FOR':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                     
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IN':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                   
                i += 1
                if i < len(tokens) and tokens[i][0] != 'REPLACE':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                status, i, value = getExpr(i, tokens)
                if not status:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                        
                status_list.append('{"status":"FOREACH"}')   
                
            # 'set delegation <tgt> q <right> -> p' or 'set x = <expr>'
            elif i < len(tokens) and tokens[i][0] == 'SET':
                i += 1
                if i < len(tokens) and tokens[i][0] == 'DELEGATION':
                    i += 1
                    if i < len(tokens) and (tokens[i][0] != 'IDENTIFIER' and tokens[i][0] != 'ALL'):
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
                    
                    i += 1
                    if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
 
                    i += 1
                    if i < len(tokens) and tokens[i][0] != 'RIGHT':
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
                       
                    i += 1
                    if i < len(tokens) and tokens[i][0] != 'ARROW':
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
                        
                    i += 1
                    if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
                    
                    status_list.append('{"status":"SET_DELEGATION"}')   
                    i += 1              
                elif i < len(tokens) and tokens[i][0] == 'IDENTIFIER':
                    i += 1
                    if i < len(tokens) and tokens[i][0] != 'EQUALS':
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list
                    
                    i += 1
                    status, i, value = getExpr(i, tokens)

                    if not status:
                        status_list = []
                        status_list.append('{"status":"FAILED"}')
                        return status_list 

                    status_list.append('{"status":"SET"}')   
                else:
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
            # 'delete delegation <tgt> q <right> -> p'
            elif i < len(tokens) and tokens[i][0] == 'DELETE':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'DELEGATION':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                
                i += 1
                if i < len(tokens) and (tokens[i][0] != 'IDENTIFIER' or tokens[i][0] != 'ALL'):
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                        
                i += 1
                if i < len(tokens) and tokens[i][0] != 'RIGHT':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                        
                i += 1
                if i < len(tokens) and tokens[i][0] != 'ARROW':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                        
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
                status_list.append('{"status":"DELETE_DELEGATION"}')   
                i += 1
                
            # 'default delegator = p'  
            elif i < len(tokens) and tokens[i][0] == 'DEFAULT':
                i += 1
                if i < len(tokens) and tokens[i][0] != 'DELEGATOR':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
                i += 1
                if i < len(tokens) and tokens[i][0] != 'EQUALS':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
                i += 1
                if i < len(tokens) and tokens[i][0] != 'IDENTIFIER':
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
                    
                status_list.append('{"status":"DEFAULT_DELEGATOR"}')   
                i += 1
            elif i < len(tokens) and tokens[i][0] == 'END':
                i += 1
                if i != len(tokens):
                    status_list = []
                    status_list.append('{"status":"FAILED"}')
                    return status_list
            else:
                status_list = []
                status_list.append('{"status":"FAILED"}')
                return status_list   
        return status_list 


