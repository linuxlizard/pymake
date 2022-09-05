# davep 20-Mar-2016 ; symbol table

import os
import logging

from symbol import Symbol
from flatten import flatten

logger = logging.getLogger("pymake.symtable")

class DuplicateFunction(Exception):
    pass

class SymbolTable(object):
    def __init__(self):
        self.symbols = {}

    def add(self, name, value):
        logger.debug("%s store \"%s\"=\"%s\"", self, name, value)

        # an attempt to store empty string is a bug
        assert isinstance(name,str), type(name)
        assert len(name)

        self.symbols[name] = value

    def maybe_eval(self, value):
        # handle the case where an expression is stored in the symbol table vs
        # a value 
        # e.g.,  a=10  (evaluated whenever $a is used)
        # vs   a:=10  (evaluated immediately and "10" stored in symtable)
        #
        if len(value) and isinstance(value[0],Symbol):
            step1 = [t.eval(self) for t in value]
            return flatten(step1)

        return value

    def fetch(self, key):
        # now try a var lookup 
        # Will always return an empty string on any sort of failure. 
        logger.debug("fetch key=\"%r\"", key)
#        print("fetch key=\"%r\"" % key)

        assert isinstance(key,list), type(key)

        s = "".join(flatten(key))
        logger.debug("fetch s=\"%r\"", s)

        if not len(s):
            # XXX why am I handling an empty key?
            assert 0
            return [""]

        try:
#            print("fetch value=\"%r\"" % self.symbols[s])
            return self.maybe_eval(self.symbols[s])
        except KeyError:
            pass

        # TODO read gnu make manual on how env vars are referenced
        logger.debug("sym=%s not in symbol table", s)

        # try environment
        value = os.getenv(s)
        if value is None:
            return [""]
        logger.debug("sym=%s found in environ", s)
        return [value]
