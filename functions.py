# SPDX-License-Identifier: GPL-2.0

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
    # Need to carefully duplicate all those behaviors.

    def __init__(self, token_list):
        # GNU Make discards whitespace between fn call and 1st arg
        # e.g., $(info   5)  ->  "5"  (not "   5")
        # Trailing whitespace is preserved.

        # To hide any leading spaces between the function name and the
        # first argument, if the first token is a literal, mark any leading
        # whitespace as hidden.  
        # $(info   a  b   )  will print "a b   "
        #        ^^-- marked as hidden
        #
        # The arguments to the printing function could result in leading spaces
        # so can't just lstrip() the result (which was my first idea)

        super().__init__(token_list)

        if not self.token_list:
            # empty list so quit now
            return

        first_token = self.token_list[0]
        if not isinstance(first_token, Literal):
            # no literal whitespace so quit now
            return

        for vchar in first_token.string:
            if not vchar.char in whitespace:
                break
            vchar.hide = True

    def _makestr(self, symbol_table):
        # If the called Symbol contains whitespace between symbols, don't add more.
        # Otherwise, add whitespace.
        msg = ""

        # results will be an array of python strings
        results = [t.eval(symbol_table) for t in self.token_list]

#        breakpoint()

        # a nice place for a sanity test
        for r in results:
            assert isinstance(r,str), (type(r), results)

        for str_list in results:
            msg += "".join(str_list)

        return msg

    def eval(self, symbol_table):
        msg = self._makestr(symbol_table)

        if self.fmt:
            t = self.token_list[0]
            filename, linenumber = t.get_pos()
            print(self.fmt.format(filename, linenumber, msg), file=self.fh)
        else:
            print("%s" % msg, file=self.fh)

        return ""


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


class Call(FunctionWithArguments):
    name = "call"
    num_args = -1 # no max

    # $(call variable,param,param,...)
    def eval(self, symbol_table):
        var = "".join([a.eval(symbol_table) for a in self.args[0]])

        arg_stack = []
        for idx, arg_list in enumerate(self.args[1:]):
            arg = "".join([a.eval(symbol_table) for a in arg_list])
            varname = "%d" % (idx+1)
            symbol_table.push(varname)
            symbol_table.add(varname, arg)
            # save the arg name so we can pop it from the symbol table 
            arg_stack.append(varname)


        # all we need to do is fetch() from the symbol table and the expression
        # will be eval'd
        s = symbol_table.fetch(var)
#        breakpoint()

        # pop the args off the symbol table in reverse order because why not
        while 1:
            try:
                symbol_table.pop(arg_stack.pop())
            except IndexError:
                break

        return s


class Eval(TODOMixIn, Function):
    name = "eval"

class Flavor(Function):
    name = "flavor"

    def eval(self, symbol_table):
        # single string that is a variable name
        var = "".join([a.eval(symbol_table) for a in self.token_list])

        return symbol_table.flavor(var)

class Foreach(FunctionWithArguments):
    name = "foreach"
    num_args = 3

    # $(foreach var,list,text)
    def eval(self, symbol_table):
        # single string that is a variable name
        var = "".join([a.eval(symbol_table) for a in self.args[0]])

        # array of strings
        list_  = "".join([a.eval(symbol_table) for a in self.args[1]]).split()

#        breakpoint()

        out_str_list = []
        symbol_table.push(var)
        for item in list_:
            symbol_table.add(var, item, self.args[0][0].get_pos())
            text = "".join([a.eval(symbol_table) for a in self.args[2]])
            out_str_list.append(text)

        symbol_table.pop(var)

        return " ".join(out_str_list)


class Origin(Function):
    name = "origin"

    # $(origin variable)
    def eval(self, symbol_table):
        # single string that is a variable name
        var = "".join([a.eval(symbol_table) for a in self.token_list])

        return symbol_table.origin(var)

class Shell(Function):
    name = "shell"

    # "The shell function performs the same function that backquotes (‘‘’) perform in most
    # shells: it does command expansion. This means that it takes as an argument a shell
    # command and evaluates to the output of the command. The only processing make does on
    # the result is to convert each newline (or carriage-return / newline pair) to a single space. If
    # there is a trailing (carriage-return and) newline it will simply be removed."
    #
    # "After the shell function or ‘!=’ assignment operator is used, its exit status is placed in
    # the .SHELLSTATUS variable."
    #
    def eval(self, symbol_table):
        return shell.execute_tokens(self.token_list, symbol_table)

        # TODO condense these steps
        step1 = [t.eval(symbol_table) for t in self.token_list]
#        step2 = flatten(step1)
        step3 = "".join(step1)
        exe_result = shell.execute(step3, symbol_table)
        if exe_result.exitcode == 0:
            return exe_result.stdout

#        breakpoint()
        # "convert each newline ... to a single space
        # TODO multiple blank lines become a single space?
        # everything returns a string
        return step4.replace("\n", " ")

class ValueClass(Function):
    name = "value"
    num_args = 1

    def eval(self, symbol_table):
        # single string that is a variable name
        var = "".join([a.eval(symbol_table) for a in self.token_list])

        return symbol_table.value(var)

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
            if c in whitespace:
                # don't return empty string, return None if there is nothing
                logger.debug("s=\"%s\" idx=%d", s, idx)
                return VCharString(s[:idx]), VCharString(s[idx+1:]) if idx+1<len(s) else None
        elif state==state_init:
            if c in whitespace:
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
    "basename" : BasenameClass,
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
        raise KeyError

#    for a  in arglist:
#        print(a)

    # do NOT .eval() here!!! will cause side effects. only want to look up the string
    vcstr = arglist[0].string

    # if .string is None then we don't have a Literal in which case we're
    # definitely not a function.
    if vcstr is None:
        raise KeyError

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
