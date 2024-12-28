# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com

# davep 20-Mar-2016 ; built-in functions

import sys
import logging

logger = logging.getLogger("pymake.functions")
#logger.setLevel(level=logging.DEBUG)

from pymake.symbol import VarRef, Literal
from pymake.vline import VCharString, whitespace
from pymake.error import *
from pymake.functions_base import Function, FunctionWithArguments
from pymake.functions_fs import *
from pymake.functions_cond import *
from pymake.functions_str import *
from pymake.todo import TODOMixIn

import pymake.shell as shell

__all__ = [ "Info", 
            "WarningClass",
            "Error",
            "Shell", 

            "make_function",
          ]

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
    # I've discovered the $(shell) function behaves differently than recipe
    # execution. A recipe execution will default to /bin/sh if $(SHELL) is
    # empty. The $(shell) function will happily exec an empty string.
    #
    # Example:
    # SHELL:=
    # .SHELLFLAGS:=
    # $(shell /bin/ls)
    #
    def eval(self, symbol_table):
        return shell.execute_tokens(self.token_list, symbol_table)

class ValueClass(Function):
    name = "value"
    num_args = 1

    def eval(self, symbol_table):
        # single string that is a variable name
        var = "".join([a.eval(symbol_table) for a in self.token_list])

        return symbol_table.value(var)

class Breakpoint(Function):
    name = "breakpoint"
    num_args = -1

    def eval(self, symbol_table):
        breakpoint()
        return ""

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

    # functions not in official Make
    "breakpoint" : Breakpoint,
}

def maybe_function_call(vcstr):

    getchars = enumerate(vcstr)
    idx, vchar = next(getchars)
    if vchar.char in whitespace:
        # GNU Make doesn't treat anything with leading whitespace as a function
        # call, e.g., $( info blah blah ) is treated as a weird var ref
        return (vcstr,)

    for idx, vchar in getchars:
        c = vchar.char
        logger.debug("m c=%s idx=%d", c, idx)
        if c in whitespace:
            # done!
            return ( VCharString(vcstr[0:idx]), VCharString(vcstr[idx+1:]) )

    # we've fun out of string before seeing anything interesting so this is just a varref
    return (vcstr,)

def make_function(arglist):
    logger.debug("make_function arglist=%s", arglist)

    # $() is valid (empty varref)
    if not arglist:
        raise KeyError

    # .string will be a VCharString
    # do NOT modify arglist; is a ref into the makefile's AST

    # do NOT .eval() here!!! will cause side effects. only want to look up the string
    vcstr = arglist[0].string

    # if .string is None then we don't have a Literal in which case we're
    # definitely not a function.
    if vcstr is None:
        raise KeyError

    results = maybe_function_call(vcstr)
    if len(results) == 1:
        # simple string, not a function
        raise KeyError

    # we have a vanilla function call
    fname, rest = results
    logger.debug("make_function fname=\"%s\" rest=\"%s\"", fname, rest)
    # convert from array to python string for lookup
    str_fname = str(fname)

    # allow KeyError to propagate to indicate this is not a function
    fcls = _classes[str_fname]

    logger.debug("make_function fname=\"%s\" rest=\"%s\" fcls=%s", str_fname, rest, fcls)

    if rest: 
        fn = fcls([Literal(rest)] + arglist[1:])
    else:
        fn = fcls(arglist[1:])

    # XXX temp hack to save the function's vstring name so we can get_pos()
    # (I should be passing this into the constructor but that would mean
    # changing a lot of code right now)
    fn.string = fname
    return fn

