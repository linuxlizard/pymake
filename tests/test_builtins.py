#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

# TODO just getting started with this file
# I need to implement ifdef/ifndef first.

import run

_debug = True

def test1():
    makefile = """
ifndef MAKE_VERSION
$(error missing MAKE_VERSION)
endif

$(info MAKE_VERSION=$(MAKE_VERSION))
@:;@:
"""
    out1 = run.makefile_string(makefile).strip()
    assert out1=="MAKE_VERSION=4.3"

def test_variables():
    makefile = """
ifndef .VARIABLES
$(error missing .VARIABLES)
endif

$(info $(.VARIABLES))
$(info $(origin .VARIABLES))
@:;@:
"""
    out1 = run.makefile_string(makefile)
    fields = out1.split("\n")
    assert fields[1] == "default"

