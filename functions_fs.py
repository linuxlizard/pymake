# functions for the filesystem

import glob
import os.path
import itertools

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn
from flatten import flatten

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

# "The argument of the function is regarded as a series of file names, separated
# by whitespace.  (Leading and trailing whitespace is ignored.) Each file name
# in the series is transformed in the same way and the results are concatenated
# with single spaces between them."  -- GNU Make manual

class AbsPath(TODOMixIn, Function):
    name = "abspath"

class AddPrefix(TODOMixIn, FunctionWithArguments):
    name = "addprefix"

class AddSuffix(TODOMixIn, FunctionWithArguments):
    name = "addsuffix"

class DirClass(Function):
    name = "dir"

    # "Extracts the directory-part of each file name in names. The
    # directory-part of the file name is everything up through (and including)
    # the last slash in it. If the file name contains no slash, the directory
    # part is the string ‘./’"  GNU Make manual

    def eval(self, symbol_table):
        breakpoint()
        return "foo"

class FileClass(TODOMixIn, FunctionWithArguments):
    name = "file"

class JoinClass(TODOMixIn, Function):
    name = "join"

class NotDirClass(TODOMixIn, FunctionWithArguments):
    name = "notdir"

class RealPath(Function):
    name = "realpath"

    # "For each file name in names return the canonical absolute name. A
    # canonical name does not contain any . or .. components, nor any repeated
    # path separators (/) or symlinks. In case of a failure the empty string
    # is returned. Consult the realpath(3) documentation for a list of possible
    # failure causes."  -- GNU Make manual
    def eval(self, symbol_table):
        print(self.token_list)
        return "foo"
        
class Suffix(TODOMixIn, FunctionWithArguments):
    name = "suffix"

class Wildcard(Function):
    name = "wildcard"

    # "The argument pattern is a file name pattern, typically containing
    # wildcard characters (as in shell file name patterns). The result of
    # wildcard is a space-separated list of the names of existing files that
    # match the pattern." - gnu_make.pdf

    # nothing is mentioned in the manual about the sort order so there's no
    # guarantee my glob will match GNU make's

    def eval(self, symbol_table):
        # TODO obviously need to condense this a bit

        # evalutate all the things
        step1 = [t.eval(symbol_table) for t in self.token_list]
#        print(f"wild step1={step1}")

        step2 = flatten(step1)
#        print(f"wild step2={step2}")

        step3 = "".join(step2)
#        print(f"wild step3={step3}")

        # split on any literal whitespace, discarding extra whitespace, empty fields
        step4 = [s for s in step3.split() if len(s.strip())]
#        print(f"wild step4={step4}")

        step5 = [glob.glob(pattern) for pattern in step4]
#        print(f"wild step5={step5}")

        files = flatten(step5)
#        print("wildcard eval files=",files)
        return files

