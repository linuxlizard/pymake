# functions for string substitution and analysis

import re
import logging

logger = logging.getLogger("pymake.functions")

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn
from flatten import flatten
from wildcard import wildcard_replace, wildcard_match_list
from symbol import Literal
from whitespace import whitespace

__all__ = [ "FilterClass", "FilterOutClass", "FindString", "FirstWord", 
    "LastWord", "Patsubst", "SortClass", "StripClass", "Subst", 
    "Word", "WordList", "Words" ]

def evaluate_gen(token_list, symbol_table):
#        print(self.name, "token_list=", self.token_list)

    # evalutate all the things
    step1 = [t.eval(symbol_table) for t in token_list]
#        print(f"{self.name} step1={step1}")

    # returns an iterable across a 1-D array of strings
    step2 = flatten(step1)

    # strings within our iterable could be space separated words so break
    # up the individual strings into their space separated selves
    for s in step2:
        for word in s.split():
            yield word

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
# NOTE! This function destroys whitespace.  Cannot use this function when
#       whitespace must be preserved.
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
    preserve_ws = False

    def eval(self, symbol_table):
        assert len(self.args)==2, len(self.args)

        tmp = list(evaluate_gen(self.args[0], symbol_table))

        filter_on = strings_evaluate(self.args[0], symbol_table)
        if tmp!=filter_on:
            print(f"FAILURE {tmp} != {filter_on}")
#        assert list(tmp)==filter_on
                
        targets = strings_evaluate(self.args[1], symbol_table)

        # TODO wildcards (yikes)
#        print(f"filter filter_on={filter_on}")
#        print(f"filter targets={targets}")
        return wildcard_match_list(filter_on, targets)

#       value = [t for t in targets if t in filter_on]


class FilterOutClass(TODOMixIn, Function):
    name = "filter-out"

class FindString(FunctionWithArguments):
    name = "findstring"
    num_args = 2
    preserve_ws = False

    # "Searches in for an occurrence of find. If it occurs, the value is find; otherwise,
    # the value is empty."
    # No duplicates. Substring finds are valid ("the" in "their")
    #
    # Whitespace is preserved in both the search and target strings ("a b"
    # matches "a b" vs "a" "b" not matching "a b")
    #
    def eval(self, symbol_table):
        seek = [t.eval(symbol_table) for t in self.args[0]]
        text = [t.eval(symbol_table) for t in self.args[1]]

        seek_str = "".join(flatten(seek))
        text_str = "".join(flatten(text))

        return [seek_str] if seek_str in text_str else [""]


class FirstWord(Function, StringFnEval):
    name = "firstword"
    preserve_ws = False

    def eval(self, symbol_table):
        s = strings_evaluate(self.token_list, symbol_table)
        try:
            return [ s[0] ]
        except IndexError:
            return [""]

#        s = self.evaluate(symbol_table)
#        try:
#            # s should be an iterable
#            # all fns must return an iterable
#            return [next(s)]
#        except StopIteration:
#            return [""]

class LastWord(Function, StringFnEval):
    name = "lastword"
    preserve_ws = False

    def eval(self, symbol_table):
        s = strings_evaluate(self.token_list, symbol_table)
        if len(s) == 0:
            return [""]
        return [ s[-1] ]

#        s = self.evaluate(symbol_table)
#        last = ""
#        # s should be an iterable but we need the last element so have to
#        # walk the whole list ; don't want to store the intermediate steps
#        for last in s:
#            pass
#        return [last]

class Patsubst(FunctionWithArguments):
    name = "patsubst"
    num_args = 3
    preserve_ws = True

    # "Finds whitespace-separated words in text that match pattern and replaces them
    # with replacement. Here pattern may contain a ‘%’ which acts as a wildcard,
    # matching any number of any characters within a word. If replacement also con-
    # tains a ‘%’, the ‘%’ is replaced by the text that matched the ‘%’ in pattern. Only
    # the first ‘%’ in the pattern and replacement is treated this way; any subsequent
    # ‘%’ is unchanged."
    #
    # "Whitespace between words is folded into single space characters; leading and
    # trailing whitespace is discarded."
    #
    # GNU make Version 4.3 January 2020  Section 8.2 page 88
    #
    # Except that's not exactly what happens. Unchanged strings leave
    # whitespace in-place.  Except the pattern-less $(patsubst) decays to a
    # special case of $(subst)
    #
    # $(info 3 >>$(patsubst foo,bar,   foo    bar     baz    )<<)
    # output:
    # >>   bar    bar     baz    << 
    #

    def _re_subst(self, from_s, to_s, target):
        # any exact match of our from_s surrounded by whitespace or at beginning or end of line
        rex = re.compile( r"(^|\s)" + re.escape(from_s) + r"(\s|$)" )

        start = 0
        new_s = ""
        while 1 :
            robj = rex.search(target, start)
            if not robj:
                new_s += target[start:]
                break
            print(f"re_sub target={target} robj={robj}")

            # g0 - char that matched before our substring
            # g1 - char that matched after our substring
            # g0,g1 will be empty at start, end of line respectively
            # The len() allows us to capture the char before/after the match except
            # for beginning/end of line
            g0,g1 = robj.groups()

            end = robj.start() + len(g0)
            new_s += target[start:end] + to_s 

            # search for next 
            # The len(g1) pulls in char after substring except for end of line
            start = robj.end() - len(g1)

        print(f"re_subst new_s={new_s}")
        return new_s

    def subst(self, from_s, to_s, symbol_table):
        # Does $(patsubst) decay to $(subst) if pattern has no wildcards???
        # (runs off and reads make 4.3 source) Yes! Yes it does!
        #
        # Sort-of.  See "by_word" 
        # TODO write more docs once I fully understand what's going on 
        #
        # Must very carefully preserve whitespace between strings.
        # $(patsubst) collapses whitespace except when there is no wildcard in
        # which case it decays to a special case of $(subst) which preserves
        # whitespace (normal $(subst) does not preserve whitespace)

#        breakpoint()
#        print(f"patsubst-subst from_s=\"{from_s}\" to_s=\"{to_s}\"")

        text_list = [a.eval(symbol_table) for a in self.args[2] ]
#        print(f"subst text={text_list}")

        # no "from" then we just return the text list
        # $(patsubst ,z,a c d e f g) -> a b c d e f g
        # $(subst ,z,a c d e f g) -> a b c d e f gz
        # $(patsubst a,,a c d e f g) ->  b c d e f g
        if not from_s:
            # FIXME I need to return an array
            return "".join(flatten(text_list))

        # when patsubst decays to subst(ish), GNU make will only replace whole
        # whitespace delimited words (exact match required)
        # !!! whitespace must be preserved !!!
        # therefore cannot use strings_evaluate()

        # The "".join() is weird ; I'd be returning a single string rather than array of string(s).
        # The patsubst->subst needs to preserve all intermediate whitespace, adding no new whitespace
        return [ "".join( [ self._re_subst(from_s, to_s, str_) for str_ in flatten(text_list)] ) ]


    def eval(self, symbol_table):
        assert len(self.args)==3, len(self.args)

        # what happens with spaces in the pattern arg(s) ?
        # I think it falls into a strange case where there can be no match
        # because the target is split on whitespace.
        # e.g., $(patsubst a b,q,a b a b a b) -> no change

        pattern = "".join(flatten([a.eval(symbol_table) for a in self.args[0]]))
        replacement = "".join(flatten([a.eval(symbol_table) for a in self.args[1]]))

        breakpoint()
#        print(f"pattern={pattern} replace={replacement}")
        if not '%' in pattern:
            # decays to strange sub-case of $(subst) substitution
            return self.subst(pattern, replacement, symbol_table)

        # NOW can use strings_evaluate()  (whitespace can be destroyed)
        text = strings_evaluate(self.args[2], symbol_table)

        # array of array of strings
#        text_list = [a.eval(symbol_table) for a in self.args[2]]

#        pattern = strings_evaluate(self.args[0], symbol_table)
#        replacement= strings_evaluate(self.args[1], symbol_table)
#        text = strings_evaluate(self.args[2], symbol_table)
#        assert len(pattern)==1, len(pattern)
#        assert len(replacement)==1, len(replacement)

        new_ = wildcard_replace(pattern, replacement, text)
#        print(f"new={new_}")

        # This class marked whitespace preserving so need to add new whitespace
        # between the strings where we destroyed the whitespace
        return [" ".join(new_)]

class SortClass(Function, StringFnEval):
    name = "sort"
    preserve_ws = False

    # "Sorts the words of list in lexical order, removing duplicate words. The
    # output is a list of words separated by single spaces." 
    # ...
    # "Incidentally, since sort removes duplicate words, you can use it for this purpose
    # even if you don’t care about the sort order."
    #
    # -- GNU Make manual

    # Sort does not take arguments function-style (commas are not interpreted
    # as separate arguments. Rather the entire single arg is interpreted as a
    # space separated list.
    def eval( self, symbol_table):
        s = strings_evaluate(self.token_list, symbol_table)
        # set() remove duplicates
        return sorted(set(s))
        

class StripClass(Function, StringFnEval):
    name = "strip"
    preserve_ws = False

    def eval(self, symbol_table):
#        s = strings_evaluate(self.token_list, symbol_table)
#        breakpoint()

        step1 = self.evaluate(symbol_table)
        return [s.strip() for s in step1]

class Subst(FunctionWithArguments):
    name = "subst"
    num_args = 3
    preserve_ws = True

    # $(subst from,to,text)
    # "Performs a textual replacement on the text text: each occurrence of from is
    # replaced by to. The result is substituted for the function call."

    def eval(self, symbol_table):
        # Needs 3 args. The number of args shall be three. Five is right out.
        logger.debug("%s len=%d args=%s", self.name, len(self.args), self.args)
        assert len(self.args)==3, len(self.args)

        from_s = "".join(flatten([a.eval(symbol_table) for a in self.args[0]]))
        to_s = "".join(flatten([a.eval(symbol_table) for a in self.args[1]]))

        # array of array of strings
        text_list = [a.eval(symbol_table) for a in self.args[2]]

        # weird special case: when the 'from' text is empty, GNU Make 4.3
        # (haven't tested other versions (yet)) will append the 'to' at the end
        # of 'text'
        # $(subst ,z,a c d e f g) -> a b c d e f gz
        if not from_s:
            # need to carefully preserve whitespace
            return "".join(flatten(text_list)) + to_s

        # TODO make a list comprehension because more nifitier
        out_s = ""
        for t in text_list:
            s = "".join(t)
            out_s += s.replace(from_s, to_s)
        return [out_s]

#        out_s = ""
#        for a in self.args[2]:
#            s = "".join(a.eval(symbol_table))
#            out_s += s.replace(from_s, to_s)
#        return [out_s]

#        return "".join([s.replace(from_s, to_s) for s in text_list])

class Word(FunctionWithArguments):
    name = "word"
    num_args = 2
    preserve_ws = False

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


class WordList(TODOMixIn, FunctionWithArguments):
    name = "wordlist"
    num_args = 3
    preserve_ws = False

    # "Returns the list of words in text starting with word s and ending with word e
    # (inclusive). The legitimate values of s start from 1; e may start from 0. If s is
    # bigger than the number of words in text, the value is empty. If e is bigger than
    # the number of words in text, words up to the end of text are returned. If s is
    # greater than e, nothing is returned." -- GNU Make manual


class Words(Function, StringFnEval):
    name = "words"
    preserve_ws = False

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

