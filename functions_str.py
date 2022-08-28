# functions for string substitution and analysis

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn
from flatten import flatten

__all__ = [ "FilterClass", "FilterOutClass", "FindString", "FirstWord", 
    "LastWord", "Patsubst", "SortClass", "StripClass", "Subst", 
    "Word", "WordList", "Words" ]

class StringFnEval():
    def evaluate(self, symbol_table):
#        print(self.name, "token_list=", self.token_list)

        # evalutate all the things
        step1 = [t.eval(symbol_table) for t in self.token_list]
#        print(f"{self.name} step1={step1}")

        # returns an iterable across a 1-D array
        step2 = flatten(step1)

        return step2

class FilterClass(TODOMixIn, Function):
    name = "filter"

class FilterOutClass(TODOMixIn, Function):
    name = "filter-out"

class FindString(TODOMixIn, Function):
    name = "findstring"

class FirstWord(Function, StringFnEval):
    name = "firstword"
    def eval(self, symbol_table):
        s = self.evaluate(symbol_table)
        try:
            # s should be an iterable
            # all fns must return an iterable
            return [next(s)]
        except StopIteration:
            return [""]

class LastWord(Function, StringFnEval):
    name = "lastword"
    def eval(self, symbol_table):
        s = self.evaluate(symbol_table)
        last = [""]
        # s should be an iterable but we need the last element so have to
        # walk the whole list ; don't want to store the intermediate steps
        for last in s:
            pass
        return [last]

class Patsubst(TODOMixIn, Function):
    name = "patsubst"

class SortClass(Function, StringFnEval):
    name = "sort"

    # Sort does not take arguments function-style (commas are not interpreted
    # as separate arguments. Rather the entire single arg is interpreted as a
    # space separated list.
    def eval( self, symbol_table):
        step1 = self.evaluate(symbol_table)

        # returns an iterable of strings
        return sorted(step1)
        

class StripClass(Function, StringFnEval):
    name = "strip"

    def eval(self, symbol_table):
        step1 = self.evaluate(symbol_table)
        return [s.strip() for s in step1]

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
        index = [t.eval(symbol_table) for t in self.args[0]]
        text = [t.eval(symbol_table) for t in self.args[1]]

        index_str = "".join(flatten(index))

        try:
            index_num = int(index_str)
        except ValueError:
            raise ParseError

        if index_num <= 0:
            errmsg = "first argument to '{.name}' must be greater than 0.".format(self)
            logger.error(errmsg)
            raise EvalError(description=errmsg)

        breakpoint()
        counter = 0
        for s in flatten(text):
            counter += 1
            if counter == index_num:
                return [s]
        return [""]


class WordList(TODOMixIn, Function):
    name = "wordlist"

class Words(Function, StringFnEval):
    name = "words"
    # "Returns the number of words in text." -- GNU make manual

    def eval(self, symbol_table):
        s = self.evaluate(symbol_table)
        # s is an interable of strings
        # don't make into a list since we just want the length
        len_ = 0
        for word in s:
            len_ += 1
        return [str(len_)]


