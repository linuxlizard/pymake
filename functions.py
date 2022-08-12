
# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")

from symbol import VarRef, Literal
from evaluate import evaluate
from vline import VCharString, whitespace
from error import *
from functions_base import Function, FunctionWithArguments
from functions_fs import *
from functions_cond import *
from functions_str import *
from todo import TODOMixIn

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

class old_Function(VarRef):
    def __init__(self, args):
        logger.debug("function=%s args=%s", self.name, args)
        super().__init__(args)

    def makefile(self):
        s = "$(" + self.name + " "
        for t in self.token_list : 
            s += t.makefile()
        s += ")"
        return s

    def eval(self, symbol_table):
        return ""

class PrintingFunction(Function):
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        logger.debug("%s \"%s\"", self.name, s)
        print(s, file=self.fh)
        return ""

class Info(PrintingFunction):
    name = "info"
    fh = sys.stdout

class WarningClass(PrintingFunction):
    # name Warning is used by Python builtins so use WarningClass instead
    name = "warning"
    fh = sys.stderr

    def eval(self, symbol_table):
        logger.debug("self=%s", self)
        t = self.token_list[0]
        s = evaluate(self.token_list, symbol_table)
        print("{}:{}: {}".format(t.string[0].filename, t.string[0].linenumber, s), file=self.fh)
        return ""

class Error(PrintingFunction):
    name = "error"
    fh = sys.stderr

    def eval(self, symbol_table):
        logger.debug("self=%s", self)

        t = self.token_list[0]

        s = evaluate(self.token_list, symbol_table)
        print("{}:{}: *** {}. Stop.".format(t.string[0].filename, t.string[0].linenumber, s), file=self.fh)
        sys.exit(1)

class old_FunctionWithArguments(Function):
    def __init__(self, token_list):
        super().__init__(token_list)
        self.args = []
        self._parse_args()

    def _parse_args(self):
        """Parse the token list into an array of arguments separated by literal commas."""
        logger.debug("parse_args \"%s\"", self.name)

        arg_idx = 0
        self.args = [[] for n in range(self.num_args)]

#        for t in self.token_list:
#            print(t)

        # Walk along the token list looking for Literals which should contain
        # the commas.  Inside the literal(s), look for our comma(s).
        # Split the Literal into new Literals around the commas.
        # Preserve everything else as-is.
        token_iter = iter(self.token_list)
        for t in token_iter:
            if not isinstance(t, Literal):
                # no touchy
                self.args[arg_idx].append(t)
                continue

            # peek inside the literal for commas 
            lit = []
            vstr_iter = iter(t.string)
            for vchar in vstr_iter:
                # looking for commas separating the args
                if vchar.char != ',':
                    # consume leading whitespace
                    if arg_idx == 0 and vchar.char in whitespace:
                        pass
                    else:
                        lit.append(vchar)
                    continue

                logger.debug("found comma idx=%d pos=%r", arg_idx, vchar.pos)
                if lit:
                    # save whatever we've seen so far (if anything)
                    self.args[arg_idx].append(Literal(VCharString(lit)))
                    lit = []
                arg_idx += 1

                if arg_idx+1 == self.num_args:
                    # Done. Have everything we need.
                    # consume the rest of this string
                    # (this will break from the inner loop)
                    remaining = list(vstr_iter)
                    if remaining:
                        self.args[arg_idx].append(Literal(VCharString(remaining)))

                    # consume the rest of the token stream
                    # (this will break from the outer loop)
                    self.args[arg_idx].extend(list(token_iter))

#        for arg in self.args:
#            for field in arg:
#                print(field)

        if arg_idx+1 != self.num_args:
            # TODO better error
            errmsg = "found args=%d but needed=%d" % (arg_idx, self.num_args)
            logger.error(errmsg)
            raise ParseError(errmsg)

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
        s = "".join([t.eval(symbol_table) for t in self.token_list])
        logger.debug("%s s=\"%s\"", self.name, s)
        return shell.execute(s)

class ValueClass(TODOMixIn, Function):
    name = "value"

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
