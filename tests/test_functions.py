#
# Whitebox testing of function implementation internals.
#
# TODO add moar tests

import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from error import *
from symbolmk import *
import functions_str
import symtablemk

# turn on internal behaviors that allow us to create literals without VCharString
import symbolmk
symbolmk._testing = True

def test1():
    symbol_table = symtablemk.SymbolTable()
    expr = Literal('1,foo bar baz qux')

    word_fn = functions_str.Word( [expr] )
    result = word_fn.eval(symbol_table)
    assert result=="foo"
    
def test_word_invalid_index():
    symbol_table = symtablemk.SymbolTable()
    expr = Literal('q,foo bar baz qux')

    word_fn = functions_str.Word( [expr] )
    try:
        result = word_fn.eval(symbol_table)
    except InvalidFunctionArguments as err:
        pass
    else:
        assert 0, "should have failed"

def test_word_bad_index():
    symbol_table = symtablemk.SymbolTable()
    expr = Literal('-1,foo bar baz qux')

    word_fn = functions_str.Word( [expr] )
    try:
        result = word_fn.eval(symbol_table)
    except InvalidFunctionArguments as err:
        pass
    else:
        assert 0, "should have failed"
