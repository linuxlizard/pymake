#!/usr/bin/env python3

import sys
import logging

logger = logging.getLogger("pymake")

from symtable import SymbolTable
import functions
from functions import *
from symbol import *

def test_info():
    symbol_table = SymbolTable()
    info = Info([])
    info.eval(symbol_table)

    info = Info([Literal("hello, world")])
    info.eval(symbol_table)

    info = Info([VarRef([Literal("q")])])
    info.eval(symbol_table)

def test_find():

    test_list = ( "info hello, world",
                  "info  hello, world",
                  " info hello, world",
                  "info\thello, world",
                  "info",
                  "info ",
                  "info   ",
                  "info \tfoo",
                )
    for test in test_list:
        fn = functions.find(test)
#        fn.eval()

def test_split():
    test_list = ( ("info hello, world", ("info", "hello, world")),
                  ("info  hello, world", ("info", " hello, world")),
                  (" info hello, world", (" info hello, world", None)),
                  ("info\thello, world", ("info", "hello, world")),
                  ("info", ("info", None)),
                  ("info ", ("info", None)),
                  ("info   ", ("info", "  ")),
                  ("info \tfoo",("info", "\tfoo")),
                )
    for test, result in test_list:
        a,b = functions.split_function_call(test)
        print("\"{}\" \"{}\"".format(test,result))
        print("\"{}\" \"{}\"".format(a,b))
        assert a==result[0], a
        assert b==result[1], b
#        assert a+b=="".join(result), result
        print("ok")
    

def test_all():
    test_split()
#    test_find()

#    test_info()


if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_all()
