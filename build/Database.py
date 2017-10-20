import copy

# read write append delegate  (rwad)
# TODO: RETURN STATUS CODES
""" TODO: functions to implement:

    create principal:            done
    change password:             done
    set (set_command):           started
    append (append_command):     not started
    local (local_commad):        not started
    foreach:                     not started
    set delegation:              started
    delete delegation:           not started
    default delegator:           done
"""
class Database:

    def __init__(self):
        self.user = {}
        self.var = {} # global variables only
        self.local = {} # local variables, clear after program
        
        self.default_delegator = None


    def default_delegator(self, caller, user):
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        if user not in self.user:
            raise ParseError("User to be set as default delegator does not exist.")
        
        self.default_delegator = {}
        self.default_delegator['r'] = copy.deepcopy(self.user[user]['r'])
        self.default_delegator['w'] = copy.deepcopy(self.user[user]['w'])
        self.default_delegator['a'] = copy.deepcopy(self.user[user]['a'])
        self.default_delegator['d'] = copy.deepcopy(self.user[user]['d'])
        
        return '{"status":"DEFAULT_DELEGATOR"}'

    
    def create_principal(self, caller, new_user, password):
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        
        if new_user in self.user:
            raise ParseError("Principal of name " + new_user + " already exists.")
        
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
        if caller != "admin" and user != caller:
            raise SecurityError("Only admins can change other user's password")
        if user not in self.user:
            raise ParseError("User does not exist")
        
        self.user[user]["password"] = password
        
        return '{"status":"CHANGE_PASSWORD"}'
        
    # set is a keyword in python actually
    def set_command(self, caller, var_name, value):
        # i am not sure, does the user always have rights to local variables? 
    
        return '{"status":"SET"}'
        
    def set_delegation(self, caller, right, target, user_getting_rights):
        if user_getting_rights not in self.user or caller not in self.user:
            raise ParseError("Caller and user getting  rights must exist.")
        
        if target == "all":
            pass #welp
        
        else: # set a specific right
        # make sure caller has the right
            pass
        # ill do it on sunday 
        
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

    # helper function, call after everyloop
    def clear_local(self):
        del(self.local)