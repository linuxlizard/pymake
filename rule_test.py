#!/usr/bin/env python3

# Regression tests for pymake.py
#
# Test Makefile rules
#
# davep 22-Sep-2014

import sys

from sm import *

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

def rule_test() :
    # parse a full rule! 
    rule_test_list = ( 
        # normal rules
        ( "all : this is a test", RuleExpression(
                                    ( Expression( (Literal("all"),) ),
                                      RuleOp(":"),
                                      PrerequisiteList( 
                                        ( Literal("this"),Literal("is"),Literal("a"),Literal("test"), )
                                      ),
                                    ),
                                  ),
                            ),

        ( "all : ", RuleExpression(
                        ( Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( 
                                ( Literal(""), ) 
                          ),
                        ),
                    ),
                ),

        # no whitespace
        ( "all:", RuleExpression(
                        ( Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( 
                                ( Literal(""), ) 
                          ),
                        ),
                    ),
                ),
        # lots of whitespace
        ( "          all          :                                      ", 
                    RuleExpression(
                        ( Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( 
                                ( Literal(""), ) 
                          ),
                        ),
                    ),
                ),
        # target specific variables
        ( "all : CC=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC=|gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("|gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC=:gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal(":gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC:=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp(":="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC::=gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("::="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC+=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("+="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        # *= not in assignment_operators
        ( "all : CC*=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC*"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC!=gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("!="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        # trailing spaces should be preserved
        ( "all : CC=gcc  # this is a comment",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      # trailing spaces are preserved
                                      Expression( (Literal("gcc  "),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "hello there all you rabbits : hello there all you rabbits", 
                          RuleExpression(
                                ( Expression( (Literal("hello"),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits"), ), ),
                                  RuleOp(":"),
                                  PrerequisiteList( 
                                    ( Literal("hello"),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits"), ),
                                  ),
                                ),
                          ),
                     ),

        # I'm starting to use the output of the tokenizer, visually verified, as the verification string. 
        # I hope I don't regret this. :-O   davep 23-Sep-2014

        ( "$(hello there all you) rabbits : hello there all you rabbits", RuleExpression( [Expression( [Literal(""),VarRef( [Literal("hello there all you")]),Literal(""),Literal("rabbits")]),RuleOp(":"),PrerequisiteList( [Literal("hello"),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits")])]) ),

        ( "$(hello there all you) rabbits : $(hello) there all you rabbits", RuleExpression( [Expression( [Literal(""),VarRef( [Literal("hello there all you")]),Literal(""),Literal("rabbits")]),RuleOp(":"),PrerequisiteList( [Literal(""),VarRef( [Literal("hello")]),Literal(""),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits")])]) ),

        ( "$(hello $(there $(all $(you) rabbits))) : $(hello) there all you rabbits", 
                        RuleExpression( [Expression( [Literal(""),VarRef( [Literal("hello "),VarRef( [Literal("there "),VarRef( [Literal("all "),VarRef( [Literal("you")]),Literal(" rabbits")]),Literal("")]),Literal("")]),Literal("")]),RuleOp(":"),PrerequisiteList( [Literal(""),VarRef( [Literal("hello")]),Literal(""),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits")])])
        ),

        ( "all : ; @echo $@", 
                    RuleExpression(
                        [ Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( [] ),
                        ],
                    ),
            ),

        ( "all:foo   # this is a comment",  
                    RuleExpression(
                        [ Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( [ Literal("foo"), ] ),
                        ],
                    ),
            ),
        ( "all : foo ; @echo $@", 
                    RuleExpression(
                        [ Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( [ Literal("foo"), ] ),
                        ],
                    ),
            ),
        
        # from ffmpeg
        ( "doc/%-all.html: TAG = HTML",
            RuleExpression( [Expression( [Literal("doc/%-all.html")]),RuleOp(":"),AssignmentExpression( [Expression( [Literal("TAG")]),AssignOp("="),Expression( [Literal("HTML")])])])
            ),
        ( "doc/%-all.html: doc/%.texi $(SRC_PATH)/doc/t2h.init $(GENTEXI)", RuleExpression( [Expression( [Literal("doc/%-all.html")]),RuleOp(":"),PrerequisiteList( [Literal("doc/%.texi"),Literal(""),VarRef( [Literal("SRC_PATH")]),Literal("/doc/t2h.init"),Literal(""),VarRef( [Literal("GENTEXI")]),Literal("")])])  ),
        
        # static pattern rule
        # TODO

        # order only prereq
        # TODO
    )

    for test in rule_test_list : 
        # source, validate
        s,v = test[0],test[1]
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )
#        print( "     v={0}".format(str(v)) )

        assert tokens==v

        assert isinstance(tokens,RuleExpression)

        print( tokens.makefile() )
        print()


    # these should all fail
    fail_tests = ( 
        # some chars aren't valid in the rule name
        # TODO find more invalid characters
        ( "rule-with-; : ", () ),

    )

#    # Can we round trip? (the following is the output of the tokenizer) Does it build?
#    tokens=RuleExpression( [Expression( [Literal(""),VarRef( [Literal("hello "),VarRef( [Literal("there "),VarRef( [Literal("all "),VarRef( [Literal("you")]),Literal(" rabbits")]),Literal("")]),Literal("")]),Literal("")]),RuleOp(":"),PrerequisiteList( [Literal(""),VarRef( [Literal("hello")]),Literal(""),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits")])]) 
#
#    print(tokens.makefile())

if __name__=='__main__':
    rule_test()

