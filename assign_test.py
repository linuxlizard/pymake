#!/usr/bin/env python3

# Regression tests for pymake.py
#
# Test Makefile assignment
#
# davep 22-Sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from pymake import *
from run_tests import run_tests_list

def run():

    assignment_tests = ( 
        ("foo=baz",AssignmentExpression( [Expression( [Literal("foo")]),AssignOp("="),Expression( [Literal("baz")])]) ),
        ("foo=$(baz)",AssignmentExpression( [Expression( [Literal("foo")]),AssignOp("="),Expression( [Literal(""),VarRef( [Literal("baz")]),Literal("")])]) ),
        ("foo=$(baz3) $(baz3) $(baz3)", AssignmentExpression( [Expression( [Literal("foo")]),AssignOp("="),Expression( [Literal(""),VarRef( [Literal("baz3")]),Literal(" "),VarRef( [Literal("baz3")]),Literal(" "),VarRef( [Literal("baz3")]),Literal("")])]) ),

        ( "foo=barbazblahblahblah", AssignmentExpression( [Expression( [Literal("foo")]),AssignOp("="),Expression( [Literal("barbazblahblahblah")])]) ),

        ( r"trailing-slash\ =", 
            AssignmentExpression( [Expression( [Literal("trailing-slash\\")]),
                                                AssignOp("="),
                                                Expression( [Literal("")])]) ),
        ( r'\% = percent', 
            AssignmentExpression( [Expression( [Literal("\\%")]),
                                                AssignOp("="),
                                                Expression( [Literal("percent")])]) ),
        ( r'%\ = percent', 
            AssignmentExpression( [Expression( [Literal("%\\")]),
                                                AssignOp("="),
                                                Expression( [Literal("percent")])]) ),


        ( r"embedded-slash-o-rama\ =\ foo\ bar\ baz\ blahblahblah", 
            AssignmentExpression( [Expression( [Literal("embedded-slash-o-rama\\")]),
                                                AssignOp("="),
                                                Expression( [Literal("\\ foo\\ bar\\ baz\\ blahblahblah")])]) ),

        # this is a hot mess
        (r"""slash-o-rama\
= foo\
bar\
baz\
blahblahblah
""", 
            AssignmentExpression( [Expression( [Literal("slash-o-rama")]),AssignOp("="),Expression( [Literal("foo bar baz blahblahblah")])]) ),

        # trailing spaces still preserved?
        (r"""trailing-spaces-backslashes\
        = foo \
        bar \
        baz     \
        """, 
            AssignmentExpression( [Expression( [Literal("trailing-spaces-backslashes")]),
                                    AssignOp("="),
                                    Expression( [Literal("foo bar baz ")])]) ),

        ( # yikes
r"""more-fun-in-assign\
=           \
    the     \
    leading \
    and     \
    trailing\
    white   \
    space   \
    should  \
    be      \
    eliminated\
    \
    \
    \
    including \
    \
    \
    blank\
    \
    \
    lines
""", 
        AssignmentExpression( [Expression( [Literal("more-fun-in-assign")]),
                               AssignOp("="),
                               Expression( [Literal("the leading and trailing white space should be eliminated including blank lines")])]) ),

        # literal backslashes in the RHS
        ( r"""literal-backslash\
                = \
                foo\bar\baz\
                blahblahblah""", AssignmentExpression([Expression([Literal("literal-backslash")]),AssignOp("="),Expression([Literal("foo\\bar\\baz blahblahblah")])]) ),

        # leading spaces discarded, trailing spaces preserved
        ("foo=     $(baz3) $(baz3) $(baz3)",
            AssignmentExpression([Expression([Literal("foo")]),AssignOp("="),Expression([Literal(""),VarRef([Literal("baz3")]),Literal(" "),VarRef([Literal("baz3")]),Literal(" "),VarRef([Literal("baz3")]),Literal("")])])
        ),

        ("foo= this is a test # this is a comment",
            AssignmentExpression([Expression([Literal("foo")]),AssignOp("="),Expression([Literal("this is a test ")])])),

        # empty is fine, too
        ( "foo=", AssignmentExpression([Expression([Literal("foo")]),AssignOp("="),Expression([Literal("")])])),
        ( " foo =     ", AssignmentExpression([Expression([Literal("foo")]),AssignOp("="),Expression([Literal("")])]) ),

        # assignment done at eol
        ( "foo=$(CC)\n", 
            AssignmentExpression([Expression([Literal("foo")]),AssignOp("="),Expression([Literal(""),VarRef([Literal("CC")]),Literal("")])])
        ), 

        ( "today != $(shell date)", 
            AssignmentExpression([Expression([Literal("today")]),AssignOp("!="),Expression([Literal(""),VarRef([Literal("shell date")]),Literal("")])]) 
        ),

        ( "this is a test = this is a test", 
            AssignmentExpression([Expression([Literal("this is a test")]),AssignOp("="),Expression([Literal("this is a test")])])
        ),

        # from ffmpeg
        ( "LDLIBS := $(shell pkg-config --libs $(FFMPEG_LIBS)) $(LDLIBS)", 
            AssignmentExpression([Expression([Literal("LDLIBS")]),AssignOp(":="),Expression([Literal(""),VarRef([Literal("shell pkg-config --libs "),VarRef([Literal("FFMPEG_LIBS")]),Literal("")]),Literal(" "),VarRef([Literal("LDLIBS")]),Literal("")])])
        ),

        ( " MANPAGES    = $(PROGS-yes:%=doc/%.1)    $(PROGS-yes:%=doc/%-all.1)    $(COMPONENTS-yes:%=doc/%.1)    $(LIBRARIES-yes:%=doc/%.3)", 
       AssignmentExpression([Expression([Literal("MANPAGES")]),AssignOp("="),Expression([Literal(""),VarRef([Literal("PROGS-yes:%=doc/%.1")]),Literal("    "),VarRef([Literal("PROGS-yes:%=doc/%-all.1")]),Literal("    "),VarRef([Literal("COMPONENTS-yes:%=doc/%.1")]),Literal("    "),VarRef([Literal("LIBRARIES-yes:%=doc/%.3")]),Literal("")])]) 
        ),
    )

    run_tests_list(assignment_tests,tokenize_statement)


if __name__=='__main__':
    run()

