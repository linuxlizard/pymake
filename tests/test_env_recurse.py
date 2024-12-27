# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com

# Test recursively expanded variables and their interaction with the shell

import pytest

import run
import verify

def test1():
    makefile="""
FOO=$(shell echo foo)
export FOO

all:
	@printenv FOO
"""
    expect = (
        "foo",
    )

    p = run.gnumake_string(makefile)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    verify.compare_result_stdout(expect, p)

def test_not_exported():
    makefile="""
FOO=$(shell echo foo)

all:
	@printenv FOO
"""
    p = run.gnumake_should_fail(makefile)

    p = run.pymake_should_fail(makefile)

@pytest.mark.skip("TODO GNU Make 4.3 has different behaviors")
def test_export_loop():
    makefile="""
FOO=$(shell printenv BAR && echo BAR ok)
BAR=$(shell printenv FOO && echo FOO ok)

export FOO BAR

all:
	@printenv FOO
	@printenv BAR
"""
    expect = (
        "FOO ok BAR ok",
        "BAR ok FOO ok"
    )

    p = run.gnumake_string(makefile)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    verify.compare_result_stdout(expect, p)

@pytest.mark.skip("TODO GNU Make 4.3 has different behaviors")
def test_self_export():
    # FOO must be in the environment but empty.
    makefile="""
FOO=$(shell printenv FOO && echo FOO ok)

export FOO

all:
	@printenv FOO
"""
    expect = (
        "FOO ok",
    )

    p = run.gnumake_string(makefile)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    verify.compare_result_stdout(expect, p)

def test_unaccessed_self_reference():
    # a definite self reference but FOO never accessed so who cares
    makefile="""
FOO=$(FOO)

@:;@:
"""
    run.simple_test(makefile)

def test_self_reference():
    # a definite self reference
    makefile="""
FOO=$(FOO)
$(info FOO=$(FOO))
@:;@:
"""

    expect = "*** Recursive variable 'FOO' references itself (eventually)."

    s = run.gnumake_should_fail(makefile)
    assert expect in s, s

    s = run.pymake_should_fail(makefile)
    s_list = s.split("\n")
    assert expect in s_list[-1]

def test_self_reference_rule():
    makefile="""
export FOO=$(FOO)

all: ; @printenv FOO
"""
    expect = "Recursive variable 'FOO' references itself (eventually)."

    s = run.gnumake_should_fail(makefile)
    assert expect in s, s

    s = run.pymake_should_fail(makefile)
    s_list = s.split("\n")
    assert expect in s_list[-1]

