
# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")

from symbol import VarRef, Literal
from evaluate import evaluate

__all__ = [ "Info", 
            "MWarning",
            "Error",

            "make_function",
          ]

# built-in functions GNU Make 3.81(ish?)
builtins = {
    "subst",
    "patsubst",
    "strip",
    "findstring",
    "filter",
    "filter-out",
    "sort",
    "word",
    "words",
    "wordlist",
    "firstword",
    "lastword",
    "dir",
    "notdir",
    "suffix",
    "basename",
    "addsuffix",
    "addprefix",
    "join",
    "wildcard",
    "realpath",
    "absname",
    "error",
    "warning",
    "shell",
    "origin",
    "flavor",
    "foreach",
    "if",
    "or",
    "and",
    "call",
    "eval",
    "file",
    "value",
    "info",
}

class Function(VarRef):
    name = "(none)"

    def __init__(self, args):
        self.token_list = args

    def eval(self, symbol_table):
        return ""

class PrintingFunction(Function):
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        print(s, file=self.fh)
        return ""

class Info(PrintingFunction):
    string = "info"
    fh = sys.stdout

class MWarning(PrintingFunction):
    # name Warning is used by Python builtins so use MWarning instead
    string = "warning"
    fh = sys.stderr

class Error(PrintingFunction):
    string = "error"
    fh = sys.stderr

    def eval(self, symbol_table):
        super().eval(symbol_table)
        sys.exit(1)

def split_function_call(s):
    # break something like "info hello world" that needs a secondary parse
    # into a proper looking function call
    #
    # "info hello, world" -> "info", "hello, world"
    # "info" -> "info"
    # "info  hello, world" -> "info", " hello, world"
    # "info\thello, world" -> "info", "hello, world"

    logger.debug("split s=\"%s\" len=%d", s, len(s))
    state_init = 0
    state_searching = 1

    iswhite = lambda c : c==" " or c=="\t"

    state = state_init

    # Find first whitespace, split the string into string before and after
    # whitespace, throwing away the whitespace itself.
    for idx, c in enumerate(s):
        # most common state first
        if state==state_searching:
            # we have seen at least one non-white so now seeking a next
            # whitespace
            if iswhite(c):
                # don't return empty string, return None if there is nothing
                logger.debug("s=%s idx=%d", s, idx)
                return s[:idx], s[idx+1:] if idx+1<len(s) else None
        elif state==state_init:
            if iswhite(c):
                # no functions start with whitespace
                return s, None
            else:
                state = state_searching

    # no whitespace anywhere
    return s, None

_classes = {
    "info" : Info,
    "warning" : MWarning,
    "error" : Error,
}

def make_function(arglist):
    # do NOT .eval() here!!! will cause side effects. only want to look up the string
    s = arglist[0].string
    logger.debug("s=%s", s)
    # do NOT modify arglist; is a ref into the AST

    fname, rest = split_function_call(s)
    assert rest != ""  # catch a weird corner condition error

    # allow KeyError to propagate to indicate this is not a function
    fcls = _classes[fname]

    logger.debug("fname=%s rest=%s fcls=%s", fname, rest, fcls)
    
    if rest: return fcls([Literal(rest)] + arglist[1:])
    return fcls(arglist)

