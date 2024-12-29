#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import tempfile
import subprocess

import run

# TODO  many many more tests

# Following if from the GNU Make Manual :
# GNU make Version 4.3
# January 2020
# 8.10 The origin Function
#
# ‘undefined’ 
# if variable was never defined.
#
# ‘default’
# if variable has a default definition, as is usual with CC and so on. See Section 10.3
# [Variables Used by Implicit Rules], page 119. Note that if you have redefined a
# default variable, the origin function will return the origin of the later definition.
#
# ‘environment’
# if variable was inherited from the environment provided to make.
#
# ‘environment override’
# if variable was inherited from the environment provided to make, and is over-
# riding a setting for variable in the makefile as a result of the ‘-e’ option (see
# Section 9.7 [Summary of Options], page 108).
#
# ‘file’
# if variable was defined in a makefile.
#
# ‘command line’
# if variable was defined on the command line.
#
# ‘override’
# if variable was defined with an override directive in a makefile (see Section 6.7
# [The override Directive], page 70).
#
# ‘automatic’
# if variable is an automatic variable defined for the execution of the recipe for
# each rule (see Section 10.5.3 [Automatic Variables], page 124).
#
def test1():
    makefile="""
FOO=bar
$(info $(origin FOO))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "file", output
    output = run.gnumake_string(makefile).strip()
    assert output == "file", output
    
def test_var_undefined():
    makefile="""
$(info $(origin FOO))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "undefined", output
    output = run.gnumake_string(makefile).strip()
    assert output == "undefined", output

def test_environment_variable():
    makefile="""
$(info $(origin PATH))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "environment", output
    output = run.gnumake_string(makefile).strip()
    assert output == "environment", output

def test_command_line():
    makefile="""
$(info $(origin FOO))
@:;@:
"""
    # "If a variable has been set with a command argument (see Section 9.5 [Overriding Variables],
    # page 107), then ordinary assignments in the makefile are ignored."
    output = run.pymake_string(makefile, extra_args=("FOO=BAR",))
    assert output.strip() == "command line", output
    output = run.gnumake_string(makefile, extra_args=("FOO=BAR",))
    assert output.strip() == "command line", output

def test_default():
    makefile="""
ifneq ($(origin CC),default)
$(error CC origin should be 'default' not '$(origin CC)')
endif

@:;@:
"""
    run.simple_test(makefile)

