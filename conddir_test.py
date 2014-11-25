#!/usr/bin/env python3

# conditional directives
# davep 22-Nov-2024 

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
    assert m=='ifdef FOO\na=b\nendif'

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
    assert m=='ifdef FOO\na=b\nelse\na=d\nendif'

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
    assert m=='ifdef FOO\na=b\nelse\nendif'

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
    assert m=='ifdef FOO\nelse\na=d\nendif'

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
#    ifdef = IfdefDirective(Expression([Literal("FOO")]),[LineBlock([VirtualLine(["a=b"],0),VirtualLine(["c=d"],0),VirtualLine(["e=f"],0)])],[])
#    assert ifdef==c

    assert m=='ifdef FOO\na=b\nc=d\ne=f\nendif'

def main():
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()

if __name__=='__main__':
    main()

