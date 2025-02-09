# SPDX-License-Identifier: GPL-2.0

import pytest

import run

# run both make and pymake
# these ifdef tests are simple enough for a pass/fail
def run_test(makefile):
    run.simple_test(makefile)

def test_ifdef_mixed_build():
    # If the value of that variable has a non-empty value, the text-if-true
    # is effective; otherwise, the text-if-false, if any, is effective. Variables
    # that have never been defined have an empty value."
    #
    # My bug discovered while parsing linux kernel makefile.  A var must exist
    # AND be non-empty for ifdef to eval true.
    s = """
mixed-build:=
ifdef mixed-build
$(error should not see this)
endif
@:;@:
"""
    run_test(s)

def test_ifdef_simple():
    s = """
foo:=1
ifdef foo
else
$(error should have found foo)
endif
@:;@:
"""
    run.pymake_string(s)

def test_ifndef_simple():
    s = """
foo:=1
ifndef foo
$(error should have found foo)
endif
@:;@:
"""
    run.pymake_string(s)

def test_ifdef_empty():
    s = """
foo:=
ifdef foo
$(error should not have found foo)
endif
@:;@:
"""
    run.pymake_string(s)

def test_ifdef_trailing_whitespace():
    # six spaces after 'foo:='
    s = """
foo:=      
ifdef foo
$(error should not have found foo)
endif
@:;@:
"""
    run.pymake_string(s)

def test_ifdef_trailing_tabs():
    s = """
foo:=			
ifdef foo
$(error should not have found foo)
endif
@:;@:
"""
    run.pymake_string(s)


def test_ifdef_empty_recursive_assign():
    s = """
foo=
ifdef foo
$(error should not have found foo)
endif
@:;@:
"""
    run.pymake_string(s)

