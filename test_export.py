#!/usr/bin/env python3

from run_tests import run_makefile_string, runlocals

def test1():
	s="""\
export f
"""
	run_makefile_string(s,"export f")


def test2():
	s="""\
export f# foo foo foo
"""
	run_makefile_string(s,"export f")


def test3():
	s = """\
export
"""
	run_makefile_string(s,"export")

def test4():
	s = """\
export \\
a\\
b\\
c
"""
	run_makefile_string(s,"export a b c")

def test5():
	s = """
	export  a   b   c  d	e f g
"""
	run_makefile_string(s,"export a   b   c  d	e f g")

def test6():
	s = """
export $(firstword $(FOO))
"""
	run_makefile_string(s,"export $(firstword $(FOO))")

def test7():
	s = """
	export FOO:=BAR
"""
	run_makefile_string(s,"export FOO:=BAR")

if __name__=='__main__':
	runlocals(locals())

