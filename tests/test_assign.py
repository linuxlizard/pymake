import run

# Test all the ways we can assign a variable
#
# from the gnu make pdf:
# immediate = deferred
# immediate ?= deferred
# immediate := immediate
# immediate ::= immediate
# immediate += deferred or immediate
# immediate != immediate
 
def run_test(makefile, expect):
    out = run.gnumake_string(makefile)
    print("out=",out)
    assert expect==out, out

    out = run.pymake_string(makefile)
    print("out=",out)

def test1():
    makefile = """
CC:=gcc
$(info CC=$(CC))
@:;@:
"""
    expect = "CC=gcc"
    run_test(makefile, expect)

def test_add():
    makefile = """
FOO:=foo
FOO+=bar
$(info FOO=$(FOO))
@:;@:
"""
    expect = "FOO=foo bar"
    run_test(makefile, expect)

