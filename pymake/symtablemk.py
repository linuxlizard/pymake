# davep 20-Mar-2016 ; symbol table

import os
import logging
import collections
from enum import Enum

import pymake.version as version
import pymake.constants as constants
from pymake.symbolmk import Symbol
from pymake.error import warning_message, MakeError

logger = logging.getLogger("pymake.symtable")

#logger.setLevel(level=logging.INFO)

#_fail_on_undefined = True
_fail_on_undefined = False

class Export(Enum):
    # by default, var not exported
    NOEXPORT = 0

    # command line and env vars are always passed to submakes
    SUBMAKE = 1<<1

    # an 'export varname' statement exported this var
    # (immune to global 'unexport')
    EXPLICIT = 1<<2

    # a global 'export' exported this var
    # (will be undone by a global 'unexport')
    IMPLICIT = 1<<3
    
# classes for vars saved in SymbolTable
class Entry:
    origin = "(invalid origin)"
    never_export = False

    def __init__(self, name, value=None, pos=None):
        logger.debug("create var name=%s origin=%s pos=%r", name, self.origin, pos)
        self.name = name
        self._value = value
        self.pos = pos

        # I'm not sure this is a good idea yet.
#        self.read_only = False

        self._export = Export.NOEXPORT.value

        # handle appended expressions
        self._appends = []

        # check for recursive variable expansion attempting to expand itself
        self.loop = 0

    @property
    def export(self):
        return (not self.never_export) and (self._export != Export.NOEXPORT.value)

    def set_export(self, flag):
        if self.never_export:
            return

        self._export = self._export | flag.value

    def set_unexport(self, flag):
        if self.never_export:
            return

        self._export = self._export & ~flag.value
        

    @property
    def value(self):
        return self._value

    def set_value(self, value, pos):
        # TODO add a stack where the values get changed
        self.pos = pos
        self._value = value

    def sanity(self):
        # TODO
        pass

    def get_pos(self):
        return self.pos

    def eval(self, symbol_table):
        # handle the case where an expression is stored in the symbol table vs
        # a value 
        # e.g.,  a=10  (evaluated whenever $a is used)
        # vs   a:=10  (evaluated immediately and "10" stored in symtable)
        #
        if isinstance(self._value, Symbol):
            if self.name=='include':
                breakpoint()
            logger.debug("recursive eval %r name=%s at pos=%r", self, self.name, self.get_pos())
            if self.loop > 0:
                msg = "Recursive variable %r references itself (eventually)" % self.name
                raise MakeError(msg=msg, pos=self.get_pos())
            self.loop += 1
            step1 = [ self._value.eval(symbol_table) ]
            step1.extend( [t.eval(symbol_table) for t in self._appends] )
            self.loop -= 1
            return " ".join(step1)

        return self._value

    def append_recursive(self, value):
        # ha ha type checking
        assert isinstance(value,Symbol), type(value)

        return self._appends.append(value)

    def append(self, value, pos):
        # simple string append, space separated
        assert isinstance(value,str), type(value)
        self.set_value(self.value + " " + value, pos)

class FileEntry(Entry):
    origin = "file"

    def __init__(self, name, value, pos):
        if pos is None:
            # happens with test code
            pos = ("/dev/null", (0,0))
        super().__init__(name, value, pos)

    def sanity(self):
        assert self.pos is not None


# "if variable has a default definition, as is usual with CC and so on. See Section 10.3
# [Variables Used by Implicit Rules], page 119. Note that if you have redefined a
# default variable, the origin function will return the origin of the later definition."
# -- GNU Make manual  Version 4.3 Jan 2020
class DefaultEntry(Entry):
    origin = "default"
    never_export = True

class CallbackEntry(DefaultEntry):
    # Some built-in variables have complex requirements that can't be stored as
    # a simple string in the symbol table. For example .VARIABLES returns a
    # list of the variables currently defined.
    
    def __init__(self, name, callback_fn):
        super().__init__(name)

        # self.eval() will call this fn to get a value
        self._value = callback_fn

    def eval(self, symbol_table):
        return self._value(symbol_table)

# Environment Variables are higher precedence than File variables.  But Command
# Line args are higher precedence than Environment Variables.
# "By default, only variables that came from the environment or the
# command line are passed to recursive invocations."
# -- GNU Make manual  Version 4.3 Jan 2020
class EnvVarEntry(Entry):
    origin = "environment"

    def __init__(self, name, value):
        pos = ("environment",(0,0))
        super().__init__(name,value,pos)
        self.set_export( Export.SUBMAKE )

# Command line args are higher precedence than variables in the makefile except
# if the variable is marked with 'override'
#
# Command Line higher precedence than Environment
#
# "By default, only variables that came from the environment or the
# command line are passed to recursive invocations."
# -- GNU Make manual  Version 4.3 Jan 2020
class CommandLineEntry(Entry):
    origin = "command line"

    def __init__(self, name, value):
        super().__init__(name,value)
        self.set_export(Export.SUBMAKE)

    def set_value(self, value, pos):
        pass


class AutomaticEntry(Entry):
    origin = "automatic"
    never_export = True

    def __init__(self, name, value, pos):
        assert name in constants.automatic_variables, name
        super().__init__(name, value, pos)



class SymbolTable(object):
    def __init__(self, **kwargs):
        # key: variable name
        # value: _entry_template dict instance
        self.symbols = {}

        # push/pop a name/value so $(foreach) (and other functions) can re-use
        # the var name (and we don't have to make a complete new copy of a
        # symbol table just to save/restore a single var)
        self.stack = {}

        self.export_default_value = Export.NOEXPORT

        self.warn_undefined = kwargs.get("warn_undefined_variables", False)

        self._init_builtins()
        self._init_envvars()

        # This is an ugly hack to allow us to treat command line argument
        # expressions transparently as just another AssignmentExpression.
        # When evaluating command line statements, we'll set this flag which
        # will mark the incoming variables as from the command line.
        self.command_line_flag = False

    def _init_builtins(self):
        # key: var name
        # value: symbol table method to return values
        
        # TODO add more internal vars
        self._add_entry(CallbackEntry('.VARIABLES', self.variables))
        self._add_entry(DefaultEntry('MAKE_VERSION', version.Version.vstring()))

        # "Unlike most variables, the variable SHELL is never set from the environment."
        # -- 5.3.2 Choosing the Shell
        # GNU Make Manual Version 4.3 January 2020

        self._add_entry(DefaultEntry('SHELL', constants.DEFAULT_SHELL))
        self._add_entry(DefaultEntry('.SHELLFLAGS', constants.DEFAULT_SHELLFLAGS))

    def _init_envvars(self):
        # "Every environment variable that make sees when it starts up is
        # transformed into a make variable with the same name and value."
        # 6.10 Variables from the Environment
        # Page 72. GNU Make Version 4.3 January 2020.

        # read (almost) all env vars, add to symbol table
        # "Unlike most variables, the variable SHELL is never set from the environment."
        # -- 5.3.2 Choosing the Shell
        # GNU Make Manual Version 4.3 January 2020
        [ self._add_entry(EnvVarEntry(k,v)) for k,v in os.environ.items() if k != "SHELL" ]

    def _add_entry(self, entry):

        # sanity check the entry fields
        entry.sanity()

        self.symbols[entry.name] = entry

    def add(self, name, value, pos=None):
        logger.debug("store \"%s\"=\"%s\"", name, value)

        # an attempt to store empty string is a bug
        assert isinstance(name,str), type(name)
        if not len(name):
            breakpoint()
        assert len(name)

        # sanity check for bad names XXX add more cases
        # (will hit this if my tokenparser is screwing up)
        assert ' ' not in name, name

        # GNU Make doesn't do this warning
        if name in constants.builtin_variables:
            warning_message(pos, "overwriting built-in variable \"%s\"" % name)

        try:
            entry = self.symbols[name]
            logger.debug("overwrite value name=%s at pos=%r", entry.name, pos)
        except KeyError:
            entry = None

        # if we didn't find it, make it
        if self.command_line_flag:
            # this flag is a weird hack to support vars created by eval()'ing
            # expressions from the command line
            new_entry = CommandLineEntry(name, value)
            # command line vars are always exported until explicitly unexported
        else:
            # command line > file
            if isinstance(entry,CommandLineEntry):
                return

            new_entry = FileEntry(name, value, pos)
            new_entry.set_export(self.export_default_value)

        # XXX not sure read-only is a good idea yet
#        if entry.read_only:
#            raise PermissionDenied(name)

        self._add_entry(new_entry)

    def add_automatic(self, name, value, pos):
        entry = AutomaticEntry(name, value, pos)
        self._add_entry(entry)

    def maybe_add(self, name, value, pos=None):
        # If name already exists in the table, don't overwrite.
        # Used with ?= assignments.
        try:
            self.symbols[name]
            return
        except KeyError:
            pass

        return self.add(name, value, pos)

    def _parse_abbrev_patsubst(self, key):
        # This function handles the case of an abbrevitated patsubst.
        # OBJ=$(SRC:.c=.o)  # need to parse out to ("SRC", ".c", ".o)
        #
        # key should be a Python string

        # fast test; allow ValueError to propagate
        colon_pos = key.index(':')
        equal_pos = key.index('=')
        if colon_pos > equal_pos:
            raise ValueError

        varname = key[0:colon_pos]
        pat1 = key[colon_pos+1:equal_pos]
        pat2 = key[equal_pos+1:]

        return (varname,pat1,pat2)

    def _eval_abbrev_patsubst(self, key):
        # allow exception(s) to propagate
        varname, pat1, pat2 = self._parse_abbrev_patsubst(key)
#        logger.debug("abbrev varname=%r pat1=%r pat2=%4", varname, pat1, pat2)

        pat1_len = len(pat1)
        value = self.fetch(varname)
        if pat1_len == 0:
            # pat1 empty so it's a simple append operation
            return " ".join([s+pat2 for s in value.split()])

        new_value = " ".join([s[:-pat1_len] + pat2 if s.endswith(pat1) else s for s in value.split()])
        return new_value

    def fetch(self, key, pos=None):
        # now try a var lookup 
        # Will always return an empty string on any sort of failure. 
        logger.debug("fetch key=%r", key)
        assert isinstance(key,str), type(key)
        assert len(key)  # empty key bad

        try:
            # check for a "magic" variable name (an abbreviated patsubst)
            # e.g., $(SRC:.c=.o)
            return self._eval_abbrev_patsubst(key)
        except ValueError:
            pass

        # built-in variable ?
#        try:
#            return self.built_ins[key](key)
#        except KeyError:
#            pass

        try:
#            print("fetch value=\"%r\"" % self.symbols[key])
            return self.symbols[key].eval(self)
        except KeyError:
            if self.warn_undefined:
                warning_message(pos, "undefined variable '%s'" % key)
            if _fail_on_undefined:
                raise

        logger.debug("sym=%s not in symbol table", key)
        return ""

    def append(self, name, value, pos=None):

        # "When the variable in question has not been defined before, ‘+=’ acts
        # just like normal ‘=’: it defines a recursively-expanded variable."
        # GNU Make 4.3 January 2020
        if name not in self.symbols:
            # ha ha type checking
            assert isinstance(value,Symbol), type(value)

            return self.add(name, value, pos)

        entry = self.symbols[name]
        if isinstance(entry.value, Symbol):
            return entry.append_recursive(value)

        # simple string append, space separated
        try:
            entry.append(value.eval(self), pos)
        except AttributeError:
            entry.append(value, pos)

    def push(self, name):
        # save current value of 'name' in secure, undisclosed location

        logger.debug("push name=%s", name)

        # don't use self.fetch() because will eval the var which could lead to
        # side effects
        if name not in self.symbols:
            # nothing to save
            return

        entry = self.symbols[name]
        # remove the other reference (otherwise 'add' will just update the
        # self.symbols[name] entry which also points to our stack entry)
        del self.symbols[name]
            
        # create the dequeue if doesn't exist
        if not name in self.stack:
            self.stack[name] = collections.deque()

        # push right, pop right (stack)
        logger.debug("push entry=%s", entry.name)
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
            # if the name doesn't exist in the self.symbols{}, we push/popped a
            # name but didn't use it between the push/pop (perfectly acceptable)
            if name in self.symbols:
                del self.symbols[name]
            return

        # TODO future memory optimization would be to delete the dequeue from
        # self.stack when empty

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
        except KeyError:
            return "undefined"

        if isinstance(value,Symbol):
            return "recursive"

        # TODO dig into gnu make code, learn why env vars return "recursive"
        if value.origin == 'environment':
            return "recursive"

        return "simple"

    def origin(self, name):
        # support for the $(origin) function

        # don't use self.fetch() because will eval the var which could lead to
        # side effects

        # undefined
        # default TODO
        # environment
        # environment override TODO
        # file 
        # command line
        # override -- override directive TODO
        # automatic -- defined in a rule e.g., $@ TODO

        try :
            entry = self.symbols[name]
            assert entry.origin is not None, name
            return entry.origin
        except KeyError:
            return "undefined"

    def value(self, name):
        # support for the $(value) function

        # don't use self.fetch() because will eval the var which could lead to
        # side effects

        try :
            entry = self.symbols[name]
            value = entry.value
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
        return name in self.symbols
        
    def ifdef(self, name):
        if not name in self.symbols:
            return False

        # it's in our table but does it have a value?
        value = self.symbols[name]
        assert value._value is not None

        if not len(value._value):
            return False

        return True

    def export(self, name=None):
        if name is None:
            # export everything
            self._export_all()
            return

        try:
            value = self.symbols[name].set_export(Export.EXPLICIT)
        except KeyError:
            # no such entry
            pass

    def unexport(self, name=None):
        if name is None:
            # export everything
            self._unexport_all()
            return

        try:
            self.symbols[name].set_unexport(Export.EXPLICIT)
        except KeyError:
            # no such entry
            pass

    def undefine(self, name):
        # support the undefine directive
        try:
            entry = self.symbols[name]
        except KeyError:
            # does not exist. no harm, no foul.
            return

        # TODO any variables that GNU Make considers an error to undefine?

        del self.symbols[name]

    def _export_all(self):
        for k,v in self.symbols.items():
            v.set_export( Export.IMPLICIT )
        # new vars from this point on will be marked as export
        self.export_start()

    def _unexport_all(self):
        for k,v in self.symbols.items():
            v.set_unexport(Export.IMPLICIT)
        self.export_stop()

    def get_exports(self):
        return { name:entry.eval(self) for name,entry in self.symbols.items() if entry.export }

    def export_start(self):
        # The export start/stop allows us to separate the "export" and
        # assignment expressions. We set the "start" before eval()'ing an
        # export with an assignment expression so any assigments in the
        # expression will be automatically marked as 'export'
        #
        # Also used with eval'ing command line arguments which are exported by
        # default.
        # 
        # "By default, only variables that came from the environment or the
        # command line are passed to recursive invocations."
        #  -- GNU Make manual  Version 4.3 Jan 2020
        self.export_default_value = Export.IMPLICIT

    def export_stop(self):
        self.export_default_value = Export.NOEXPORT

    def command_line_start(self):
        # yuk ugly hack
        self.command_line_flag = True

    def command_line_stop(self):
        self.command_line_flag = False

