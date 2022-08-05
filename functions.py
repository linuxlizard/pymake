
# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")

from symbol import VarRef, Literal
from evaluate import evaluate
from vline import VCharString, whitespace
from error import *
import shell

__all__ = [ "Info", 
            "WarningClass",
            "Error",
            "Shell", 

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

class Words(Function):
    name = "words"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        return str(len(s.split()))

class FirstWord(Function):
    name = "firstword"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        try:
            return s.split()[0]
        except IndexError:
            return ""

class IfClass(Function):
    name = "if"
    def eval(self, symbol_table):
        result = self.token_list[0].eval(symbol_table)
        if len(result):
            breakpoint()
            print(":::".join([str(t) for t in self.token_list]))
            return self.token_list[2].eval(symbol_table)
        else:
            return self.token_list[4].eval(symbol_table)

class LastWord(Function):
    name = "lastword"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        try:
            return s.split()[-1]
        except IndexError:
            return ""

class FunctionWithArguments(Function):
    def __init__(self, token_list):
        super().__init__(token_list)
        self.args = []
        self._parse_args()

    def _parse_args(self):
        """Parse the token list into an array of arguments separated by literal commas."""
        logger.debug("parse_args \"%s\"", self.name)

        arg_idx = 0
        self.args = [[] for n in range(self.num_args)]

        for t in self.token_list:
            print(t)

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
            str_iter = iter(t.string)
            for vchar in str_iter:
                # looking for commas separating the args
                if vchar.char != ',':
                    # consume leading whitespace
                    if arg_idx == 0 and vchar.char in whitespace:
                        pass
                    else:
                        lit.append(vchar)
                    continue

                logger.debug("found comma idx=%d", arg_idx)
                if lit:
                    # save whatever we've seen so far (if anything)
                    self.args[arg_idx].append(Literal(VCharString(lit)))
                    lit = []
                arg_idx += 1

                if arg_idx+1 == self.num_args:
                    # Done. Have everything we need.
                    # consume the rest of this string
                    self.args[arg_idx].append(Literal(VCharString(list(str_iter))))

                    # consume the rest of the token stream
                    self.args[arg_idx].extend(list(token_iter))

        for arg in self.args:
            for field in arg:
                print(field)

        if arg_idx+1 != self.num_args:
            # TODO better error
            errmsg = "found args=%d but needed=%d" % (arg_idx, self.num_args)
            logger.error(errmsg)
            raise ParseError(errmsg)


class Subst(FunctionWithArguments):
    name = "subst"
    num_args = 3

    def eval(self, symbol_table):
        # needs 3 args
        logger.debug("%s len=%d args=%s", self.name, len(self.args), self.args)

        from_s = "".join(t.eval(symbol_table) for t in self.args[0])
        to_s = "".join(t.eval(symbol_table) for t in self.args[1])
        text_s = "".join(t.eval(symbol_table) for t in self.args[2]) 

        logger.debug("%s from=\"%s\" to=\"%s\" text=\"%s\"", self.name, from_s, to_s, text_s)
        if not from_s:
            # empty "from" leaves text unchanged
            return text_s
        s = text_s.replace(from_s, to_s)
        logger.debug("%s \"%s\"", self.name, s)

        return s

class Word(FunctionWithArguments):
    name = "word"
    num_args = 2

    def eval(self, symbol_table):
        n_s = "".join(t.eval(symbol_table) for t in self.args[0])
        text_s = "".join(t.eval(symbol_table) for t in self.args[1])

        try:
            idx = int(n_s)
        except ValueError:
            raise ParseError

        if idx <= 0:
            errmsg = "first argument to '{.name}' must be greater than 0.".format(self)
            logger.error(errmsg)
            raise EvalError(description=errmsg)

        try:
            return text_s.split()[idx]
        except IndexError:
            return ""

class Shell(Function):
    name = "shell"

    def eval(self, symbol_table):
        s = "".join([t.eval(symbol_table) for t in self.token_list])
        logger.debug("%s s=\"%s\"", self.name, s)
        return shell.execute(s)

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
    "error" : Error,
    "firstword" : FirstWord,
    "if" : IfClass,
    "info" : Info,
    "lastword" : LastWord,
    "shell" : Shell,
    "subst" : Subst,
    "warning" : WarningClass,
    "word" : Word,
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

    if rest: return fcls([Literal(rest)] + arglist[1:])
    return fcls(arglist[1:])
