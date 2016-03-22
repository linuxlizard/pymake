#!/usr/bin/env python3

# davep 12-Mar-2016 ; evaluate the Makefile AST

import sys
import logging

logger = logging.getLogger("pymake.evaluate")

from symtable import SymbolTable

symbol_table = SymbolTable()

def evaluate(symbol_list):
    for m in makefile:
        logger.debug("m=%s", m)
        s = m.eval(symbol_table)
        print("s={}".format(s))
        print("symbol_table={}".format(symbol_table))

