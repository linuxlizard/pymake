#!/usr/bin/env python3

# davep 12-Mar-2016 ;  

import logging

logger = logging.getLogger("pymake")

from symbol import *

def test1():
    symbol_table = {}
    lit = Literal("foo")
    s = lit.eval(symbol_table)
    assert s=="foo", s

    e = Expression((Literal("a"), Literal("b"), Literal("c")))
    s = e.eval(symbol_table)
    assert s=="abc", s

    # $(a) not in symbol table so should return an empty string
    e = VarRef([Literal("a")])
    s = e.eval(symbol_table)
    assert s=="", s
    
    # a=10
    e = VarRef([Literal("a")])
    symbol_table["a"] = "10"
    s = e.eval(symbol_table)
    assert s=="10", s

    # $(info b=$(b))
    e = Expression([Literal(""),VarRef([Literal("info b="),VarRef([Literal("b")]),Literal("")])])
    s = e.eval(symbol_table)
    logger.info("s=%s",s)

    # b = 10
    e = AssignmentExpression([Expression([
                                Literal("b")
                                ]),
                              AssignOp("="),
                              Expression([Literal("10")])
                              ])

def run_tests():
    test1()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    run_tests()
