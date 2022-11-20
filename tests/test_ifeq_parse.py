import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from symbol import *
from vline import VirtualLine
from tokenizer import tokenize_statement
from parser import parse_ifeq_conditionals
from error import ParseError

# Note on the weird strings e.g. s= " '$a' '$b' " without the ifeq/ifneq:
# parse_ifeq_conditionals() parses the directive expression not the entire
# directive.
#
# Note also I'm passing in ifeq every time because the actual directive type
# doesn't matter when parsing the conditionals.

def _should_succeed(s):
    vline = VirtualLine([s], (0,4), "/dev/null")
    stmt = tokenize_statement(iter(vline))
    parse_ifeq_conditionals(stmt, "ifeq", None)

def _should_fail(s):
    vline = VirtualLine([s], (0,4), "/dev/null")
    stmt = tokenize_statement(iter(vline))
    try:
        parse_ifeq_conditionals(stmt, "ifeq", None)
    except ParseError:
        pass
    else:
        assert 0, "should have failed"

def test1():
    s = " '$a' '$b'"
    _should_succeed(s)

def test_parens():
    s = "($a,$b)"
    _should_succeed(s)

def test_extra_close_paren():
    s = "($a,$b))"
    _should_succeed(s)

def test_extra_chars_after_close_paren():
    s = "($a,$b)qqq"
    _should_succeed(s)

def test_extra_chars_after_close_quote():
    s = "'$a''$b'qqq"
    _should_succeed(s)

def test_mismatch_open_close():
    # mismatching open/close quote
    s = " '$a\" '$b'"
    _should_fail(s)

def test_missing_close_paren():
    s = " ($a,$b"
    _should_fail(s)

def test_missing_close_quote():
    s = " '$a' '$b"
    _should_fail(s)

def test_missing_open_paren():
    s = "$a,$b)"
    _should_succeed(s)

if __name__ == '__main__':
    test_missing_open_paren()
#    test1()

