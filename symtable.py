# davep 20-Mar-2016 ; symbol table

import logging

logger = logging.getLogger("pymake.symtable")

from symbol import Literal

class DuplicateFunction(Exception):
    pass

class SymbolTable(object):
    def __init__(self):
        self.symbols = {}

    def add(self, name, value):
        logger.debug("%s store \"%s\"=\"%s\"", self, name, value)

        # an attempt to store empty string is a bug
        assert len(name)

        self.symbols[name] = value

    def fetch(self, s):
        # now try a var lookup (allow keyerror to propagate)
        logger.debug("fetch sym=%s", s)
        if not len(s):
            return ""
        try:
            return self.symbols[s]
        except KeyError:
            return ""
