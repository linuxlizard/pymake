# functions for the filesystem

import glob
import os.path

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn
from flatten import flatten

__all__ = [ "AbsPath", 
            "AddPrefix",
            "AddSuffix",
            "BasenameClass",
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

class AbsPath(Function):
    name = "abspath"

    def eval(self, symbol_table):
        # list of strings
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        return " ".join([os.path.abspath(fname) for fname in filename_list])

class AddPrefix(TODOMixIn, FunctionWithArguments):
    name = "addprefix"

class AddSuffix(TODOMixIn, FunctionWithArguments):
    name = "addsuffix"

class BasenameClass(Function):
    name = "basename"

    # "Extracts all but the suffix of each file name in names. If the file name contains
    # a period, the basename is everything starting up to (and not including) the last
    # period. Periods in the directory part are ignored. If there is no period, the
    # basename is the entire file name."
    #
    def eval(self, symbol_table):
        # list of strings
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def basename(fname):
            pass

        return " ".join([basename(fname) for fname in filename_list])

class DirClass(Function):
    name = "dir"

    # "Extracts the directory-part of each file name in names. The
    # directory-part of the file name is everything up through (and including)
    # the last slash in it. If the file name contains no slash, the directory
    # part is the string ‘./’"  GNU Make manual

    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def dirname(fname):
            # fiddle with the string to match the quirks in gnu make

            # no path components treated as current directory
            # e.g. $(dir foo.txt) -> "./"
            if not os.path.sep in fname:
                return "." + os.path.sep

            # Can't use os.path.dirname() because it's too clean.
            # GNU make $(dir //////tmp//////foo.txt) -> "//////tmp//////"
            # python dirname -> "//////tmp/"

            pos = fname.rindex(os.path.sep)
            return fname[:pos+1]

        return " ".join([ dirname(fname) for fname in filename_list])

class FileClass(TODOMixIn, FunctionWithArguments):
    name = "file"

class JoinClass(TODOMixIn, Function):
    name = "join"

class NotDirClass(Function):
    name = "notdir"

    # "Extracts all but the directory-part of each file name in names. If the file name
    # contains no slash, it is left unchanged. Otherwise, everything through the last
    # slash is removed from it.
    #
    # "A file name that ends with a slash becomes an empty string. This is unfortunate,
    # because it means that the result does not always have the same number of
    # whitespace-separated file names as the argument had; but we do not see any
    # other valid alternative."  -- GNU Make manual

    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def notdir(fname):
            # no path components treated as current directory
            # e.g. $(dir foo.txt) -> "./"
            if not os.path.sep in fname:
                return fname

            pos = fname.rindex(os.path.sep)
            return fname[pos+1:]

        return " ".join([ notdir(fname) for fname in filename_list])

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
        
class Suffix(Function):
    name = "suffix"

    # "Extracts the suffix of each file name in names. If the file name contains a period,
    # the suffix is everything starting with the last period. Otherwise, the suffix is
    # the empty string. This frequently means that the result will be empty when
    # names is not, and if names contains multiple file names, the result may contain
    # fewer file names."
    #
    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def suffix(fname):
            try:
                return fname[fname.rindex('.'):]
            except ValueError:
                return ""

        return " ".join([ suffix(fname) for fname in filename_list])

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

        # evaluate all the things; will have an array of strings
        step1 = [t.eval(symbol_table) for t in self.token_list]
#        print(f"wild step1={step1}")

#        step2 = flatten(step1)
#        print(f"wild step2={step2}")

        step3 = "".join(step1).split()
#        print(f"wild step3={step3}")

        # split on any literal whitespace, discarding extra whitespace, empty fields
#        step4 = [s for s in step3.split() if len(s.strip())]
#        print(f"wild step4={step4}")

        # array of arrays of strings (glob.glob() returns array of strings)
        step5 = [glob.glob(pattern) for pattern in step3]
#        print(f"wild step5={step5}")

        return " ".join(flatten(step5))
#        files = flatten(step5)
#        print("wildcard eval files=",files)
#        return files

