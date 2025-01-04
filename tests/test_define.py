# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com
#
# test tokenzparsing the 'define' directive.

import pytest

from pymake.vline import get_vline, VirtualLine, VCharString
from pymake.scanner import ScannerIterator
import pymake.tokenizer as tokenizer
import pymake.symbol
from pymake.symbol import *
import pymake.pymake as pymake
import pymake.source as source
from pymake.error import *

import run

# turn on some extra code paths that allow normally incorrect types to work
pymake.symbol._testing = True
pymake.vline._testing = True

def _run_tokenize(s,name):
    dir_s = VCharString.from_string("define")
    vchar_string = VCharString.from_string(s)
    line_scanner= ScannerIterator(vchar_string, name)
    e = tokenizer.tokenize_assignment_expression(iter(line_scanner), define=True)
    print(e)
    return e

def _prepare_parser(s, name):
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, name)
    vline_iter = get_vline(name, line_scanner)
    return vline_iter

def test1():
    e = _run_tokenize("two-lines=\n", "test1")
    assert e.token_list[0].makefile()=="two-lines"

def test2():
    e = _run_tokenize("    two-lines   =     \n", "test2")
    assert e.token_list[0].makefile()=="    two-lines   "

def test_no_equal():
    e = _run_tokenize("    two-lines       \n", "test_no_equal")
    assert e.token_list[0].makefile()=="    two-lines       "

def test_extraneous_text():
    # GNU Make throws a warning "extraneous text after 'define' directive
    e = _run_tokenize("    two-lines = junk      \n", "test_extraneous_text")
    assert e.token_list[0].makefile()=="    two-lines "

def test_extraneous_text_no_equal():
    # GNU Make throws a warning "extraneous text after 'define' directive
    e = _run_tokenize("    two-lines  junk      \n", "test_extraneous_text_no_equal")
    assert e.token_list[0].makefile()=="    two-lines  "

@pytest.mark.skip(reason="spaces in variable name might be a bug in GNU Make")
def test_internal_whitespace():
    # GNU Make does not warn "extraneous text after 'define' directive here.
    # What does GNU Make actually do?  A variable named 'a b c' is added to the
    # symbol table. Can be accessed via an env var exported to child processes.
    # Example:
    #
    # export define a b c=
    # lol found a b c
    # endef
    #
    # all:
    # <tab>python3 -c 'import os; print(os.getenv("a b c"))'
    #
    # output is:
    # =lol found a b c
    # 
    # Note the '=' is part of the value.
    #
    e = _run_tokenize("a b c=\n", "test-internal-whitespace")
    assert e.token_list[0].makefile() == "a b c"

def test_varref_name():
    e = _run_tokenize("$a$b$c= \n", "test-varref-name")
    assert all( ( isinstance(t,VarRef) for t in e.token_list[0].token_list) )

def test_varref_and_literal_name():
    e = _run_tokenize("$a$b$cdef = \n", "test-varref-literal-name")
    assert e.token_list[0].token_list[3].literal
    assert all( ( isinstance(t,VarRef) for t in e.token_list[0].token_list[:3]) )

def test_define_block():
    s = """
define two-lines
echo foo
echo $(bar)
endef

define two-lines :=
echo foo
echo $(bar)
endef

export define two-lines :=
echo foo
echo $(bar)
endef

define two-lines:=
echo \
foo
echo $(bar)
endef
    
define two-lines:=
\t\techo foo
\t\techo $(bar)
endef
"""

    name = "test-define-block"
    vline_iter = _prepare_parser(s,name)

    defines_list = [v for v in pymake.parse_vline(vline_iter)]

    for d in defines_list:
        assert d
        assert isinstance(d,DefineDirective)
        assert d.name == "define"
        print("d=",d)
        # test round tripping (haven't tried this in a long time)
        eval('%s' % d)

        print("m=",d.makefile())

    with pytest.raises(StopIteration):
        s = next(vline_iter)

def test_missing_endef():
    s = """
define two-lines
echo foo
echo $(bar)
"""
    name = "test-missing-endef"
    vline_iter = _prepare_parser(s,name)

    pv = pymake.parse_vline(vline_iter)
    with pytest.raises(ParseError):
        d = next(pv)

    with pytest.raises(StopIteration):
        s = next(vline_iter)

def test_extraneous_text_endef():
    s = """
define two-lines
echo foo
echo $(bar)
endef two-lines
"""
    name = "test-extraneous-text-after-endef"
    vline_iter = _prepare_parser(s,name)

    d = [ v for v in pymake.parse_vline(vline_iter)]
    print("d=",d)

    with pytest.raises(StopIteration):
        s = next(vline_iter)

def test_fake_endef():
    s = """
define two-lines
echo foo
echo $(bar)
endeff
endef



# Now is the time for all good men to come to the aid of their country.
"""
    name = "test-fake-endef"
    vline_iter = _prepare_parser(s,name)

    d = [v for v in pymake.parse_vline(vline_iter)]
    print("d=",d)

    with pytest.raises(StopIteration):
        s = next(vline_iter)

def test_endef_comment():
    s = """
define two-lines
echo foo
echo $(bar)
endef#end of two-lines-2
"""
    name = "test-endef-commend"
    vline_iter = _prepare_parser(s,name)

    d = [v for v in pymake.parse_vline(vline_iter)]
    print("d=",d)

    with pytest.raises(StopIteration):
        s = next(vline_iter)



def test_nested_define():
    s = """
define two-lines
echo foo
echo $(bar)
define three-lines
echo 1
echo 2
echo 3
endef
endef
"""
    name = "test-nested-define"
    vline_iter = _prepare_parser(s,name)

    d = [v for v in pymake.parse_vline(vline_iter)]
    print("d=",d)

    with pytest.raises(StopIteration):
        s = next(vline_iter)

@pytest.mark.skip(reason="spaces handling in multi-line shell assign is broken")
def test_shell_define():
    makefile = """
define shell_example !=
    echo foo
    echo bar
endef
$(info >>$(shell_example)<<)
@:;@:
"""
    s1 = run.gnumake_string(makefile)
    print("make=",s1)

    s2 = run.pymake_string(makefile)
    print("pymake=",s2)

    assert s1==s2

