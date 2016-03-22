#!/usr/bin/env python3

import sys
import logging

from symtable import SymbolTable

logger = logging.getLogger("pymake.test_symtable")

def test_all():
    symbol_table = SymbolTable()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_all()
