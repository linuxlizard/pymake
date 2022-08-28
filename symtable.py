# davep 20-Mar-2016 ; symbol table

import os
import logging

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

    def fetch(self, key):
        # now try a var lookup 
        # Will always return an empty string on any sort of failure. 
        logger.debug("fetch key=\"%r\"", key)

        assert isinstance(key,list), type(key)

        s = "".join(flatten(key))
        logger.debug("fetch s=\"%r\"", s)

        if not len(s):
            return [""]
        try:
            return self.symbols[s]
        except KeyError:
            pass

        # TODO read gnu make manual on how env vars are referenced
        logger.debug("sym=%s not in symbol table", s)

        # try environment
        value = os.getenv(s)
        if value is None:
            return [""]
        logger.debug("sym=%s found in environ", s)
        return value

