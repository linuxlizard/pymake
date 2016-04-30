#!/usr/bin/python

import pymake
from pymake import *
import run_tests

run = run_tests.run_makefile_string

def test1():
    s = """\
define foo
    foo foo foo
endef
"""
    run(s,s.strip())

if __name__=='__main__':
    from run_tests import runlocals
    runlocals(locals())

