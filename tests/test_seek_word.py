#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import pytest

from pymake.constants import *
from pymake.vline import VCharString
from pymake.scanner import ScannerIterator
from pymake.tokenizer import seek_word

def test_export():
    v = VCharString.from_string("export\n")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"w={w}")
    assert str(w)=="export", w
    assert vline.is_empty()

def test_substring():
    v = VCharString.from_string("exportttt\n")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert w is None, w
    assert vline.lookahead().get_pos()[1] == (0,0)

def test_trailing_whitespace():
    v = VCharString.from_string("export   \n")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"w={w}")
    assert str(w)=="export", w
    assert vline.is_empty()

@pytest.mark.parametrize("d", directive)
def test_all(d):
    v = VCharString.from_string(d)
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"d={d} w={w}")
    assert str(w)==d, (w,d)

@pytest.mark.parametrize("d", directive)
def test_all_whitespace(d):
    v = VCharString.from_string("   "+d+"   ")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"d={d} w={w}")
    assert str(w)==d, (w,d)

@pytest.mark.parametrize("d", directive)
def test_all_whitespace_tabs(d):
    v = VCharString.from_string("\t\t"+d+"\t\t")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"d={d} w={w}")
    assert str(w)==d, (w,d)

def test_export_statement():
    v = VCharString.from_string("export SRC:=hello.c")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    print(f"w={w}")
    assert str(w)=="export", w
    vchar = next(vline)
    assert vchar.char == 'S', vchar.char
    p = vchar.get_pos()
    assert p[1] == (0,7), p

def test_multiple_modifiers():
    v = VCharString.from_string("export override unexport private export unexport SRC:=hello.c")
    vline = ScannerIterator(v, v.get_pos()[0])
    while True:
        w = seek_word(vline, directive)
        if not w:
            vchar = next(vline)
            assert vchar.char == 'S', vchar.char
            break
        else:
            print(f"w={w}")
            assert str(w) in directive, w

def test_case_sensitivity():
    v = VCharString.from_string("EXPORT SRC:=hello.c")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert w is None, w
    assert vline.lookahead().get_pos()[1] == (0,0)

def test_shuffled():
    v = VCharString.from_string("pextor SRC:=hello.c")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert w is None, w
    assert vline.lookahead().get_pos()[1] == (0,0)

def test_comment():
    v = VCharString.from_string("export#export everything")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert str(w)=="export", w
    # should have consumed rest of line
    assert vline.is_empty()

def test_comment_whitespace():
    v = VCharString.from_string("export #export everything")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert str(w)=="export", w
    # should have consumed rest of line
    assert vline.is_empty()

def test_seek_delimited_word():
    # should stop at non-matching character and be pointing at that char
    v = VCharString.from_string("hello world")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, set(("hello",)))
    assert str(w)=="hello", w
    vchar = next(vline)
    assert vchar.char == 'w', vchar.char

def test_seek_nonwhitespace_delimited():
    v = VCharString.from_string("export,CC:=GCC")
    vline = ScannerIterator(v, v.get_pos()[0])
    w = seek_word(vline, directive)
    assert w is None, w
    assert vline.lookahead().get_pos()[1] == (0,0)

