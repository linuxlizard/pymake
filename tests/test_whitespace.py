#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import run
import verify

def test_simple_whitespace():
    makefile="""
# leading whitespace is discarded
# trailing whitespace is preserved (there are three spaces after 'BAR')
FOO:=   BAR   
$(info FOO=>>>$(FOO)<<<)
@:;@:
"""
    p = run.gnumake_string(makefile)
    print("p=",p)
    assert p=="FOO=>>>BAR   <<<"

    p = run.pymake_string(makefile)
    print("p=",p)
    assert p=="FOO=>>>BAR   <<<"

def test_simple_whitespace_tabs():
    makefile="""
# leading whitespace is discarded
# trailing whitespace is preserved (there are three tabsafter 'BAR')
FOO:=	BAR			
$(info FOO=>>>$(FOO)<<<)
@:;@:
"""
    p = run.gnumake_string(makefile)
    print("p=",p)
    assert p=="FOO=>>>BAR			<<<"

    p = run.pymake_string(makefile)
    print("p=",p)
    assert p=="FOO=>>>BAR			<<<"

def test_whitespace_SHELL():
    # whitespace after /bin/sh
    makefile="""
SHELL:=/bin/sh    
$(info SHELL=>>>$(SHELL)<<<)
$(info $(shell echo hello, world))
@:;@:
"""
    expect = (
        "SHELL=>>>/bin/sh    <<<",
        "hello, world",
    )

    p = run.gnumake_string(makefile)
    print("p=",p)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    print("p=",p)
    verify.compare_result_stdout(expect, p)

