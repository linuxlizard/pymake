# functions for string substitution and analysis

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn

__all__ = [ "FilterClass", "FilterOutClass", "FindString", "FirstWord", 
    "LastWord", "Patsubst", "SortClass", "StripClass", "Subst", 
    "Word", "WordList", "Words" ]

class FilterClass(TODOMixIn, Function):
    name = "filter"

class FilterOutClass(TODOMixIn, Function):
    name = "filter-out"

class FindString(TODOMixIn, Function):
    name = "findstring"

class FirstWord(Function):
    name = "firstword"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        try:
            return s.split()[0]
        except IndexError:
            return ""

class LastWord(Function):
    name = "lastword"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        try:
            return s.split()[-1]
        except IndexError:
            return ""

class Patsubst(TODOMixIn, Function):
    name = "patsubst"

class SortClass(Function):
    name = "sort"

    # Sort does not take arguments function-style (commas are not interpreted
    # as separate arguments. Rather the entire single arg is interpretted as a
    # space separated list.
    def eval( self, symbol_table):
        print(self.token_list)
        # evalutate all the things
        step1 = "".join([t.eval(symbol_table) for t in self.token_list])
        print(f"step1={step1}")
        # split on whitespace, discarding extra whitespace
        step2 = [s for s in step1.split() if len(s.strip())]
        s = " ".join(sorted(step2))
        return s
        

class StripClass(TODOMixIn, Function):
    name = "strip"

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

class WordList(TODOMixIn, Function):
    name = "wordlist"

class Words(Function):
    name = "words"
    def eval(self, symbol_table):
        s = evaluate(self.token_list, symbol_table)
        return str(len(s.split()))


