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
 
def exe(makefile, expect):
    pass

def test1():
    makefile = """
CC:=gcc
$(info CC=$(CC))
@:;@:
"""
    expect = ("CC=gcc",)
    exe(makefile, expect)
