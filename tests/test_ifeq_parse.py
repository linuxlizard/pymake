import logging

import pytest

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from pymake.tokenizer import tokenize_statement_LHS
from pymake.vline import VirtualLine
from pymake.parsermk import parse_ifeq_conditionals
from pymake.symbolmk import Expression
from pymake.error import InvalidSyntaxInConditional
from pymake.constants import whitespace

# Note on the weird strings e.g. s= " '$a' '$b' " without the ifeq/ifneq:
# parse_ifeq_conditionals() parses the directive expression not the entire
# directive.
#
# Note also I'm passing in ifeq every time because the actual directive type
# doesn't matter when parsing the conditionals.

def _run(s, expect):
    print("try %r" % s)
    virt_line = VirtualLine([s], (0,0), "/dev/null")
    viter = iter(virt_line)
    lhs, op = tokenize_statement_LHS(viter)

    # if expect is None, then we have a junk expression so don't validate
    # anything 
    # check+remove the first two tokens
    assert lhs[0].makefile() == "ifeq"
    del lhs[0]
    assert lhs[0].makefile() in whitespace
    del lhs[0]

    expr = Expression(lhs)

    expr1, expr2 = parse_ifeq_conditionals(expr, "ifeq")
    if expect is None:
        # should have failed
        assert 0, (s, expr1.makefile(),expr2.makefile())
    assert expr1.makefile() == expect[0]
    assert expr2.makefile() == expect[1]

def _should_succeed(s, expect):
    _run(s, expect)

def _should_fail(s):
    try:
        _run(s, None)
    except InvalidSyntaxInConditional as err:
        print("err=%s" % err)
#        pass
    else:
        assert 0, "\"%s\" should have failed" % s

def test_single_quotes():
    s = "ifeq '$a' '$b'\n"

    _should_succeed(s, ("$(a)", "$(b)"))

def test_double_quotes():
    s = 'ifeq "$a" "$b"\n'
    _should_succeed(s, ("$(a)", "$(b)"))

def test_parens():
    s = "ifeq ($a,$b)\n"
    _should_succeed(s, ("$(a)", "$(b)"))

def test_extra_close_paren():
    s = "ifeq ($a,$b))\n"
    _should_succeed(s, ("$(a)", "$(b)"))

def test_extraneous_text():
    s = "ifeq (a,a),"
    _should_succeed(s, ("a", "a"))

def test_extra_chars_after_close_paren():
    s = "ifeq ($a,$b)qqq\n"
    _should_succeed(s, ("$(a)", "$(b)"))

def test_extra_chars_after_close_quote():
    s = "ifeq '$a''$b'qqq"
    _should_succeed(s, ("$(a)", "$(b)"))

def test_mismatch_open_close():
    # mismatching open/close quote
    s = "ifeq '$a\" '$b'\n"
    _should_fail(s)

def test_missing_close_paren():
    s = "ifeq ($a,$b \n"
    _should_fail(s)

def test_missing_close_quote():
    s = "ifeq '$a' '$b"
    _should_fail(s)

def test_missing_open_paren():
    s = "ifeq $a,$b)\n"
    _should_fail(s)

def test_unbalanced_quotes():
    s = "ifeq '$a',$b\n"
    _should_fail(s)

def test_invalid_char():
    s = "ifeq 10,10\n"
    _should_fail(s)

@pytest.mark.skip(reason="FIXME missing whitespacespace after ifeq")
def test_missing_space():
    # parse error (note the missing space after ifeq) that GNU Make reports as
    # "missing separator"
    s = "ifeq(1,1)\n"
    _should_fail(s)

def test_tab():
    s = "ifeq	(1,1)"
    _should_succeed(s, ("1","1"))

@pytest.mark.skip(reason="FIXME balanced parenthesis parsing")
def test_balanced_parens():
    s = "ifeq ((1),(1))"
    _should_succeed(s, ("(1)", "(1)"))

@pytest.mark.skip(reason="FIXME balanced parenthesis parsing")
def test_balanced_parens_more():
    s = "ifeq (( 1 ),( 1 ))"
    _should_succeed(s, ("( 1 )", "( 1 )"))

@pytest.mark.skip(reason="FIXME balanced parenthesis parsing")
def test_unbalanced_parens():
    s = "ifeq ((,() "
    _should_fail(s)

partial_expressions = (
    "ifeq (",
    "ifeq (a",
    "ifeq (a,",
    "ifeq (a,b",

    "ifeq '",
    "ifeq 'a",
    "ifeq 'a,",
    "ifeq 'a,b",

    'ifeq "',
    'ifeq "a',
    'ifeq "a,',
    'ifeq "a,b',

#    'ifeq "a" "a" "a"',
)

@pytest.mark.parametrize("partial_expression", partial_expressions)
def test_partial_expressions(partial_expression):
    _should_fail(partial_expression)
    _should_fail(partial_expression+"\n")
    _should_fail(partial_expression+" ")
    _should_fail(partial_expression+" \n")
    _should_fail(partial_expression+" # foo")

def test_too_many_expressions():
    s = "ifeq (1,1,1)"
    _should_succeed(s,("1", "1,1"))

def test_empty_first_arg():
    s = "ifeq (,1)"
    _should_succeed(s, ("", "1"))