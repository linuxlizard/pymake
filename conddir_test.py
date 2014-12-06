#!/usr/bin/env python3

# conditional directives
# davep 22-Nov-2024 

import pymake
from pymake import (Literal, Expression, ConditionalBlock,
                    ConditionalDirective, IfdefDirective, LineBlock)
from vline import VirtualLine
import run_tests

run = run_tests.run_makefile_string

def round_trip(cond_block,expected_makefile):
    s = str(cond_block)
    print("s=",s)
    m2=eval(s).makefile()
    print(m2)
    assert m2==expected_makefile,m2
    print(m2)

def test1():
    # ifdef FOO 
    # endif
    e = Expression([Literal("FOO")])
    b = ConditionalBlock()
    c = IfdefDirective(e)
    b.add_conditional(c)
    print(b)
    m = b.makefile()
    print(m)
    assert m=='ifdef FOO\nendif'

    s = str(b)
    print("s=",s)
    m2=eval(s).makefile()
    print(m2)
    assert m2=='ifdef FOO\nendif',m2
    print(m2)

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
    assert m=='ifdef FOO\na=b\nendif',m

    s = str(b)
    print("s=",s)
    m2=eval(s).makefile()
    print(m2)
    assert m2=='ifdef FOO\na=b\nendif',m2
    print(m2)

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
    print(b)
    m = b.makefile()
    print(m)
    expect = 'ifdef FOO\na=b\nelse\na=d\nendif'
    assert m==expect,m
    round_trip(b,expect)

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
    expect = 'ifdef FOO\na=b\nelse\nendif'
    assert m==expect,m
    round_trip(b,expect)

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
    expect='ifdef FOO\nelse\na=d\nendif'
    assert m==expect,m
    round_trip(b,expect)

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
    m = b.makefile()
    print(m)
    expect='ifdef FOO\na=b\nc=d\ne=f\nendif'
    assert m==expect,m
    round_trip(b,expect)

def test7():
    s = """\
ifdef FOO
a=b
else#foobarbaz
a=c
endif
"""
    run(s,"ifdef FOO\na=b\nelse\na=c\nendif")

def test8():
    s = """\
ifdef FOO
    ifdef BAR
        ifdef BAZ
        endif
    endif
endif
"""
    r = """\
ifdef FOO
ifdef BAR
ifdef BAZ
endif
endif
endif"""
    run(s,r)

def test9():
    s = """\
ifdef NOTDEF
    this is a bunch of crap
    that makefile will ignore
    ifeq ($a,$b)
        this should still be ignored
    endif
endif
"""
    r = """\
ifdef NOTDEF
    this is a bunch of crap
    that makefile will ignore
ifeq ($(a),$(b))
        this should still be ignored
endif
endif"""
    run(s,r)

def test10():
    s="""\
ifdef FOO
else
    ifdef BAR
    endif
endif
"""
    r="""\
ifdef FOO
else
ifdef BAR
endif
endif"""
    run(s,r)

def test11():
    s="""\
ifdef FOO
    a=b foo
    b=c foo
    d=e foo
else
    ifdef XYZ

    else ifdef BAR
        e=f bar
        f=g bar
        g=h bar
        ifdef BAZ
            h=i baz
            i=j baz
            j=k baz
        else
        endif
    else ifdef BAZ
        ifndef QQQQ
        else
        endif
    else
    endif
endif
"""
    r="""\
ifdef FOO
    a=b foo
    b=c foo
    d=e foo
else
ifdef XYZ
else ifdef BAR
        e=f bar
        f=g bar
        g=h bar
ifdef BAZ
            h=i baz
            i=j baz
            j=k baz
else
endif
else ifdef BAZ
ifndef QQQQ
else
endif
else
endif
endif"""
    run(s,r)

if __name__=='__main__':
    from run_tests import runlocals
    runlocals(locals())
#    test9()


