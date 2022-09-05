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

        # returns an iterable across a 1-D array of strings
        step2 = flatten(step1)

        # strings within our iterable could be space separated words so break
        # up the individual strings into their space separated selves
        for s in step2:
            for word in s.split():
                yield word


class FilterClass(FunctionWithArguments):
    name = "filter"
    num_args = 2

    def eval(self, symbol_table):
        assert len(self.args)==2, len(self.args)

        breakpoint()
        step1 = [a.eval(symbol_table) for a in self.args[0]]
        filter_on = "".join(flatten(step1)).split()

        step1 = [a.eval(symbol_table) for a in self.args[1]]
        targets = "".join(flatten(step1)).split()

#        breakpoint()
        """
        for a in self.args[1]:
            # eval() returns a list of strings
            s_list = a.eval(symbol_table)
            for s in s_list:
                for f in s.split():
#                    print(f"split f={f}")
                    pass
        """

#        filter_on = [f for a in self.args[0] for s in a.eval(symbol_table) for f in s.split()]
#        targets = [f for a in self.args[1] for s in a.eval(symbol_table) for f in s.split()]

        value = [t for t in targets if t in filter_on]
        return value


        step2 = flatten(step1)
        filter_on = list(flatten([s.split() for s in step2]))
        print(f"split filter={filter_on}")

        step1 = [a.eval(symbol_table) for a in self.args[1]]
        step2 = flatten(step1)
        targets = list(flatten([s.split() for s in step2]))
        print(f"split targets={targets}")

        value = [t for t in targets if t in filter_on]
        print(f"split value={value}")

        return value

class FilterOutClass(TODOMixIn, Function):
    name = "filter-out"

class FindString(FunctionWithArguments):
    name = "findstring"
    num_args = 2

    def eval(self, symbol_table):
        seek = [t.eval(symbol_table) for t in self.args[0]]
        text = [t.eval(symbol_table) for t in self.args[1]]

        seek_str = "".join(flatten(seek))

        for s in flatten(text):
            for word in s.split():
                if word==seek_str:
                    return [word]

        return [""]


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
        last = ""
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

        counter = 0
        for s in flatten(text):
            for word in s.split():
                counter += 1
                if counter == index_num:
                    return [word]
        return [""]


class WordList(TODOMixIn, Function):
    name = "wordlist"

    # "Returns the list of words in text starting with word s and ending with word e
    # (inclusive). The legitimate values of s start from 1; e may start from 0. If s is
    # bigger than the number of words in text, the value is empty. If e is bigger than
    # the number of words in text, words up to the end of text are returned. If s is
    # greater than e, nothing is returned." -- GNU Make manual

class Words(Function, StringFnEval):
    name = "words"
    # "Returns the number of words in text." -- GNU make manual

    def eval(self, symbol_table):
        step1 = self.evaluate(symbol_table)
        # step1 is an interable of strings
        # don't make into a list since we just want the length
        len_ = 0
        # strings within our iterable could be space separated words so break
        # up the individual strings into their space separated selves
#        for s in step1:
#            words = s.split()            
#            for w in words:
#                len_ += 1

        for s in step1:
            len_ += 1
        return [str(len_)]


