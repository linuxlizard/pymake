#!/usr/bin/env python3

# Regression tests for pymake.py
#
# Test Makefile assignment
#
# davep 22-Sep-2014

import sys

from sm import *

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

def assignment_test():

    assignment_tests = ( 
        ("foo=baz",""),
        ("foo=$(baz)",""),
        ("foo=$(baz3) $(baz3) $(baz3)",""),

        # leading spaces discarded, trailing spaces preserved
        ("foo=     $(baz3) $(baz3) $(baz3)",""),
        ("foo= this is a test # this is a comment",""),
        ("foo= this is a test # this is a comment\nbar=baz",""),

        # empty is fine, too
        ( "foo=", ""),
        ( " foo =     ", "" ),

        # assignment done at eol
        ( "foo=$(CC)\nfoo bar baz=$(LD)\n", "" ), 

        ( "today != $(shell date)", "" ),
        ( "this is a test = this is a test", "" ),
    )

    for test in assignment_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )

        # AssignmentExpression :=  Expression AssignOp Expression
        assert isinstance(tokens,AssignmentExpression)
        assert isinstance(tokens[0],Expression)
        assert isinstance(tokens[1],AssignOp)
        assert isinstance(tokens[2],Expression),(type(tokens[2]),)

#        print( "string={0}".format(my_iter))
        print("\n")

if __name__=='__main__':
    assignment_test()

