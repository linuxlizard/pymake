#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import run

def test_simple():
    makefile="""
$(info .SHELLFLAGS=$(.SHELLFLAGS))
@:;@:
"""
    a = run.gnumake_string(makefile)

    b = run.pymake_string(makefile)

    assert a==b

# the -x flag will echo the command to stderr before executing it
# (very useful when debugging)
def test_x_flag():
    makefile="""
.SHELLFLAGS+=-x
$(info .SHELLFLAGS=$(.SHELLFLAGS))
top:
	echo .SHELLFLAGS=$(.SHELLFLAGS)
"""
    a = run.gnumake_string(makefile)

    b = run.pymake_string(makefile)

    assert a==b

