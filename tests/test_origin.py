#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import tempfile
import subprocess

import run

_debug = True

def test1():
    makefile="""
FOO=bar
$(info $(origin FOO))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "file", output
    
def test_var_undefined():
    makefile="""
$(info $(origin FOO))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "undefined", output

def test_environment_variable():
    makefile="""
$(info $(origin PATH))
@:;@:
"""
    output = run.pymake_string(makefile).strip()
    assert output == "environment", output

def test_command_line():
    makefile="""
$(info $(origin FOO))
@:;@:
"""
    output = run.pymake_string(makefile, extra_args=("FOO=BAR",))
    assert output.strip() == "command line", output

