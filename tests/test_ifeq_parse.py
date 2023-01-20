import logging
import tempfile

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

import pymake.pymake as pymake
from pymake.symbolmk import *
#from vline import VirtualLine, VCharString
#from tokenizer import tokenize_statement
#from parser import parse_ifeq_conditionals
from pymake.error import ParseError

# Note on the weird strings e.g. s= " '$a' '$b' " without the ifeq/ifneq:
# parse_ifeq_conditionals() parses the directive expression not the entire
# directive.
#
# Note also I'm passing in ifeq every time because the actual directive type
# doesn't matter when parsing the conditionals.

def _should_succeed(s):
    with tempfile.NamedTemporaryFile() as infile:
        infile.write(s.encode("utf8"))
        infile.flush()
        pymake.parse_makefile(infile.name)

def _should_fail(s):
    with tempfile.NamedTemporaryFile() as infile:
        infile.write(s.encode("utf8"))
        infile.flush()
        try:
            pymake.parse_makefile(infile.name)
        except ParseError:
            pass
        else:
            assert 0, "\"%s\" should have failed" % s

def test_quotes():
    s = "ifeq '$a' '$b'\nendif\n"
    _should_succeed(s)

    s = 'ifeq "$a" "$b"\nendif\n'
    _should_succeed(s)

def test_parens():
    s = "ifeq ($a,$b)\nendif\n"
    _should_succeed(s)

def test_extra_close_paren():
    s = "ifeq ($a,$b))\nendif\n"
    _should_succeed(s)

def test_extra_chars_after_close_paren():
    s = "ifeq ($a,$b)qqq\nendif\n"
    _should_succeed(s)

def test_extra_chars_after_close_quote():
    s = "'$a''$b'qqq"
    _should_succeed(s)

def test_mismatch_open_close():
    # mismatching open/close quote
    s = "ifeq '$a\" '$b'\nendif\n"
    _should_fail(s)

def test_missing_close_paren():
    s = "ifeq ($a,$b \nendif\n"
    _should_fail(s)

def test_missing_close_quote():
    s = "ifeq '$a' '$b"
    _should_fail(s)

def test_missing_open_paren():
    s = "ifeq $a,$b)\nendif\n"
#    s = "ifeq '$a',$b\nendif\n"
    _should_fail(s)

def test_invalid_char():
    s = "ifeq 10,10\nendif\n"
    _should_fail(s)

def test_nested_missing_endif():
    s = """
ifeq (10,10)
    ifeq (a,b)
        
endif
"""
    _should_fail(s)

def test_nested():
    s = """
ifeq (10,10)
    ifeq (a,b)
    endif        
endif
"""
    _should_succeed(s)

def test_nested_invalid_inside():
    s = """
ifeq (10,10)
    ifeq (a,a)
        $(error should not see this)
    endif
endif
"""
    _should_succeed(s)
    

if __name__ == '__main__':
#    test_missing_open_paren()
#    test_mismatch_open_close()
    test_nested_missing_endif()
#    test1()

