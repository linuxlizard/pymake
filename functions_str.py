# functions for string substitution and analysis

import logging

logger = logging.getLogger("pymake.functions")

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

# Make is very whitespace sensitive so this is a little strange.  I'm
# going to comment this like crazy because the "why" will all leak
# from my brain the moment I move on.
#
# GNU Make works on whitespace separated strings. GNU Make will build a new
# string then split it on whitespace later. 
#
# My make works with arrays of Python strings (functions return an array of
# python strings). However, when I'm working with a Literal string
# containing spaces, I still need to treat those spaces as signifigant.
#
# My functions return an array of strings. My functions work with arrays of
# strings. An expression will be an array of function calls returning arrays of
# strings (yielding an array of array of strings). However, a literal string
# containing spaces will eval to the literal string which needs to be split
# into individual strings.
#
def strings_evaluate(token_list, symbol_table):
    # hilarious one liner
    return "".join( [" ".join(s_list) for s_list in [t.eval(symbol_table) for t in token_list]] ).split()

#    step1 = [t.eval(symbol_table) for t in token_list]
    # step1 will be an array of arrays of strings
    #
    # Contrived Example:
    # x=a e i o u
    # a=a ; b=b
    # $(filter $a$b $a $b  e  i  o  u   $(shell seq 1 1 10), $(x))
    # 
    # The eval'd array of array of string would be:
    #   [['a'], ['b'], [' '], ['a'], [' '], ['b'], [' e  i  o  u   '], ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']]
    # I need to collapse that to:
    #   ['ab', 'a', 'b', 'e', 'i', 'o', 'u', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    # Note the literal "e i o u" contains spaces.
    #
    # The inner " ".join combines neighboring strings of the inner lists ; each
    # inner list is a list of strings from Symbol.eval() (a function call or a
    # symbol table lookup; the function call result will be a list of strings
    # but a symbol table lookup could be a literal string containing spaces)
    # ['1', '2', '3', ...]  ->  "1 2 3 "...
    # [' e  i  o  u   '] -> " e  i  o  u   "
    #
    # outer "".join combines separate fields
    # ['a'],['b'] -> "ab"
    # ['a'],[' '],['b'] -> "a b"
    #
    # Then we have to re-split it on whitespace. Now we have an 1-D array of
    # python strings that can be used for any string fn operation.
    #
#    s = "".join( [" ".join(s_list) for s_list in step1] )
#    return s.split()
                

class FilterClass(FunctionWithArguments):
    name = "filter"
    num_args = 2

    def eval(self, symbol_table):
        assert len(self.args)==2, len(self.args)

        filter_on = strings_evaluate(self.args[0], symbol_table)
                
        targets = strings_evaluate(self.args[1], symbol_table)

        # TODO wildcards (yikes)
        print(f"filter filter_on={filter_on}")
        print(f"filter targets={targets}")
        value = [t for t in targets if t in filter_on]
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

    # "Sorts the words of list in lexical order, removing duplicate words. The
    # output is a list of words separated by single spaces." -- GNU Make manual

    # Sort does not take arguments function-style (commas are not interpreted
    # as separate arguments. Rather the entire single arg is interpreted as a
    # space separated list.
    def eval( self, symbol_table):
        s = strings_evaluate(self.token_list, symbol_table)
        # set() remove duplicates
        return sorted(set(s))
        

class StripClass(Function, StringFnEval):
    name = "strip"

    def eval(self, symbol_table):
        step1 = self.evaluate(symbol_table)
        return [s.strip() for s in step1]

class Subst(FunctionWithArguments):
    name = "subst"
    num_args = 3

    def eval(self, symbol_table):
        # Needs 3 args. The number of args shall be three. Five is right out.
        assert len(self.args)==3, len(self.args)
        logger.debug("%s len=%d args=%s", self.name, len(self.args), self.args)
        from_s = "".join(strings_evaluate(self.args[0], symbol_table))
        to_s = "".join(strings_evaluate(self.args[1], symbol_table))
#        text_s = strings_evaluate(self.args[2], symbol_table)

#        breakpoint()
        out_s = ""
        for a in self.args[2]:
            s = "".join(a.eval(symbol_table))
            out_s += s.replace(from_s, to_s)
        return [out_s]

#        from_s = "".join(t.eval(symbol_table) for t in self.args[0])
#        to_s = "".join(t.eval(symbol_table) for t in self.args[1])
#        text_s = "".join(t.eval(symbol_table) for t in self.args[2]) 

#        logger.debug("%s from=\"%s\" to=\"%s\" text=\"%s\"", self.name, from_s, to_s, text_s)
#        if not from_s:
#            # empty "from" leaves text unchanged
#            return text_s
#        s = text_s.replace(from_s, to_s)
#        logger.debug("%s \"%s\"", self.name, s)
#
#        return s

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

