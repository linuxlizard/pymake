# davep 20-Mar-2016 ; symbol table

import os
import logging
import collections

from symbol import Symbol
from flatten import flatten

logger = logging.getLogger("pymake.symtable")

#_fail_on_undefined = True
_fail_on_undefined = False


# template for vars saved in SymbolTable
_entry_template = {
    "name" : None,
    "value" : None,
    "origin" : None,  # see origin() ; used with env var override and $(foreach)
    "pos" : None,  # filename/position where last set
    "flags" : 0
}

FLAG_NONE = 0
FLAG_READ_ONLY = 1

class SymbolTable(object):
    def __init__(self):
        # key: variable name
        # value: _entry_template dict instance
        self.symbols = {}

        # push/pop a name/value so $(foreach) (and other functions) can re-use
        # the var name (and we don't have to make a complete new copy of a
        # symbol table just to save/restore a single var)
        self.stack = {}

        self._init_builtins()

    def _init_builtins(self):
        entry = dict(_entry_template)
        entry['name'] = '.VARIABLES'
        entry['origin'] = 'default'
        entry['flags'] = FLAG_READ_ONLY
        self.symbols[entry['name']] = entry

        self.built_ins = {
            ".VARIABLES" : self.variables,
        }
        

    def add(self, name, value, pos=None):
        logger.debug("%s store \"%s\"=\"%s\"", self, name, value)

        # an attempt to store empty string is a bug
        assert isinstance(name,str), type(name)
        if not len(name):
            breakpoint()
        assert len(name)

        # sanity check for bad names XXX add more cases
        # (will hit this if my tokenparser is screwing up)
        assert ' ' not in name, name

#        breakpoint()
#        assert isinstance(value,Symbol), type(value)

        # make a new symtable from the template
        try:
            entry = self.symbols[name]
        except KeyError:
            entry = dict(_entry_template)
            entry['name'] = name
            # TODO this can change when I implement 'override'
            entry['origin'] = 'file'

        # XXX not sure read-only is a good idea yet
        if entry['flags'] & FLAG_READ_ONLY:
            raise PermissionDenied

        if pos:
            entry['pos'] = pos
        entry['value'] = value

        self.symbols[name] = entry

    def _maybe_eval(self, entry):
        value = entry['value']

        # handle the case where an expression is stored in the symbol table vs
        # a value 
        # e.g.,  a=10  (evaluated whenever $a is used)
        # vs   a:=10  (evaluated immediately and "10" stored in symtable)
        #
        if isinstance(value,Symbol):
            step1 = [t.eval(self) for t in value]
            return "".join(step1)

        return value

    def fetch(self, key):
        # now try a var lookup 
        # Will always return an empty string on any sort of failure. 
        logger.debug("fetch key=\"%r\"", key)
#        print("fetch key=\"%r\"" % key)

        assert isinstance(key,str), type(key)
        assert len(key)  # empty key bad

        # built-in variable ?
        try:
            return self.built_ins[key](key)
        except KeyError:
            pass

        try:
#            print("fetch value=\"%r\"" % self.symbols[key])
            return self._maybe_eval(self.symbols[key])
        except KeyError:
            if _fail_on_undefined:
                raise

        # TODO read gnu make manual on how env vars are referenced
        logger.debug("sym=%s not in symbol table", key)

        # try environment
        value = os.getenv(key)
        if value is None:
            return ""
        logger.debug("sym=%s found in environ", key)
        return value


    def push(self, name):
        # save current value of 'name' in secure, undisclosed location

        # don't use self.fetch() because will eval the var which could lead to
        # side effects
        if name in self.symbols:
            entry = self.symbols[name]
            # remove the other reference (otherwise 'add' will just update the
            # self.symbols[name] entry which also points to our stack entry)
            del self.symbols[name]
        else:
            # no var with this name.
            # could still be an env var.
            value = os.getenv(name)
            if value is None:
                # nothing to save
                return
            entry = dict(_entry_template)
            entry['origin'] = 'environment'
            entry['name'] = name
            
        # create the dequeue if doesn't exist
        if not name in self.stack:
            self.stack[name] = collections.deque()

        # push right, pop right (stack)
        logger.debug("push entry=%s", entry['name'])
        self.stack[name].append(entry)

    def pop(self, name):
        # restore previous value of 'name' from the secure, undisclosed location

        # push right, pop right (stack)
        # allow KeyError and IndexError to propagate (indicates a bug in the
        # calling code)
        logger.debug("pop name=%s", name)

        # The stack will contain values previously in the symbol table.
        # If there was no previous value in the symbol table, there will be no
        # entry for it in the stack. In this case, just delete the value from
        # the symbol table.
        # For example, the $(call) function will push each arg $1 $2 $3 $4 etc
        # then pop them after the call.  Very likely $1 $2 $3, etc, are not in
        # the symbol table originally.
        try:
            entry = self.stack[name].pop()
        except KeyError:
            # allow KeyError to propagate if the name doesn't exist in the
            # self.symbols{} because that would be a bug  (this might change in
            # the future)
            del self.symbols[name]
            return

        # TODO future memory optimization would be to delete the dequeue from
        # self.stack when empty

        # if it's not an env var, restore previous value 
        if entry['origin'] == 'environment':
            del self.symbols[name]
        else:
            # restore previous value
            self.symbols[name] = entry

    def flavor(self, name):
        # Support for the $(flavor) function
        #
        # undefined
        # recursive
        # simple

        # don't use self.fetch() because will eval the var which could lead to
        # side effects
        try :
            value = self.symbols[name]
            return "recursive" if isinstance(value,Symbol) else "simple"
        except KeyError:
            pass

        # check for env vars
        value = os.getenv(name)
        if value is None:
            return "undefined"

        # TODO dig into gnu make code, learn why env vars return "recursive"
        return "recursive"

    def origin(self, name):
        # support for the $(origin) function

        # don't use self.fetch() because will eval the var which could lead to
        # side effects

        # undefined
        # default TODO
        # environment
        # environment override TODO
        # file 
        # command line  TODO
        # override -- override directive TODO
        # automatic -- defined in a rule e.g., $@ TODO

        try :
            entry = self.symbols[name]
            assert entry["origin"] is not None, name
            return entry["origin"]
        except KeyError:
            pass

        value = os.getenv(name)
        if value is None:
            return "undefined"

        return "environment"

    def value(self, name):
        # support for the $(value) function

        # don't use self.fetch() because will eval the var which could lead to
        # side effects

        try :
            entry = self.symbols[name]
            value = entry['value']
            if isinstance(value,Symbol):
                return value.makefile()
            return value
        except KeyError:
            pass

    def variables(self, _):
        # return $(.VARIABLES)
        return " ".join(self.symbols.keys())

    def is_defined(self, name):
        # is this varname in our symbol table (or other mechanisms)

        return name in self.built_ins or\
            name in self.symbols or\
            os.getenv(name) is not None
        
