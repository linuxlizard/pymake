#!/usr/bin/env python3

# davep 12-Mar-2016 ;  

import logging

logger = logging.getLogger("pymake")

from pymake.symbolmk import  (
    Literal, Expression, VarRef, AssignmentExpression, AssignOp,)
from pymake.symtablemk import SymbolTable

def test1():
    # foo
    symbol_table = SymbolTable()
    lit = Literal("foo")
    s = lit.eval(symbol_table)
    assert s=="foo", s

    # abc
    e = Expression((Literal("a"), Literal("b"), Literal("c")))
    s = e.eval(symbol_table)
    assert s=="abc", s

    # $(a) not in symbol table so should return an empty string
    e = VarRef([Literal("a")])
    s = e.eval(symbol_table)
    assert s=="", s
    
    # manually insert 'a' into symbol table
    # then look up
    # a=10
    e = VarRef([Literal("a")])
    symbol_table["a"] = "10"
    s = e.eval(symbol_table)
    assert s=="10", s

    # b not in symbol table so should just return "b="
    # $(info b=$(b))
    binfo = Expression([Literal(""),
                    VarRef([
                        Literal("info b="),
                        VarRef([
                            Literal("b")
                        ]),
                        Literal("")
                    ])
                   ])
    s = binfo.eval(symbol_table)
    logger.info("s=%s",s)
    assert s=="b=", s

    # b = 10
    assign = AssignmentExpression([Expression([Literal("b")]),
                                   AssignOp("="),
                                   Expression([Literal("10")])
                                  ])
    s = assign.eval(symbol_table)

    # now run the $(info b=$b) again
    s = binfo.eval(symbol_table)
    logger.info("s=%s",s)
    assert s=="b=10", s

def run_tests():
    test1()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    run_tests()
