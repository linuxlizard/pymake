# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024-2025 David Poole david.poole@ericsson.com
#
# test the $(eval) function

import run

def test1():
    makefile="""
$(eval FOO:=foo)
ifndef FOO
$(error FOO is missing
endif
ifneq ($(FOO),foo)
$(error FOO is wrong)
endif
@:;@:
"""
    run.simple_test(makefile)

def test_rule():
    makefile="""
$(eval @:;@:)
"""
    run.simple_test(makefile)

def test_two_eval():
    makefile="""
$(eval BAR:=bar)
$(eval FOO:=$(BAR))
ifndef FOO
$(error FOO is missing)
endif
ifneq ($(FOO),bar)
$(error foo is wrong)
endif
@:;@:
"""
    run.simple_test(makefile)

def test_eval_return():
    makefile="""
$(info >>$(eval FOO:=foo)<<)
ifneq ($(FOO),foo)
$(error foo is wrong)
endif
@:;@:
"""
    run.simple_test(makefile)
