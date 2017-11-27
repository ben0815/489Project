import copy
from Error import ParseError
from Error import SecurityError
import collections

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
        self.user['anyone'] = {}
        self.user['anyone']['password'] = '#'
        self.user['anyone']['r'] = set()
        self.user['anyone']['w'] = set()
        self.user['anyone']['a'] = set()
        self.user['anyone']['d'] = set()
        self.var = {} # global variables only
        self.local = {} # local variables, clear after program
        self.security_stack = []
        
        # state dictionaries are used to store the state of the program when a command is being run
        # at rollback just set user, var to their initial states
        self.user_state = {}
        self.var_state = {}
        self.delegator_state = "anyone"
        
        self.default_delegator = "anyone"
        
    def set_admin_password(self, password):
        self.user['admin']['password'] = password

    def set_default_delegator(self, caller, name):
        if name not in self.user:
            raise ParseError("User to be set as default delegator does not exist.")
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        
        self.default_delegator = name
        
        return '{"status":"DEFAULT_DELEGATOR"}'
    
    def as_principal(self, caller, password):
        if caller not in self.user:
            raise ParseError("Principal: " + caller + " does not exist.")
        
        if password != self.user[caller]['password']:
            raise SecurityError("Invalid password.")
        
        self.user_state = copy.deepcopy(self.user)
        self.var_state = copy.deepcopy(self.var)
        self.delegator_state = copy.deepcopy(self.default_delegator)
        self.security_stack_state = copy.deepcopy(self.security_stack) 
    
    def create_principal(self, caller, new_user, password):
        if new_user in self.user:
            raise ParseError("Principal of name " + new_user + " already exists.")
            
        if caller != "admin":
            raise SecurityError("To create a principal you must be admin.")
        
        self.user[new_user] = {}
        
        self.user[new_user]["password"] = password
        
        self.user[new_user]["r"] = set()
        self.user[new_user]["w"] = set()
        self.user[new_user]["a"] = set()
        self.user[new_user]["d"] = set()
        
        for delegate in self.user[self.default_delegator]['d']:
            self.user[new_user]["r"].add(delegate)
            self.user[new_user]["w"].add(delegate)
            self.user[new_user]["a"].add(delegate)
            self.user[new_user]["d"].add(delegate)   
            
        return '{"status":"CREATE_PRINCIPAL"}'
        
    def change_password(self, caller, user, password):
        if user not in self.user:
            raise ParseError("User does not exist")
            
        if caller != "admin" and user != caller:
            raise SecurityError("Only admins can change other user's password")
        
        self.user[user]["password"] = password
        
        return '{"status":"CHANGE_PASSWORD"}'

    # Check that a user has permission. That is: security stack has granted them the permission, and granting user has the permission.
    def check_permission(self, permission, name, element):
        for item in self.security_stack:
            if item[0] == element and item[2] == permission and item[3] == name:
                if item[1] == 'admin':
                    return True
                else:
                    return self.check_permission(permission, item[1], element)

        return False   

        
    # set is a keyword in python actually
    def set_command(self, caller, var_name, value):
        if caller != 'admin' and var_name in self.var and not self.check_permission('w', caller, var_name) and not self.check_permission('w', 'anyone', var_name):
            raise SecurityError("No write permission")
             
        if var_name not in self.local and var_name not in self.var:
            self.var[var_name] = value
            if caller != 'admin':
                self.set_delegation('admin', 'admin', 'r', var_name, caller)
                self.set_delegation('admin', 'admin', 'w', var_name, caller)
                self.set_delegation('admin', 'admin', 'a', var_name, caller)
                self.set_delegation('admin', 'admin', 'd', var_name, caller)
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
            
        if target != 'all' and caller == user_giving_rights and caller != 'admin':
            if target not in self.user[caller]['d']:
               raise SecurityError("user_giving_rights does not have delegation power") 

        if target == "all" and user_getting_rights != "admin":
            if caller == "admin":
                for item in self.var:
                    # Add this set delegation to the security stack
                    stack = [item, user_giving_rights, right, user_getting_rights]
                    self.security_stack.append(stack)
            else:
                for item in self.user[user_giving_rights]['d']:
                    # Add this set delegation to the security stack
                    stack = [item, user_giving_rights, right, user_getting_rights]
                    self.security_stack.append(stack)

        else: # set a specific right
            if user_getting_rights != 'admin':
                # Add this set delegation to the security stack
                stack = [target, user_giving_rights, right, user_getting_rights]
                self.security_stack.append(stack)
        
        return '{"status":"SET_DELEGATION"}'

    # check if a delete delegation is in the stack
    # return negative value if not in stack, index of assertion if in stack.
    def get_in_security_stack(self, target, taking, right, losing):
        for i in range(0, len(self.security_stack)):
            if target == self.security_stack[i][0] and taking == self.security_stack[i][1] and right == self.security_stack[i][2] and losing == self.security_stack[i][3]:
                return i

        return -1

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
            
        if caller == user_taking_rights and target != 'all' and caller != "admin":
            if target not in self.user[caller]['d']:
               raise SecurityError("user_taking_rights does not have delegation power")
        
        if target == "all" and user_losing_rights != "admin":
            if caller == "admin":
                for item in self.var:
                    index = self.get_in_security_stack(item, user_taking_rights, right, user_losing_rights)
                    if index > -1:
                        del self.security_stack[index]
            else:
                for item in self.user[user_taking_rights]['d']:
                    index = self.get_in_security_stack(item, user_taking_rights, right, user_losing_rights)
                    if index > -1:
                        del self.security_stack[index]

        else:
            if user_losing_rights != 'admin':
                index = self.get_in_security_stack(target, user_taking_rights, right, user_losing_rights)
                if index > -1:
                    del self.security_stack[index]
        
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
           
    # check permission of caller on list_name before evaluating expression
    def check_append_permission(self, caller, list_name):
        if list_name not in self.var and list_name not in self.local:
            raise ParseError("List doesn't exist.")
        
        if caller != 'admin' and list_name in self.var and not self.check_permission('w', caller, list_name) and not self.check_permission('w', 'anyone', list_name) and not self.check_permission('a', caller, list_name) and not self.check_permission('a', 'anyone', list_name):
            raise SecurityError("User can't append.")
        
        the_list = None
        
        if list_name in self.var:
            the_list = self.var[list_name]
        else:
            the_list = self.local[list_name]
            
        if not isinstance(the_list, list):
           raise ParseError("Not a list")
           
    def check_let(self, caller, variable):
        if variable in self.var or variable in self.local:
            raise ParseError("Variable already exists.")
        
    
    # parser will call this function with the value the expr evaluate
    def append_command(self, caller, list_name, expr): 
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
    
    # give value to parser
    def get_identifier_value(self, caller, identifier):
        if identifier not in self.local and identifier not in self.var:
            raise ParseError("Doesn't exist")
        elif caller != 'admin' and identifier in self.var and not self.check_permission('r', caller, identifier) and not self.check_permission('r', 'anyone', identifier):
            raise SecurityError("Caller cannot read that variable")
        
        if identifier in self.var:
            return copy.deepcopy(self.var[identifier])
        else:
            return copy.deepcopy(self.local[identifier])
    
    # give value of x.y to parser        
    def get_record_value(self, caller, record, value):
        if record not in self.local and record not in self.var:
            raise ParseError("Doesn't exist")
        elif caller != 'admin' and record in self.var and not self.check_permission('r', caller, record) and not self.check_permission('r', 'anyone', record):
            raise SecurityError("Caller cannot read that variable") 
         
        variable = None 
            
        if record in self.var:
            variable = self.var[record]
        else:
            variable = self.local[record]
            
        if not isinstance(variable, collections.OrderedDict):
            raise ParseError("Not a record")
        
        if value not in variable:
            raise ParseError("Record does not have the value.")
            
        return copy.deepcopy(variable[value])
    
    # used to check the specifics of foreach call   
    def check_for_each(self, caller, x, y):
        if x not in self.var and x not in self.local:
            raise ParseError("List doesn't exist.")
        
        if caller != 'admin' and x in self.var and (not self.check_permission('w', caller, x) or not self.check_permission('r', caller, x)) and (not self.check_permission('w', 'anyone', x) or not self.check_permission('r', 'anyone', x)):
            raise SecurityError("User can't for each.")
            
        if y in self.var or y in self.local:
            raise ParseError("Element already exists.")
            
    def temporary_set(self, caller, y, value):
        self.local[y] = value
                
    def temporary_remove(self, caller, y):
        del self.local[y]
    
    # helper function, call after everyloop
    def clear_local(self):
        self.local.clear()
        
    def roll_back(self):
        self.var = copy.deepcopy(self.var_state)
        self.user = copy.deepcopy(self.user_state)
        self.default_delegator = copy.deepcopy(self.delegator_state)
        self.security_stack = copy.deepcopy(self.security_stack_state)
        self.clear_local()
