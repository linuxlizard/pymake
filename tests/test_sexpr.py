import sys

import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from symbol import *
from functions_str import *
from symtable import SymbolTable

# test some S Expression execution
#
symtable = SymbolTable()
symtable.add("target", ["abcdefghijklmnopqrstuvwxyz"])

a = AssignmentExpression([Expression([Literal("UPPERCASE")]), AssignOp("="), Expression([Subst([Literal("z,Z,"), Subst([Literal("y,Y,"), Subst([Literal("x,X,"), Subst([Literal("w,W,"), Subst([Literal("v,V,"), Subst([Literal("u,U,"), Subst([Literal("t,T,"), Subst([Literal("s,S,"), Subst([Literal("r,R,"), Subst([Literal("q,Q,"), Subst([Literal("p,P,"), Subst([Literal("o,O,"), Subst([Literal("n,N,"), Subst([Literal("m,M,"), Subst([Literal("l,L,"), Subst([Literal("k,K,"), Subst([Literal("j,J,"), Subst([Literal("i,I,"), Subst([Literal("h,H,"), Subst([Literal("g,G,"), Subst([Literal("f,F,"), Subst([Literal("e,E,"), Subst([Literal("d,D,"), Subst([Literal("c,C,"), Subst([Literal("b,B,"), Subst([Literal("a,A,"), VarRef([Literal("target")])])])])])])])])])])])])])])])])])])])])])])])])])])])])])

print(a)
a.eval(symtable)
print(a.makefile())

result = symtable.fetch(['target'])
print(f"result={result}")
assert result[0]=='abcdefghijklmnopqrstuvwxyz'

