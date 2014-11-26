#!/usr/bin/env python3

# conditional directives
# davep 22-Nov-2024 

import pymake
from pymake import (Literal, Expression, ConditionalDirective, IfdefDirective,
                    LineBlock)
from vline import VirtualLine

def test1():
    # ifdef FOO 
    # endif
    e = Expression([Literal("FOO")])
    c = IfdefDirective(e,[])
    s = str(c)
    print(s)
    print(eval(s))
    m = c.makefile()
    print(m)
    assert m=='ifdef FOO\nendif'

def test2():
    # ifdef FOO
    # a=b
    # endif
    e = Expression([Literal("FOO")])
    v = VirtualLine.from_string("a=b\n")
    b = LineBlock([v])
    c = IfdefDirective(e,[b])
    print(c)
    m = c.makefile()
    print(m)
    assert m=='ifdef FOO\n    a=b\nendif',m

def test3():
    # ifdef FOO
    # a=b
    # else
    # a=d
    # endif
    e = Expression([Literal("FOO")])
    v1 = VirtualLine.from_string("a=b\n")
    v2 = VirtualLine.from_string("a=d\n")
    b1 = LineBlock([v1])
    b2 = LineBlock([v2])
    c = IfdefDirective(e,[b1],[b2])
    print(c)
    m = c.makefile()
    print(m)
    assert m=='ifdef FOO\n    a=b\nelse\n    a=d\nendif',m

def test4():
    # ifdef FOO
    # a=b
    # else
    # endif
    e = Expression([Literal("FOO")])
    v1 = VirtualLine.from_string("a=b\n")
    b1 = LineBlock([v1])
    b2 = LineBlock([])
    c = IfdefDirective(e,[b1],[b2])
    print(c)
    m = c.makefile()
    print(m)
    assert m=='ifdef FOO\n    a=b\nelse\nendif'

def test5():
    # ifdef FOO
    # else
    # a=d
    # endif
    e = Expression([Literal("FOO")])
    v2 = VirtualLine.from_string("a=d\n")
    b1 = LineBlock([])
    b2 = LineBlock([v2])
    c = IfdefDirective(e,[],[b2])
    print(c)
    m = c.makefile()
    print(m)
    assert m=='ifdef FOO\nelse\n    a=d\nendif'

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
    b = LineBlock(v)
    c = IfdefDirective(e,[b])
    s = str(c)
#    print(s)
#    print(eval(s))
#    s = eval(s)
#    print(s)
#    s = eval(str(s))
    m = c.makefile()
    print(m)

    assert m=='ifdef FOO\n    a=b\n    c=d\n    e=f\nendif'

def test7():
    s = """\
ifdef FOO
a=b
else#foobarbaz
a=c
endif
"""
    makefile = pymake.parse_makefile_string(s)

if __name__=='__main__':
    from run_tests import runlocals
    runlocals(locals())

