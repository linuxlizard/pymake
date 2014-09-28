#!/usr/bin/env python3

# Test Makefile statement
#
#   statement ::=  rule
#             ::=  assignment
#             ::=  directive
#
# Originally inside the parser python itself. Moved to own file.
# davep 27-sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from sm import *
from run_tests import run_tests_list

def run():
    rules_tests = ( 
        # rule LHS
        ( "all:",    RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [])])),
        ( "all::",   RuleExpression( [Expression( [Literal("all")]),RuleOp("::"),PrerequisiteList( [])])),
        # assignment LHS
        ( "all=foo",    AssignmentExpression( [Expression( [Literal("all")]),AssignOp("="),Expression( [Literal("foo")])]) ),
        ( "    all  =", AssignmentExpression( [Expression( [Literal("all")]),AssignOp("="),Expression( [Literal("")])]) ),
        ( "all:=",      AssignmentExpression( [Expression( [Literal("all")]),AssignOp(":="),Expression( [Literal("")])]) ),
        ( "all::=",     AssignmentExpression( [Expression( [Literal("all")]),AssignOp("::="),Expression( [Literal("")])]) ),
        ( "all?=",      AssignmentExpression( [Expression( [Literal("all")]),AssignOp("?="),Expression( [Literal("")])]) ),
        ( "all?=",      AssignmentExpression( [Expression( [Literal("all")]),AssignOp("?="),Expression( [Literal("")])]) ),
        ( "all+=",      AssignmentExpression( [Expression( [Literal("all")]),AssignOp("+="),Expression( [Literal("")])]) ),
        ( "$(all)+=foo",    AssignmentExpression( [Expression( [Literal(""),VarRef( [Literal("all")]),Literal("")]),AssignOp("+="),Expression( [Literal("foo")])]) ),
        ( "qq$(all)+=foo",    AssignmentExpression( [Expression( [Literal("qq"),VarRef( [Literal("all")]),Literal("")]),AssignOp("+="),Expression( [Literal("foo")])]) ),
        ( "qq$(all)qq+=foo",    AssignmentExpression( [Expression( [Literal("qq"),VarRef( [Literal("all")]),Literal("qq")]),AssignOp("+="),Expression( [Literal("foo")])]) ),

        # kind of ambiguous
        ( "this is a test = ",           AssignmentExpression( [Expression( [Literal("this is a test")]),AssignOp("="),Expression( [Literal("")])])  ),

        ( "  this   is   a   test   = ", AssignmentExpression( [Expression( [Literal("this   is   a   test")]),AssignOp("="),Expression( [Literal("")])])  ),

        ( "this$(is) $a $test = ",      AssignmentExpression( [Expression( [Literal("this"),VarRef( [Literal("is")]),Literal(" "),VarRef( [Literal("a")]),Literal(" "),VarRef( [Literal("t")]),Literal("est")]),AssignOp("="),Expression( [Literal("")])])  ),

        ( "this $(  is  ) $a $test = ",  AssignmentExpression( [Expression( [Literal("this "),VarRef( [Literal("  is  ")]),Literal(" "),VarRef( [Literal("a")]),Literal(" "),VarRef( [Literal("t")]),Literal("est")]),AssignOp("="),Expression( [Literal("")])])  ),

        ( "this$(is)$a$(test) : ",       RuleExpression( [Expression( [Literal("this"),VarRef( [Literal("is")]),Literal(""),VarRef( [Literal("a")]),Literal(""),VarRef( [Literal("test")]),Literal("")]),RuleOp(":"),PrerequisiteList( [])]) ),

        ( "this is a test : ",           RuleExpression( [Expression( [Literal("this"),Literal("is"),Literal("a"),Literal("test")]),RuleOp(":"),PrerequisiteList( [])])  ),

        ( "  this   is   a   test   : ", RuleExpression( [Expression( [Literal("this"),Literal("is"),Literal("a"),Literal("test")]),RuleOp(":"),PrerequisiteList( [])])  ),

        ( "this $(is) $a $test : ",      RuleExpression( [Expression( [Literal("this"),Literal(""),VarRef( [Literal("is")]),Literal(""),Literal(""),VarRef( [Literal("a")]),Literal(""),Literal(""),VarRef( [Literal("t")]),Literal("est")]),RuleOp(":"),PrerequisiteList( [])]) ),

        # yadda yadda yadda
        ( "override all=foo",    AssignmentExpression( [Expression( [Literal("override all")]),AssignOp("="),Expression( [Literal("foo")])]) ),

        ( "all:",       RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [])]) ),

        ( "all:foo",    RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [Literal("foo")])]) ),

        ( "   all :   foo    ", RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [Literal("foo")])]) ),
        ( "   all :   foo#comment    ", RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [Literal("foo")])]) ),

        # this line is a happy train wreck!
        ( r"""   all :\
        foo#comment\
        commentcomment
        ; bar""", RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [Literal("foo")])]) ),

        # how about backslashes? 
        ( r"""all : test-backslash-semicolon test-backslash-recipes lots-of-fore-whitespace\
lots-of-aft-whitespace backslash-in-string backslash-in-string-echo\
backslash-eol backslash-o-rama backslash-space-eol assignment split-assignment \
split-prereqs-with-backslashes this-is-a-rule-with-backslashes \
 ; @echo $@""", 
        RuleExpression( [Expression( [Literal("all")]),RuleOp(":"),PrerequisiteList( [Literal("test-backslash-semicolon"),Literal("test-backslash-recipes"),Literal("lots-of-fore-whitespacelots-of-aft-whitespace"),Literal("backslash-in-string"),Literal("backslash-in-string-echobackslash-eol"),Literal("backslash-o-rama"),Literal("backslash-space-eol"),Literal("assignment"),Literal("split-assignment"),Literal("split-prereqs-with-backslashes"),Literal("this-is-a-rule-with-backslashes")])]) ),

        # backslashes from ffmpeg
        ( r"""SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \
               HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \
               ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \
               ALTIVEC-OBJS VIS-OBJS                                     \
               MMX-OBJS YASM-OBJS                                        \
               MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \
               OBJS HOSTOBJS TESTOBJS
               """, () ),

        # from busybox
        ( """
SUBARCH := $(shell echo $(SUBARCH) | sed -e s/i.86/i386/ -e s/sun4u/sparc64/ \
					 -e s/arm.*/arm/ -e s/sa110/arm/ \
					 -e s/s390x/s390/ -e s/parisc64/parisc/ \
					 -e s/ppc.*/powerpc/ -e s/mips.*/mips/ )
                                         """, () ),

        ( "the quick brown fox jumped over lazy dogs : ; ", 
            ("the", "quick", "brown", "fox","jumped","over","lazy","dogs",":", ";", )),
        ( '"foo" : ; ',     ('"foo"',":",";")),
        ('"foo qqq baz" : ;',   ('"foo',"qqq",'baz"',":",";")),
        (r'\foo : ; ',  (r'\foo', ':', ';')),
        (r'foo\  : ; ', (r'foo ',':', ';',)),
        ('@:;@:',       ('@',':',';','@:',)),
        ('I\ have\ spaces : ; @echo $@',    ('I have spaces',':',';','@echo $@',)),
        ('I\ \ \ have\ \ \ three\ \ \ spaces : ; @echo $@', ('I   have   three   spaces',':', ';', '@echo $@' )),
        ('I$(CC)have$(LD)embedded$(OBJ)varref : ; @echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',
            ( 'I', '$(', 'CC', ')', 'have', '$(', 'LD',')','embedded','$(','OBJ',')','varref',':',';',
              '@echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',)
        ),

        # implicit pattern rule TODO
#        ('$(filter %.o,$(files)): %.o: %.c',    
#                    ( '', '$(','filter %.o,',
#                            '$(','files',')','',
#                       ')','',
#                          ':','%.o',':','%.c',)),

#        ('aa$(filter %.o,bb$(files)cc)dd: %.o: %.c',    
#                    ( 'aa', '$(','filter %.o,bb',
#                            '$(','files',')','cc',
#                       ')','dd',
#                          ':','%.o',':','%.c',)),
        ("double-colon1 :: colon2", ("double-colon1","::","colon2")),
        ( "%.tab.c %.tab.h: %.y", ("%.tab.c","%.tab.h",":","%.y")),
        ("foo2:   # hello there; is this comment ignored?",("foo2",":")),
        ("$(shell echo target $$$$) : $(shell echo prereq $$$$)",
            ("","$(","shell echo target $$$$",")","",":","$(shell echo prereq $$$$)",),)
    )

    run_tests_list(rules_tests,tokenize_assignment_or_rule)

#    for test in rules_tests : 
#        s,result = test
#        my_iter = ScannerIterator(s)
#        tokens = tokenize_assignment_or_rule(my_iter)
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

#    for test in rules_tests : 
#        s,v = test
#        print("test={0}".format(s))
#        my_iter = ScannerIterator(s)
#
#        tokens = tokenize_assignment_or_rule(my_iter)
#        print( "tokens={0}".format(str(tokens)) )
#        print("\n")
##    run_tests_list( rules_tests, tokenize_assignment_or_rule)

if __name__=='__main__':
    run()

