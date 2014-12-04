#!/usr/bin/env python3

# conditional directives
# davep 22-Nov-2024 

import pymake
from pymake import (Literal, Expression, ConditionalBlock,
                    ConditionalDirective, IfdefDirective, LineBlock)
from vline import VirtualLine
import run_tests

run = run_tests.run_makefile_string

def test1():
    # ifdef FOO 
    # endif
    e = Expression([Literal("FOO")])
    b = ConditionalBlock()
    c = IfdefDirective(e)
    b.add_conditional(c)
    print(b)
    m = b.makefile()
    print(m,end="")
    assert m=='ifdef FOO\nendif\n'

    s = str(b)
    print("s=",s)
    m2=eval(s).makefile()
    assert m2=='ifdef FOO\nendif\n'
    print(m2,end="")

def test2():
    # ifdef FOO
    # a=b
    # endif
    e = Expression([Literal("FOO")])
    v = VirtualLine.from_string("a=b\n")
    lb = LineBlock([v])
    c = IfdefDirective(e)
    b = ConditionalBlock()
    b.add_conditional(c)
    b.add_block(lb)
    print(b)
    m = b.makefile()
    print(m)
    assert m=='ifdef FOO\na=b\nendif\n',m

def test3():
    # ifdef FOO
    # a=b
    # else
    # a=d
    # endif
    e = Expression([Literal("FOO")])
    c = IfdefDirective(e)
    v1 = VirtualLine.from_string("a=b\n")
    v2 = VirtualLine.from_string("a=d\n")
    lb1 = LineBlock([v1])
    lb2 = LineBlock([v2])
    b = ConditionalBlock()
    b.add_conditional(c)
    b.add_block(lb1)
    b.start_else()
    b.add_block(lb2)
    print(b.cond_expr)
    print(b.cond_blocks)
    print(b)
    m = b.makefile()
    print(m)
    assert m=='ifdef FOO\na=b\nelse\na=d\nendif\n',m

def test4():
    # ifdef FOO
    # a=b
    # else
    # endif
    e = Expression([Literal("FOO")])
    v1 = VirtualLine.from_string("a=b\n")
    lb1 = LineBlock([v1])
    c = IfdefDirective(e)
    b = ConditionalBlock()
    b.add_conditional(c)
    b.add_block(lb1)
    b.start_else()
    print(b)
    m = b.makefile()
    print(m)
    assert m=='ifdef FOO\na=b\nelse\nendif\n'

def test5():
    # ifdef FOO
    # else
    # a=d
    # endif
    e = Expression([Literal("FOO")])
    v2 = VirtualLine.from_string("a=d\n")
    lb1 = LineBlock([v2])
    c = IfdefDirective(e)
    b = ConditionalBlock()
    b.add_conditional(c)
    b.start_else()
    b.add_block(lb1)
    print(b)
    m = b.makefile()
    print(m)
    assert m=='ifdef FOO\nelse\na=d\nendif\n'

def test6():
    # ifdef FOO
    # a=b
    # c=d
    # e=f
    # endif
    e = Expression([Literal("FOO")])
    v = [ VirtualLine.from_string("a=b\n"),
          VirtualLine.from_string("c=d\n"),
          VirtualLine.from_string("e=f\n") 
        ]
    lb = LineBlock(v)
    c = IfdefDirective(e)
    b = ConditionalBlock()
    b.add_conditional(c)
    b.add_block(lb)
    print(b)
#    print(eval(s))
#    s = eval(s)
#    print(s)
#    s = eval(str(s))
    m = b.makefile()
    print(m)

    assert m=='ifdef FOO\na=b\nc=d\ne=f\nendif\n'

def test7():
    s = """\
ifdef FOO
a=b
else#foobarbaz
a=c
endif
"""
    run(s,"ifdef FOO\na=b\nelse\na=c\nendif\n")

if __name__=='__main__':
#    from run_tests import runlocals
#    runlocals(locals())
    test1()


