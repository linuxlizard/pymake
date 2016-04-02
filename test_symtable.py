#!/usr/bin/env python3

# davep 20-Mar-2016 ; symbol table

import sys
import logging

from symtable import SymbolTable

logger = logging.getLogger("pymake.test_symtable")

def test_all():
    symbol_table = SymbolTable()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_all()
