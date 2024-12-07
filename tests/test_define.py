# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com
#
# test tokenzparsing the 'define' directive.

import pytest

from pymake.vline import VCharString
from pymake.scanner import ScannerIterator
import pymake.tokenizer as tokenizer
from pymake.symbolmk import VarRef

def _run(s,name):
    dir_s = VCharString.from_string("define")
    vchar_string = VCharString.from_string(s)
    vline = ScannerIterator(vchar_string, name)
    e = tokenizer.tokenize_assignment_expression(iter(vline), define=True)
    print(e)
    return e

def test1():
    e = _run("two-lines=\n", "test1")
    assert e.token_list[0].makefile()=="two-lines"

def test2():
    e = _run("    two-lines   =     \n", "test2")
    assert e.token_list[0].makefile()=="    two-lines   "

def test_no_equal():
    e = _run("    two-lines       \n", "test_no_equal")
    assert e.token_list[0].makefile()=="    two-lines       "

def test_extraneous_text():
    # GNU Make throws a warning "extraneous text after 'define' directive
    e = _run("    two-lines = junk      \n", "test_extraneous_text")
    assert e.token_list[0].makefile()=="    two-lines "

def test_extraneous_text_no_equal():
    # GNU Make throws a warning "extraneous text after 'define' directive
    e = _run("    two-lines  junk      \n", "test_extraneous_text_no_equal")
    assert e.token_list[0].makefile()=="    two-lines  "

@pytest.mark.skip(reason="spaces in variable name might be a bug in GNU Make")
def test_internal_whitespace():
    # GNU Make does not warn "extraneous text after 'define' directive here.
    # What does GNU Make actually do?  A variable named 'a b c' is added to the
    # symbol table. Can be accessed via an env var exported to child processes.
    # Example:
    #
    # export define a b c=
    # echo lol found a b c
    # endef
    #
    # all:
    # <tab>python3 -c 'import os; print(os.getenv("a b c"))'
    #
    # output is:
    # =echo lol found a b c
    # 
    # Note the '=' is part of the value.
    #
    e = _run("a b c=\n", "test-internal-whitespace")
    assert e.token_list[0].makefile() == "a b c"

def test_varref_name():
    e = _run("$a$b$c= \n", "test-varref-name")
    assert all( ( isinstance(t,VarRef) for t in e.token_list[0].token_list) )

def test_varref_and_literal_name():
    e = _run("$a$b$cdef = \n", "test-varref-literal-name")
    assert e.token_list[0].token_list[3].literal
    assert all( ( isinstance(t,VarRef) for t in e.token_list[0].token_list[:3]) )

