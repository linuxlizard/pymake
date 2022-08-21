# functions for the filesystem

import glob

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn

__all__ = [ "AbsPath", 
            "AddPrefix",
            "AddSuffix",
            "DirClass", 
            "FileClass",
            "JoinClass",
            "NotDirClass",
            "RealPath",
            "Suffix",
            "Wildcard",
        ]

class AbsPath(TODOMixIn, Function):
    name = "abspath"

class AddPrefix(TODOMixIn, FunctionWithArguments):
    name = "addprefix"

class AddSuffix(TODOMixIn, FunctionWithArguments):
    name = "addsuffix"

class DirClass(TODOMixIn, FunctionWithArguments):
    name = "dir"

class FileClass(TODOMixIn, FunctionWithArguments):
    name = "file"

class JoinClass(TODOMixIn, Function):
    name = "join"

class NotDirClass(TODOMixIn, FunctionWithArguments):
    name = "notdir"

class RealPath(TODOMixIn, FunctionWithArguments):
    name = "realpath"

class Suffix(TODOMixIn, FunctionWithArguments):
    name = "suffix"

class Wildcard(FunctionWithArguments):
    name = "wildcard"
    num_args = 1  

    # "The argument pattern is a file name pattern, typically containing
    # wildcard characters (as in shell file name patterns). The result of
    # wildcard is a space-separated list of the names of existing files that
    # match the pattern." - gnu_make.pdf

    # nothing is mentioned in the manual about the sort order so there's no
    # guarantee my glob will match GNU make's
    def eval(self, symbol_table):
        result = ""
        for arg in self.args:
            pattern = "".join([a.eval(symbol_table) for a in arg])
            files = glob.glob(pattern)
            result += " ".join(files)
        return result

