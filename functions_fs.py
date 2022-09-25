# SPDX-License-Identifier: GPL-2.0
# functions for the filesystem

# TODO lots of copy/paste code in here. Ugly.

import sys
import glob
import os.path
import itertools

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
# with single spaces between them." -- GNU Make manual  Version 4.3 Jan 2020 

class AbsPath(Function):
    name = "abspath"

    def eval(self, symbol_table):
        # list of strings
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        return " ".join([os.path.abspath(fname) for fname in filename_list])

class AddPrefix(FunctionWithArguments):
    name = "addprefix"
    num_args = 2

    def eval(self, symbol_table):
        prefix = "".join([a.eval(symbol_table) for a in self.args[0]])
        str_list = [a.eval(symbol_table) for a in self.args[1]]
        filename_list = "".join(str_list).split()

        return " ".join([prefix+fname for fname in filename_list])

class AddSuffix(FunctionWithArguments):
    name = "addsuffix"
    num_args = 2

    def eval(self, symbol_table):
        suffix = "".join([a.eval(symbol_table) for a in self.args[0]])
        str_list = [a.eval(symbol_table) for a in self.args[1]]
        filename_list = "".join(str_list).split()

        return " ".join([fname+suffix for fname in filename_list])


class BasenameClass(Function):
    name = "basename"

    # "Extracts all but the suffix of each file name in names. If the file name contains
    # a period, the basename is everything starting up to (and not including) the last
    # period. Periods in the directory part are ignored. If there is no period, the
    # basename is the entire file name." -- GNU Make manual  Version 4.3 Jan 2020 
    #
    def eval(self, symbol_table):
        # list of strings
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def basename(fname):
            # handle case where there is a . before a /
            # e.g., foo.c/bar
            try:
                slash_idx = fname.rindex('/')
            except ValueError:
                slash_idx = -1

            try:
                dot_idx = fname.rindex('.')
            except ValueError:
                return fname

            if slash_idx > dot_idx: return fname
            return fname[:dot_idx]

        return " ".join([basename(fname) for fname in filename_list])

class DirClass(Function):
    name = "dir"

    # "Extracts the directory-part of each file name in names. The
    # directory-part of the file name is everything up through (and including)
    # the last slash in it. If the file name contains no slash, the directory
    # part is the string ‘./’" -- GNU Make manual  Version 4.3 Jan 2020 

    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def dirname(fname):
            # fiddle with the string to match the quirks in gnu make

            # Can't use os.path.dirname() because it's too clean.
            # GNU make $(dir //////tmp//////foo.txt) -> "//////tmp//////"
            # python dirname -> "//////tmp/"

            try:
                return fname[:fname.rindex(os.path.sep)+1]
            except ValueError:
                # no path components treated as current directory
                # e.g. $(dir foo.txt) -> "./"
                return "." + os.path.sep

        return " ".join([ dirname(fname) for fname in filename_list])

class FileClass(TODOMixIn, FunctionWithArguments):
    name = "file"

class JoinClass(FunctionWithArguments):
    name = "join"
    num_args = 2

    # $(join list1,list2)
    #
    # "Concatenates the two arguments word by word: the two first words (one from
    # each argument) concatenated form the first word of the result, the two second
    # words form the second word of the result, and so on. So the nth word of the
    # result comes from the nth word of each argument. If one argument has more
    # words that the other, the extra words are copied unchanged into the result.
    #
    # "For example, ‘$(join a b,.c .o)’ produces ‘a.c b.o’.
    #
    # "Whitespace between the words in the lists is not preserved; it is replaced with
    # a single space"   -- GNU Make manual  Version 4.3 Jan 2020
    #
    def eval(self, symbol_table):

        # array of strings
        list1 = "".join([a.eval(symbol_table) for a in self.args[0]]).split()
        list2 = "".join([a.eval(symbol_table) for a in self.args[1]]).split()

        # to use zip() need each list to be identical size because zip() will
        # stop at shortest list otherwise; gnu make continues 
        # e.g. 
        # $(join a b c d e f g, .c .o) -> a.c b.o d e f g 
        # $(join a b,.c .o .cc .pas .f .rs .ada) -> a.c b.o .cc .pas .f .rs .ada
        #
        return " ".join( [a+b for a,b in itertools.zip_longest(list1,list2, fillvalue='')] )


class NotDirClass(Function):
    name = "notdir"

    # "Extracts all but the directory-part of each file name in names. If the file name
    # contains no slash, it is left unchanged. Otherwise, everything through the last
    # slash is removed from it.
    #
    # "A file name that ends with a slash becomes an empty string. This is unfortunate,
    # because it means that the result does not always have the same number of
    # whitespace-separated file names as the argument had; but we do not see any
    # other valid alternative."  -- GNU Make manual  Version 4.3 Jan 2020

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
    # failure causes."  -- GNU Make manual  Version 4.3 Jan 2020
    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def realpath(fname):
            # if the file doesn't exist, return empty string
            ver = sys.version_info
            if ver.major==3 and ver.minor >= 10:
                # strict argument added in python 3.10
                try:
                    s = os.path.realpath(fname, strict=True)
                except OSError:
                    return ""

            s = os.path.realpath(fname)
            if not os.path.exists(s):
                return ""
            return s

        return " ".join([realpath(fname) for fname in filename_list])
        
class Suffix(Function):
    name = "suffix"

    # "Extracts the suffix of each file name in names. If the file name contains a period,
    # the suffix is everything starting with the last period. Otherwise, the suffix is
    # the empty string. This frequently means that the result will be empty when
    # names is not, and if names contains multiple file names, the result may contain
    # fewer file names." -- GNU Make manual  Version 4.3 Jan 2020
    #
    def eval(self, symbol_table):
        str_list = [t.eval(symbol_table) for t in self.token_list]
        filename_list = "".join(str_list).split()

        def suffix(fname):
            # handle case where there is a . before a /
            # e.g., foo.c/bar
            try:
                slash_idx = fname.rindex('/')
            except ValueError:
                slash_idx = -1

            try:
                dot_idx = fname.rindex('.')
            except ValueError:
                return ""

            if slash_idx > dot_idx: return ""
            return fname[dot_idx:]

        # extra hoops to throw away empty strings
        new_names = filter( lambda s : bool(s), [suffix(fname) for fname in filename_list] )
        return " ".join(new_names)

class Wildcard(Function):
    name = "wildcard"

    # "The argument pattern is a file name pattern, typically containing
    # wildcard characters (as in shell file name patterns). The result of
    # wildcard is a space-separated list of the names of existing files that
    # match the pattern." -- GNU Make manual  Version 4.3 Jan 2020

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

