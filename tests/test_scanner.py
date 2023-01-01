#!/usr/bin/env python3

# Finally writing a regression test for ScannerIterator.
#
# davep 16-Nov-2014

from scanner import ScannerIterator
from vline import VChar, VirtualLine

def test1() : 
    input_str = "hello, world"
    input_iter = iter(input_str)
    s = ScannerIterator( input_str, "/dev/null" )
    for c in s:
#        print(c,end="")
        input_c = next(input_iter)
        assert c==input_c, (c,input_c)
#    print()

def test_pushback():
    s = ScannerIterator("hello, world", "/dev/null" )
    assert s.next()=='h'
    assert s.next()=='e'
    s.pushback()
    s.pushback()
    assert s.next()=='h'
    assert s.next()=='e'
    s.pushback()
    s.pushback()
    assert s.lookahead()=='h'
    assert s.next()=='h'
    assert s.next()=='e'
    
def test_state_push_pop():
    s = ScannerIterator("hello, world", "/dev/null" )
    s.push_state()
    for c in s :
        if c==' ':
            break
    assert s.remain()=="world"
    s.pop_state()
    assert s.remain()=='hello, world', s.remain()

def test_lookahead():
    s = ScannerIterator("hello, world", "/dev/null" )
    assert s.lookahead() == 'h'
    next(s)
    assert s.lookahead() == 'e'
    assert s.remain() == "ello, world"

# 20230101 I don't know if I need peek_back() anymore
#def test_peek_back():
#    s = ScannerIterator("hello, world", "/dev/null" )
#    assert next(s) == 'h'
#    assert next(s) == 'e'
#    assert s.peek_back() == 'e'

if __name__=='__main__':
    main()

