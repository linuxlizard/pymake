#!/usr/bin/env python3

# davep 20-Mar-2016 ; symbol table

import sys
import logging

from symbol import *
from functions import *
from symtable import SymbolTable

logger = logging.getLogger("pymake.test_symtable")

def test_all():
    symtable = SymbolTable()

    logger.debug("functions=%s", symtable.functions)

    thing = symtable.fetch("info hello, world")
    assert thing, "info"
    s = thing.eval(symtable)
    assert len(s)==0
    assert isinstance(thing, Info)

    symtable.add("a",Literal("10"))
    thing = symtable.fetch("info a=",[VarRef([Literal("a")])])
    assert thing, "info"
    s = thing.eval(symtable)
    
if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_all()
