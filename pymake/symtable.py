# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com
#
# davep 20-Mar-2016 ; symbol table

import os
import logging
import collections
from enum import Enum

import pymake.version as version
import pymake.constants as constants
from pymake.error import *

logger = logging.getLogger("pymake.symtable")

#logger.setLevel(level=logging.INFO)

#_fail_on_undefined = True
_fail_on_undefined = False

def _value_is_recursive(v):
    # test if a value is something with its own eval method which would
    # indicate it's a recursive variable 
    # for example:
    # FOO=foo  <-- stored as a Symbol
    # FOO:=foo <-- stored as a Python string (no eval method)
    try:
        return True if v.eval else False
    except AttributeError:
        return False

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

        self._export_stack = []

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
        logger.debug("overwrite value name=%s at pos=%r", self.name, pos)
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
        if _value_is_recursive(self._value):
            logger.debug("recursive eval %r loop=%d name=%s at pos=%r", self, self.loop, self.name, self.get_pos())
            if self.loop > 0:
                msg = "Recursive variable %r references itself (eventually)." % self.name
                logger.debug("%s", msg)
                if symbol_table.env_recursion > 0:
                    # if we're expanding a recursive variable for a shell
                    # command, just return an empty string
                    return ""
                
                raise RecursiveVariableError(msg=msg, pos=self.get_pos())

            logger.debug("recursive eval %r %s loop+=1", self, self.name)
            self.loop += 1
            step1 = [ self._value.eval(symbol_table) ]
            step1.extend( [t.eval(symbol_table) for t in self._appends] )
            self.loop -= 1
            logger.debug("recursive eval %r %s loop-=1", self, self.name)
            assert self.loop >= 0, self.loop
            return " ".join(step1)

        return self._value

    def append_recursive(self, value):
        # ha ha type checking; require a Symbol-ish thing
        assert _value_is_recursive(value), type(value)

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

# An Immutable Entry is one where we cannot change the value BUT we can
# completely change the entry. For example, .VARIABLES has a special meaning in
# Make (a string containing names of all the defined variables) BUT we can do something bone-headed like:
#
# .VARIABLES:=foo  # kill the .VARIABLES variable
#
# When am Immutable Entry is updated, the set_value() will throw an exception.
# The Symbol Table add() method will then create a new entry instead.
#
class ImmutablemixIn:
    def set_value(self, value, pos):
        raise ValueError("cannot update CallbackEntry name=%s" % self.name)

class CallbackEntry(ImmutablemixIn, DefaultEntry):
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
class EnvVarEntry(ImmutablemixIn, Entry):
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
class CommandLineEntry(ImmutablemixIn, Entry):
    origin = "command line"

    def __init__(self, name, value):
        super().__init__(name,value)
        self.set_export(Export.SUBMAKE)


class AutomaticEntry(Entry):
    origin = "automatic"
    never_export = True

    def __init__(self, name, value, pos):
        assert name in constants.automatic_variables, name
        super().__init__(name, value, pos)


class BuiltInEntry(Entry):
    origin = "override"
    next_export = True

    def __init__(self, name, value, pos):
        assert name in constants.builtin_variables, name
        super().__init__(name, value, pos)

class SymbolTable(object):
    def __init__(self, **kwargs):
        # Stack of dictionary to support "hiding" variable definitions. For
        # example, foreach loop variables and target specific variables must
        # not change existing definitions
        #
        # The topmost layer will be [0]
        # New layers are added using .insert(0) and removed using [1:]
        #
        # In some places, I skip search layers if the len()==1
        #
        # key: variable name
        # value: Entry instance
        self.layers = [{},]

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

        # Copy GNU Make's method of handling recursive variable expansion for
        # shell exports. When we launch a shell, vars marked 'export' must be
        # put into the environment. However, we can run into variable expansion
        # loops. For example:
        #
        # DATE=$(shell date)
        # export DATE
        #
        # DATE is exported so DATE needs to be in the environment. But DATE's
        # value comes from a $(shell) execution which needs DATE's value as an
        # env var. When env_recursion is set, a recursive variable returns an
        # empty string instead of throwing the "recurisve variable references
        # itself" error.
        #
        # (In GNU Make this is a global variable)
        #
        self.env_recursion = 0

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

    def push_layer(self):
        # push top, pop top
        self.layers.insert(0, {})

    def pop_layer(self):
        # push top, pop top
        self.layers = self.layers[1:]

    def find(self, name, layer_idx=None):
        # search the layers for a variable; throw KeyError on failure 
        if len(self.layers)==1:
            return self.layers[0][name]

        if layer_idx is not None:
            # only search a specific layer
            return self.layers[layer_idx][name]

        # search layers from top to bottom (forward iterator)
        for symbols in self.layers:
            try:
                return symbols[name]
            except KeyError:
                pass
        raise KeyError(name)

    def _get_entries(self, filter_fn=None):
        # Build a dict name:entry of entire symbol table contents taking layers
        # into account. Created originally to fetch all exported vars and to
        # handle global 'export'/'unexport' directives.
        entries = {}

        # walk layers bottom to top so higher entries replace lower
        # (reverse iterator)
        if filter_fn:
            for symbols in self.layers[::-1]:
                entries.update({ name:entry for name,entry in symbols.items() if filter_fn(entry) })
        else:
            for symbols in self.layers[::-1]:
                entries.update({ name:entry for name,entry in symbols.items() })

        return entries        

    def _add_entry(self, entry):

        # sanity check the entry fields
        entry.sanity()

        # always add to the top layer
        self.layers[0][entry.name] = entry

    def add(self, name, value, pos=None):
        logger.debug("store \"%s\"=\"%s\"", name, value)

        assert isinstance(name,str), type(name)

        # an attempt to store empty string is a bug
        if not name:
            raise EmptyVariableName(pos=pos)

        # sanity check for bad names XXX add more cases
        # (will hit this if my tokenparser is screwing up)
        assert ' ' not in name, ">>%s<<" % name

        # GNU Make doesn't do this warning
        if name in constants.builtin_variables:
            warning_message(pos, "overwriting built-in variable \"%s\"" % name)

        # only search top layer; if not there, we'll add it to mask the
        # layer(s) below
        try:
            entry = self.find(name, 0)
        except KeyError:
            entry = None 

        if entry is None:
            # easy case: if we didn't find it, make it
            if self.command_line_flag:
                # this flag is a weird hack to support vars created by eval()'ing
                # expressions from the command line
                # - command line vars are always exported until explicitly
                #   marked 'unexport'
                # - command line vars cannot be overwritten by file variables
                #   except by the 'override' directive (not yet implemented)
                entry = CommandLineEntry(name, value)
            else:
                if pos and pos[0] == "@defaults":
                    entry = DefaultEntry(name, value, pos)
                else:
                    entry = FileEntry(name, value, pos)
                entry.set_export(self.export_default_value)

            self._add_entry(entry)
        else:
            overwrite = False
            try:
                entry.set_value(value, pos)
            except ValueError:
                overwrite = True

            if overwrite:
                # Found an immutable variable that refuses to be overwritten.
                # So (maybe) create a new one.
                overwrite_entry = None
                if self.command_line_flag:
                    # command line entry can happily override command line entry
                    overwrite_entry = CommandLineEntry(name, value)
                else:
                    # do not overwrite a command line entry when we're
                    # no longer processing command line variables
                    if not isinstance(entry, CommandLineEntry):
                        overwrite_entry = FileEntry(name, value, pos)

                if overwrite_entry:
                    self._add_entry(overwrite_entry)

    def add_automatic(self, name, value, pos):
        entry = AutomaticEntry(name, value, pos)
        self._add_entry(entry)

    def maybe_add(self, name, value, pos=None):
        # If name already exists in the table, don't overwrite.
        # Used with ?= assignments.
        try:
            self.find(name)
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
            return self.find(key).eval(self)
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

        entry = None
        try:
            entry = self.find(name)
        except KeyError:
            pass
        if entry is None:
            assert _value_is_recursive(value), type(value)
            return self.add(name, value, pos)
        
        if _value_is_recursive(entry.value):
            return entry.append_recursive(value)

        # simple string append, space separated
        try:
            entry.append(value.eval(self), pos)
        except AttributeError:
            entry.append(value, pos)

    def flavor(self, name):
        # Support for the $(flavor) function
        #
        # undefined
        # recursive
        # simple

        # don't use self.fetch() because will eval the var which could lead to
        # side effects
        try :
            value = self.find(name)
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
            entry = self.find(name)
            assert entry.origin is not None, name
            return entry.origin
        except KeyError:
            return "undefined"

    def value(self, name):
        # support for the $(value) function

        # don't use self.fetch() because will eval the var which could lead to
        # side effects

        try :
            entry = self.find(name)
            value = entry.value
            if isinstance(value,Symbol):
                return value.makefile()
            return value
        except KeyError:
            pass

    def variables(self, _):
        # return $(.VARIABLES)
        # walk the layers, bottom to top, gathering the key strings

        if len(self.layers)==1:
            return " ".join(self.layers[0].keys())
        raise NotImplementedError("variables")
#        return " ".join(self.symbols.keys())

    def is_defined(self, name):
        # is this varname in our symbol table (or other mechanisms)
        try:
            _ = self.find(name)
            return True
        except KeyError:
            return False
        
    def ifdef(self, name):
        entry = None
        try:
            entry = self.find(name)
        except KeyError:
            return False

        # it's in our table but does it have a value?
        assert entry._value is not None

        if not len(entry._value):
            return False

        return True

    def export(self, name=None):
        if name is None:
            # export everything
            self._export_all()
            return

        try:
            value = self.find(name).set_export(Export.EXPLICIT)
        except KeyError:
            # no such entry
            pass

    def unexport(self, name=None):
        if name is None:
            # export everything
            self._unexport_all()
            return

        try:
            self.find(name).set_unexport(Export.EXPLICIT)
        except KeyError:
            # no such entry
            pass

    def undefine(self, name):
        # support the undefine directive
        if len(self.layers)==1:
            try:
                del self.layers[0][name]
            except KeyError:
                # does not exist. no harm, no foul.
                return

        # TODO any variables that GNU Make considers an error to undefine?

        # Try in layer order. If we don't find it in a layer, we're done (leave
        # lower layers intact)
        for symbols in self.layers:
            try:
                del symbols[name]
            except KeyError:
                return

    def _export_all(self):
        entries = self._get_entries()
        for k,v in entries.items():
            v.set_export( Export.IMPLICIT )
        # new vars from this point on will be marked as export
        self.export_start()

    def _unexport_all(self):
        entries = self._get_entries()
        for k,v in entries.items():
            v.set_unexport(Export.IMPLICIT)
        # turn off global export flag
        self.export_stop()

    def get_exports(self):
        logger.debug("get_exports")
        assert self.env_recursion >= 0

        # cannot eval() during the self.symbols iteration because we could
        # store something in the symbol table that will throw a "dictionary
        # changed during iteration" error (for example, .SHELLSTATUS is updated
        # internally every time a shell is run)
        entries = self._get_entries(lambda e:e.export )

        exports = { name:entry.eval(self) for name,entry in entries.items() }

        assert self.env_recursion >= 0
        return exports

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

    def ignore_recursion(self):
        assert self.env_recursion >= 0
        self.env_recursion += 1

    def allow_recursion(self):
        self.env_recursion -= 1
        assert self.env_recursion >= 0

    def update_builtin(self, name, value, pos=None):
        # update a known built-in variable (fewer checks)
        assert name in constants.builtin_variables, name

        try:
            return self.find(name).set_value(value, pos)
        except KeyError:
            pass

        new_entry = BuiltInEntry(name, value, pos)
        self._add_entry(new_entry)


