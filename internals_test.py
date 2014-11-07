#!/usr/bin/env python3

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from pymake import *

@depth_checker
def recurse_test(foo,bar,baz):
    recurse_test(foo+1,bar+1,baz+1)

def run():
    assert isinstance(VarRef([]),Symbol)

    # $($(qq))
    v = VarRef( [VarRef([Literal("qq")]),] )
    print("v={0}".format(str(v)))

    # 
    # Verify my recursion circuit breaker.
    # (Much more shallow than Python's built-in recursion depth checker.)
    #
    try : 
        recurse_test(10,20,30)
    except NestedTooDeep:
        depth_reset()
    else:
        assert 0
    assert depth==0

    # 
    # Verify == operator
    # The equality operator mostly used in regression tests.
    # 
    lit1 = Literal("all")
    lit2 = Literal("all")
    assert lit1==lit2

    lit1 = Literal("all")
    lit2 = Literal("foo")
    assert lit1!=lit2

    for s in rule_operators : 
        op1 = RuleOp(s)
        op2 = RuleOp(s)
        assert op1==op2

    for s in assignment_operators : 
        op1 = AssignOp(s)
        op2 = AssignOp(s)
        assert op1==op2

    exp1 = RuleExpression( ( Expression( (Literal("all"),) ),
                             RuleOp(":"),
                             PrerequisiteList( () ) )
                        ) 
    exp2 = RuleExpression( (  Expression( (Literal("all"),) ),
                             RuleOp(":"),
                             PrerequisiteList( () ) )
                        ) 
    assert exp1==exp2

    exp2 = RuleExpression( (  Expression( (Literal("all"),) ),
                             RuleOp("::"),
                             PrerequisiteList( () ) )
                        ) 
    assert exp1!=exp2

if __name__=='__main__':
    run()

