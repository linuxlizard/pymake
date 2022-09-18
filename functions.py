
# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")

from symbol import VarRef, Literal
from vline import VCharString, whitespace
from error import *
from functions_base import Function, FunctionWithArguments
from functions_fs import *
from functions_cond import *
from functions_str import *
from todo import TODOMixIn
from flatten import flatten

import shell

__all__ = [ "Info", 
            "WarningClass",
            "Error",
            "Shell", 

            "make_function",
          ]

# built-in functions GNU Make 3.81(ish?)
#builtins = {
#    "subst",
#    "patsubst",
#    "strip",
#    "findstring",
#    "filter",
#    "filter-out",
#    "sort",
#    "word",
#    "words",
#    "wordlist",
#    "firstword",
#    "lastword",
#    "dir",
#    "notdir",
#    "suffix",
#    "basename",
#    "addsuffix",
#    "addprefix",
#    "join",
#    "wildcard",
#    "realpath",
#    "absname",
#    "error",
#    "warning",
#    "shell",
#    "origin",
#    "flavor",
#    "foreach",
#    "if",
#    "or",
#    "and",
#    "call",
#    "eval",
#    "file",
#    "value",
#    "info",
#}

class PrintingFunction(Function):
    fmt = None

    # gnu make has some very particular behaviors around spacing in printing output.
    def eval(self, symbol_table):
        msg = ""
        for t in self.token_list:
            isfn = isinstance(t, Function)
#            print(f"t={t} isfn={isfn}")
            if isfn:
                if t.preserve_ws:
                    msg += "".join(t.eval(symbol_table))
                else:
                    msg += " ".join(t.eval(symbol_table))
            else:
                s = "".join(t.eval(symbol_table))
#                s = " ".join(t.eval(symbol_table))
                msg += s
#            print(f"msg=**{msg}**")

        # GNU Make discards whitespace between fn call and 1st arg
        # e.g., $(info   5)  ->  "5"  (not "   5")
        # Trailing whitespace is preserved.
        msg = msg.lstrip()

        if self.fmt:
            t = self.token_list[0]
            print(self.fmt.format(t.string[0].filename, t.string[0].linenumber, msg), file=self.fh)
        else:
            print("%s" % msg, file=self.fh)

        return [""]


class Info(PrintingFunction):
    name = "info"
    fh = sys.stdout

class WarningClass(PrintingFunction):
    # name Warning is used by Python builtins so use WarningClass instead
    name = "warning"
    fh = sys.stderr
    fmt = "{}:{}: {}"


class Error(PrintingFunction):
    name = "error"
    fh = sys.stderr
    fmt = "{}:{}: *** {}. Stop."

    def eval(self, symbol_table):
        super().eval(symbol_table)
        # buh-bye
        sys.exit(1)


class Call(TODOMixIn, Function):
    name = "call"

class Eval(TODOMixIn, Function):
    name = "eval"

class Flavor(TODOMixIn, Function):
    name = "flavor"

class Foreach(TODOMixIn, Function):
    name = "foreach"

class Origin(TODOMixIn, Function):
    name = "origin"

class Shell(Function):
    name = "shell"

    def eval(self, symbol_table):
        # TODO condense these steps
        step1 = [t.eval(symbol_table) for t in self.token_list]
        step2 = flatten(step1)
        step3 = "".join(step2)
        step4 = shell.execute(step3)
        # everything returns an iterable of strings
        return step4.split()

class ValueClass(TODOMixIn, Function):
    name = "value"
    num_args = 1

    # 20220820 ; start implementing this, ran into some pretty big problems, so
    # leaving it for now. (put TODO back)

    def eval(self, symbol_table):
#        assert len(self.args)==1, len(self.args)
        result = evaluate(self.token_list, symbol_table)
        sym = symbol_table.fetch(result)
        breakpoint()
        return sym.eval(symbol_table)

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
    for idx, vchar in enumerate(s):
        c = vchar.char
        logger.debug("c=%s state=%d idx=%d", c, state, idx)
        # most common state first
        if state==state_searching:
            # we have seen at least one non-white so now seeking a next
            # whitespace
            if iswhite(c):
                # don't return empty string, return None if there is nothing
                logger.debug("s=\"%s\" idx=%d", s, idx)
                return VCharString(s[:idx]), VCharString(s[idx+1:]) if idx+1<len(s) else None
        elif state==state_init:
            if iswhite(c):
                # no functions start with whitespace
                return s, None
            else:
                state = state_searching

    # no whitespace anywhere
    return s, None

_classes = {
    # please keep in alphabetical order
    "abspath" : AbsPath,
    "addprefix" : AddPrefix,
    "addsuffix" : AddSuffix,
    "and" : AndClass,
    "call" : Call,
    "dir" : DirClass,
    "error" : Error,
    "eval" : Eval,
    "file" : FileClass,
    "filter" : FilterClass,
    "filter-out" : FilterOutClass,
    "findstring" : FindString,
    "firstword" : FirstWord,
    "flavor" : Flavor,
    "foreach" : Foreach,
    "if" : IfClass,
    "info" : Info,
    "join" : JoinClass,
    "lastword" : LastWord,
    "notdir" : NotDirClass,
    "or" : OrClass,
    "origin" : Origin,
    "patsubst" : Patsubst,
    "realpath" : RealPath,
    "shell" : Shell,
    "sort" : SortClass,
    "strip" : StripClass,
    "subst" : Subst,
    "suffix" : Suffix,
    "value" : ValueClass,
    "warning" : WarningClass,
    "wildcard" : Wildcard,
    "word" : Word,
    "wordlist" : WordList,
    "words" : Words,
}

def make_function(arglist):
    logger.debug("make_function arglist=%s", arglist)

    # $() is valid (empty varref)
    if not arglist:
        raise KeyError("")

#    for a  in arglist:
#        print(a)

    # do NOT .eval() here!!! will cause side effects. only want to look up the string
    vcstr = arglist[0].string
    # .string will be a VCharString
    # do NOT modify arglist; is a ref into the AST

    fname, rest = split_function_call(vcstr)

    logger.debug("make_function fname=\"%s\" rest=\"%s\"", fname, rest)

    # convert from array to python string for lookup
    fname = str(fname)

    # allow KeyError to propagate to indicate this is not a function
    fcls = _classes[fname]

    logger.debug("make_function fname=\"%s\" rest=\"%s\" fcls=%s", fname, rest, fcls)

    if rest: 
        return fcls([Literal(rest)] + arglist[1:])

    return fcls(arglist[1:])
