
# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")

from evaluate import evaluate

__all__ = [ "Info", 
            "Warning",
            "Error",
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
}

class Function:
    name = "(none)"

    def __init__(self, args):
        self.args = args

    def eval(self, symbol_table):
        return ""

class PrintingFunction(Function):
    def eval(self, symbol_table):
        s = evaluate(self.args, symbol_table)
        print(s, file=self.fh)
        return ""

class Info(PrintingFunction):
    name = "info"
    fh = sys.stdout

class Warning(PrintingFunction):
    name = "warning"
    fh = sys.stderr

class Error(PrintingFunction):
    name = "error"
    fh = sys.stderr

    def eval(self, symbol_table):
        super().eval(symbol_table)
        sys.exit(1)

print(locals())

