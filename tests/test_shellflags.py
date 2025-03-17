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

def test_x_flag():
    makefile="""
.SHELLFLAGS+=-x
$(info .SHELLFLAGS=$(.SHELLFLAGS))
@:;@:
"""
    a = run.gnumake_string(makefile)

    b = run.pymake_string(makefile)

    assert a==b

