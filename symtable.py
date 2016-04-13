# davep 20-Mar-2016 ; symbol table

import logging

logger = logging.getLogger("pymake.symtable")

from symbol import Literal
import functions

class DuplicateFunction(Exception):
    pass

class SymbolTable(object):
    def __init__(self):
        self.symbols = {}

        self.functions = {}
        functions.make_symbols(self)

    def add(self, name, value):
        logger.debug("%s store \"%s\"=\"%s\"", self, name, value)
        self.symbols[name] = value

    def add_function(self, name, cls):
        try:
            # for now, don't allow overwriting
            self.functions[name]
        except KeyError:
            self.functions[name] = cls
        else:
            raise DuplicateFunction(name)

    def fetch(self, s, fargs=None):
        # first try functions
        fname, rest = functions.split_function_call(s)
        logger.debug("fetch fn=%s", fname)
        try:
            fcls = self.functions[fname]
        except KeyError:
            logger.debug("no fn=%s", fname)
            pass
        else:
            # function args should be a list or None
            # but we need to pass the constructor a list of args
            args = fargs or []
            # do NOT modify fnargs; is a ref into the AST
            assert rest != ""  # catch a weird corner condition error
            if rest:
                return fcls([Literal(rest)] + args)
            return fcls(args)

        # now try a var lookup (allow keyerror to propagate)
        logger.debug("fetch sym=%s", s)
        return self.symbols[s]
