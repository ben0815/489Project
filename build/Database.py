import copy
from Error import ParseError
from Error import SecurityError

# read write append delegate  (rwad)
# TODO: RETURN STATUS CODES
""" TODO: functions to implement:
    create principal:            done
    change password:             done
    set (set_command):           started
    append (append_command):     started
    local (local_commad):        done (See Note)
    foreach:                     started
    set delegation:              done
    delete delegation:           not started
    default delegator:           done
"""
class Database:

    def __init__(self):
        self.user = {}
        self.user['admin'] = {}
        self.user['admin']['password'] = 'admin'
        self.var = {} # global variables only
        self.local = {} # local variables, clear after program
        
        self.default_delegator = None

    def default_delegator(self, caller, user):
        if user not in self.user:
            raise ParseError("User to be set as default delegator does not exist.")
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        
        self.default_delegator = {}
        self.default_delegator['r'] = copy.deepcopy(self.user[user]['r'])
        self.default_delegator['w'] = copy.deepcopy(self.user[user]['w'])
        self.default_delegator['a'] = copy.deepcopy(self.user[user]['a'])
        self.default_delegator['d'] = copy.deepcopy(self.user[user]['d'])
        
        return '{"status":"DEFAULT_DELEGATOR"}'
    
    def as_principal(self, caller, password):
        if caller not in self.user:
            raise ParseError("Principal: " + caller + " does not exist.")
        
        if password != self.user[caller]['password']:
            raise SecurityError("Invalid password.")    
    
    def create_principal(self, caller, new_user, password):
        if new_user in self.user:
            raise ParseError("Principal of name " + new_user + " already exists.")
            
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        
        self.user[new_user] = {}
        
        self.user[new_user]["password"] = password
        
        if self.default_delegator is None:
            self.user[new_user]["r"] = set()
            self.user[new_user]["w"] = set()
            self.user[new_user]["a"] = set()
            self.user[new_user]["d"] = set()
        else:
            self.user[new_user]["r"] = copy.deepcopy(self.default_delegator['r'])
            self.user[new_user]["w"] = copy.deepcopy(self.default_delegator['w'])
            self.user[new_user]["a"] = copy.deepcopy(self.default_delegator['a'])
            self.user[new_user]["d"] = copy.deepcopy(self.default_delegator['d'])
            
        return '{"status":"CREATE_PRINCIPAL"}'
        
    def change_password(self, caller, user, password):
        if user not in self.user:
            raise ParseError("User does not exist")
            
        if caller != "admin" and user != caller:
            raise SecurityError("Only admins can change other user's password")
        
        self.user[user]["password"] = password
        
        return '{"status":"CHANGE_PASSWORD"}'
        
    # set is a keyword in python actually
    def set_command(self, caller, var_name, value):
        if caller != 'admin' and var_name in self.var and var_name not in self.user[caller]['w']:
            raise SecurityError("No write permission")
             
        if var_name not in self.local and var_name not in self.var:
            self.var[var_name] = value
            if caller != 'admin':
                self.user[caller]['r'].add(var_name)
                self.user[caller]['w'].add(var_name)
                self.user[caller]['a'].add(var_name)
                self.user[caller]['d'].add(var_name)
        elif var_name in self.local:
            self.local[var_name] = value
        elif var_name in self.var:
            self.var[var_name] = value
    
        return '{"status":"SET"}'
        
    def set_delegation(self, caller, user_giving_rights, right, target, user_getting_rights):
        if user_getting_rights not in self.user or user_giving_rights not in self.user:
            raise ParseError("Caller and user getting rights must exist.")
        if target != 'all':
            if target in self.local:
                raise ParseError("target must not be a local variable")
            if target not in self.var:
                raise ParseError("target must exist")
                
        if caller != user_giving_rights and caller != "admin":
            raise SecurityError("Caller must be admin or the user user_giving_rights")
            
        if target != 'all' and caller == user_giving_rights:
            if target not in self.user[caller]['d']:
               raise SecurityError("user_giving_rights does not have delegation power") 

        if target == "all":
            for item in self.user[user_giving_rights]['d']:
                self.user[user_getting_rights][right].add(item) # should I check to see if right is rwad,or is this already done?

        else: # set a specific right
            self.user[user_getting_rights][right].add(target)
        
        return '{"status":"SET_DELEGATION"}'

    # delete del
    def delete_delegation(self, caller, user_taking_rights, right, target, user_losing_rights):
        if user_losing_rights not in self.user or user_taking_rights not in self.user:
            raise ParseError("Delete_del: Caller and user losing rights must exist")

        if target != 'all' and target not in self.var:
            raise ParseError("Delete_del: target not in global")

        if target != 'all' and target in self.local:
            raise ParseError("Delete_del: target exists in local")
            
        if caller != user_taking_rights and caller != "admin" and caller != user_losing_rights:
            raise SecurityError("Caller must be admin or user losing or taking rights")
            
        if caller == user_taking_rights and target != 'all':
            if target not in self.user[caller]['d']:
               raise SecurityError("user_taking_rights does not have delegation power")
        
        if target == "all":
            for item in self.user[user_taking_rights]['d']:
                self.user[user_losing_rights][right].discard(item)

        else:
            self.user[user_getting_rights][right].discard(target)    
        
        
        # all users or single user
        if user_losing_rights == "anyone":
            pass
        else:
            pass
            
        return '{"status":"DELETE_DELEGATION"}'

    # local
    # NOTE: possibly need to check if user has permission to read existing...
    # Cont: would be possible to local x = some_file which you dont have read access to...
    # Cont: then read x. But this isnt in specification.
    def set_local(self, new_var, value):
        # Check if new_var exists
        if new_var in self.local or new_var in self.var:
            raise ParseError("Local: new_var already exists")

        self.local[new_var] = value
                
        return '{"status":"LOCAL"}'

    # foreach (element y) in (list x) replacewith <expr>
    def for_each(self, caller, element, list_name, expr):
        if list_name not in self.var and list_name not in self.local:
            raise ParseError("List doesn't exist.")
        
        if caller != 'admin' and (list_name not in self.user[caller]['w'] or list_name not in self.user[caller]['r']):
            raise SecurityError("User can't for each.")
            
        if element in self.var or element in self.local:
            raise ParseError("Element already exists.")
            
        the_list = None
        
        if list_name in self.var:
            the_list = self.var[list_name]
        else:
            the_list = self.local[list_name]
            
        if not isinstance(the_list, list):
           raise ParseError("Not a list")
           
        
    # parser will call htis function with the value the expr evaluate
    def append_command(self, caller, list_name, expr): 
        if list_name not in self.var and list_name not in self.local:
            raise ParseError("List doesn't exist.")
        
        if caller != 'admin' and list_name not in self.user[caller]['w'] and list_name not in self.user[caller]['a']:
            raise SecurityError("User can't append.")
        
        the_list = None
        
        if list_name in self.var:
            the_list = self.var[list_name]
        else:
            the_list = self.local[list_name]
            
        if not isinstance(the_list, list):
           raise ParseError("Not a list")
           
        if isinstance(expr, list):
            the_list = the_list + expr
            if list_name in self.var:
                self.var[list_name] = the_list
            else:
                self.local[list_name] = the_list
        else:
            the_list.append(expr)
            if list_name in self.var:
                self.var[list_name] = the_list
            else:
                self.local[list_name] = the_list
       
        return '{"status":"APPEND"}'

    # helper function 
    def get_table(self, var_name):
        if var_names in self.local:
            return self.local
        elif var_names in self.var:
            return self.var
        else:
            return None

    # helper function
    def get_val(self, var_name):
        if var_names in self.local:
            return self.local[var_name]
        elif var_names in self.var:
            return self.var[var_name]
        else:
            return None
    
    # give value to parser
    def get_identifier_value(self, caller, identifier):
        if identifier not in self.local and identifier not in self.var:
            raise ParseError("Doesn't exist")
        elif caller != 'admin' and identifier not in self.user[caller]['r']:
            raise SecurityError("Caller cannot read that variable")
        
        if identifier in self.var:
            return self.var[identifier]
        else:
            return self.local[identifier]
    
    # give value of x.y to parser        
    def get_record_value(self, caller, record, value):
        if record not in self.local and record not in self.var:
            raise ParseError("Doesn't exist")
        elif caller != 'admin' and record not in self.user[caller]['r']:
            raise SecurityError("Caller cannot read that variable") 
         
        variable = None 
            
        if record in self.var:
            variable = self.var[record]
        else:
            variable = self.local[record]
            
        if not isinstance(variable, dict):
           raise ParseError("Not a record")
        
        if value not in variable:
            raise ParseError("Record does not have the value.")
            
        return variable[value]
    
    # used to check the specifics of foreach call   
    def check_for_each(self, caller, x, y):
        if x not in self.var and x not in self.local:
            raise ParseError("List doesn't exist.")
        
        if caller != 'admin' and (x not in self.user[caller]['w'] or x not in self.user[caller]['r']):
            raise SecurityError("User can't for each.")
            
        if y in self.var or y in self.local:
            raise ParseError("Element already exists.")
            
    def temporary_set(self, caller, y, value):
        self.local[y] = value
                
    def temporary_remove(self, caller, y):
        del self.local[y]
    
    # helper function, call after everyloop
    def clear_local(self):
        del(self.local)
