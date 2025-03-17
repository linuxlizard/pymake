# SPDX-License-Identifier: GPL-2.0

import os

import pytest

import run

_debug = True

#  printenv will have non-zero exit code if the variable doesn't exist. 
#  The subprocess.run_test() will raise error on non-zero exit.

def run_test(makefile, expect, extra_args=None, extra_env=None):
    output = run.gnumake_string(makefile, extra_args, extra_env)
    if _debug:
        print("gnumake output=>>>",output, "<<<")
    run.verify(output,expect)
    output = run.pymake_string(makefile, extra_args, extra_env)
    if _debug:
        print("pymake output=>>>",output, "<<<")
    run.verify(output,expect)

def test1():
    makefile = """
CC=gcc
export CC
all:
	printenv CC
"""
    expect = ("printenv CC", "gcc")
    run_test(makefile,expect)

def test_simple_assign():
    makefile = """
export CC=gcc
all:
	printenv CC
"""
    expect = ("printenv CC", "gcc")
    run_test(makefile,expect)

def test_multiple_assign():
    makefile = """
export CC=gcc
export CFLAGS=-Wall
all:
	printenv CC CFLAGS
"""
    expect = ("printenv CC CFLAGS", "gcc", "-Wall")
    run_test(makefile,expect)

def test_multiple_export():
    makefile = """
CC=gcc
CFLAGS=-Wall
export CC CFLAGS
all:
	printenv CC CFLAGS
"""
    expect = ("printenv CC CFLAGS", "gcc", "-Wall")
    run_test(makefile, expect)

def test_whitespace():
    makefile = """
            export              CC =  gcc
		export	CFLAGS	=	-Wall
all:
	printenv CC CFLAGS
"""
    expect = ("printenv CC CFLAGS", "gcc", "-Wall")
    run_test(makefile, expect)

def test_export_everything():
    makefile = """
CC=gcc
CFLAGS=-Wall
export
CXXFLAGS=-std=c++20
all:
	printenv CC CFLAGS CXXFLAGS
"""
    # make sure to have a variable set after the export statement to verify new
    # vars are marked for export, too
    expect = ("printenv CC CFLAGS CXXFLAGS", "gcc", "-Wall", "-std=c++20")
    run_test(makefile, expect)

def test_export_environment_vars():
    # All environment variables will be marked for export.
    # "By default, only variables that came from the environment or the
    # command line are passed to recursive invocations."
    #  -- GNU Make manual  Version 4.3 Jan 2020
    makefile = """
CC=gcc
CFLAGS=-Wall
export
all:
	printenv CC CFLAGS
"""
    # environment vars do not override internal vars
    os.environ["CC"] = "xcc"
    expect = ("printenv CC CFLAGS", "gcc", "-Wall")
    run_test(makefile, expect)
    del os.environ["CC"]

def test_export_varname():
    # "export" isn't a keyword so can be used as a variable name, too
    # (/me shakes fist at Make)
    makefile = """
export:=42
$(info export=$(export))
all:
"""
    expect = ("export=42",)
    run_test(makefile, expect)

def test_double_export():
    # can only have one expression per export
    makefile="""
export FOO=BAR BAZ=QUX
all:
	printenv FOO
"""
    expect = ("printenv FOO", "BAR BAZ=QUX",)
    run_test(makefile, expect)

def test_env_var_export():
    # "By default, only variables that came from the environment or the
    # command line are passed to recursive invocations."
    # -- GNU Make manual  Version 4.3 Jan 2020

    # verify all environment variables are exported
    makefile = """
FOO=bar
export FOO
all:
	printenv FOO BAR
"""
    expect = ("printenv FOO BAR", "bar", "baz")
    run_test(makefile, expect, extra_env={"BAR":"baz"})

def test_command_line_export():
    # "By default, only variables that came from the environment or the
    # command line are passed to recursive invocations."
    # -- GNU Make manual  Version 4.3 Jan 2020

    # verify all command line args are exported
    makefile = """
FOO=bar
export FOO
all:
	printenv FOO BAR
"""
    expect = ("printenv FOO BAR", "bar", "baz")
    run_test(makefile, expect, extra_args=("BAR=baz",))

def test_command_line_override():
    # command line var value overrides file var
    makefile = """
CFLAGS=-Wall
export CFLAGS
all:
	printenv CFLAGS
"""
    expect = ("printenv CFLAGS", "-Wextra")
    run_test(makefile, expect, extra_args=("CFLAGS=-Wextra",))

def test_export_define():
    # an old error makefile from way back
    makefile="""
# make 3.81 "export define" not allowed ("missing separator")
# make 3.82 works
# make 4.0  works
export define foo
bar
endef
$(info $(call foo))

@:;@:
"""
    # XXX this test won't work in pymake until I implement 'define'
    expect = ("bar",)
#    run_test(makefile, expect)

def test_export_equals():
    makefile="""
# looks like an assignment 
export = a b c d 
ifndef export
$(error export should be a b c d)
endif
ifdef export
$(info export=$(export))
endif
@:;@:
"""
    expect = ('export=a b c d',)
    run_test(makefile, expect)

def test_simple_unexport():
    makefile = """
CC=gcc
export CC
unexport CC
all:
	@printenv CC || echo no CC for you
"""
    expect=("no CC for you",)
    run_test(makefile,expect)

def test_unexport_variables():
    # unexport variables explicitly
    makefile = """
CC=gcc
CFLAGS=-g -Wall
export CC
export CFLAGS
unexport CC CFLAGS
all:
	@printenv CC || echo no CC for you
	@printenv CFLAGS || echo no CFLAGS for you
"""
    expect=("no CC for you","no CFLAGS for you")
    run_test(makefile,expect)

def test_global_export():
    makefile = """
export
CC=gcc
CFLAGS=-g -Wall
all:
	@printenv CC
	@printenv CFLAGS
"""
    expect=("gcc","-g -Wall")
    run_test(makefile,expect)

def test_global_unexport():
    makefile = """
export
CC=gcc
CFLAGS=-g -Wall
unexport
all:
	@printenv CC || echo no CC for you
	@printenv CFLAGS || echo no CFLAGS for you
"""
    expect=("no CC for you","no CFLAGS for you")
    run_test(makefile,expect)

def test_specific_unexport():
    # lone export means export everything
    # but lone unexport will undo that
    # lone unexport will not unexport specifically export'd vars
    makefile = """
export
export CC=gcc
CFLAGS=-g -Wall
unexport
all:
	@printenv CC
	@printenv CFLAGS || echo no CFLAGS for you
"""
    expect=("gcc","no CFLAGS for you")
    run_test(makefile,expect)

def test_circular_export():
    makefile="""
FOO=$(shell echo foo)
export FOO
@:; @printenv FOO
"""
    expect = ("foo",)
    run_test(makefile,expect)

def test_export_commandline_var():
    # command line variable assignments always override export status of file
    # variables
    makefile="""
export FOO:=foo
@:; @echo $(FOO)
"""
    expect = ("bar",)
    run_test(makefile, expect, extra_args=("FOO=bar",))
    

def test_export_commandline_var_explicit():
    # command line variable assignments always override export status of file
    # variables
    makefile="""
export FOO:=foo
@:; @echo $(FOO)
"""
    expect = ("bar",)
    # use explicity assign instead of recursive assign
    run_test(makefile, expect, extra_args=("FOO:=bar",))
    
def test_export_before_define():
    makefile="""
export FOO
FOO:=foo
@:; printenv FOO
"""
    run.simple_test(makefile)

def test_unexpert_unknown():
    makefile="""
unexport FOO
@:;@:
"""
    run.simple_test(makefile)

