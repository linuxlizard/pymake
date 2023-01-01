# SPDX-License-Identifier: GPL-2.0
# Functions for string substitution and analysis
#
# Make is very whitespace sensitive so this is a little strange.  I'm
# going to comment this like crazy because the "why" will all leak
# from my brain the moment I move on.
#
# GNU Make works on whitespace separated strings. GNU Make will build a new
# string then split it on whitespace later. 
#
# 20220918  Passing around array of strings won't work, there are too many
# corner cases for whitespace and printing. Let's try mimicing gnu-make itself
# and simply operate on strings. Each function eval() returns a python string.
# Any function that needs to operate on whitespace separated words within that
# string will need to split() (then " ".join() the results).

import re
import logging

logger = logging.getLogger("pymake.functions")

from error import *
from functions_base import Function, FunctionWithArguments
from flatten import flatten
from wildcard import wildcard_replace, wildcard_match_list
from symbol import Literal
from constants import whitespace

__all__ = [ "FilterClass", "FilterOutClass", "FindString", "FirstWord", 
    "LastWord", "Patsubst", "SortClass", "StripClass", "Subst", 
    "Word", "WordList", "Words" ]
    
# mix-in to parse an arg that needs to be interpretted as a non-zero integer
class IntegerArgument:
    def int_parse(self, token_list, symbol_table, **kwargs):
        # array of strings
        step1 = [t.eval(symbol_table) for t in token_list]

        # squish together to make a single string
        str_ = "".join(step1)

        errmsg = None

        # TODO need "first", "second" strings for arg_position

        try:
            num = int(str_)
        except ValueError:
            errmsg = "non-numeric {0} argument to '{1}' function: ".format(
                arg_position, self.name)
            raise ParseError

        min_value = kwargs.get("min", None)
        max_value = kwargs.get("max", None)

        if min_value is not None and num < min_value:
            errmsg = "argument to '{0}' must be greater than {1}.".format(
                self.name, min_value)
        elif max_value is not None and num > max_value:
            errmsg = "argument to '{0}' must be less than {1}.".format(
                self.name, max_value)

        if errmsg:
            logger.error(errmsg)
            filename, pos = self.get_pos()
            raise EvalError(filename=filename, pos=pos, msg=errmsg)

        return num 


class FilterClass(FunctionWithArguments):
    name = "filter"
    num_args = 2

    # $(filter pattern...,text)
    # "Returns all whitespace-separated words in text that do match any of the pattern
    # words, removing any words that do not match. The patterns are written using
    # ‘%’, just like the patterns used in the patsubst function above."
    #
#    def _mkpattern(self, symbol_table):
#        pattern_step1 = [t.eval(symbol_table) for t in self.args[0]]
#        pattern_step2 = "".join(pattern_step1).split()
#        return pattern_step2
#
#    def _mktext(self, symbol_table):
#        text_step1 = [t.eval(symbol_table) for t in self.args[1]]
#        text_step2 = "".join(text_step1).split()
#        return text_step2

    def eval(self, symbol_table):
        assert len(self.args)==2, len(self.args)
        
        # $(filter) destroys intermediate whitespace

        # array of strings
        pattern_step1 = [t.eval(symbol_table) for t in self.args[0]]
        pattern_step2 = "".join(pattern_step1).split()

        text_step1 = [t.eval(symbol_table) for t in self.args[1]]
        text_step2 = "".join(text_step1).split()

        return " ".join(wildcard_match_list(pattern_step2, text_step2, self.name=="filter-out"))

class FilterOutClass(FilterClass):
    name = "filter-out"

class FindString(FunctionWithArguments):
    name = "findstring"
    num_args = 2

    # $(findstring find,in)
    # "Searches in for an occurrence of find. If it occurs, the value is find; otherwise,
    # the value is empty."
    #
    # No duplicates. Substring finds are valid ("the" in "their")
    #
    # Whitespace is preserved in both the search and target strings ("a b"
    # matches "a b" vs "a" "b" not matching "a b")
    #
    def eval(self, symbol_table):
        seek = [t.eval(symbol_table) for t in self.args[0]]
        text = [t.eval(symbol_table) for t in self.args[1]]

        # whitespace must be preserved!!!
        seek_str = "".join(flatten(seek))
        text_str = "".join(flatten(text))

        return seek_str if seek_str in text_str else ""


class FirstWord(Function):
    name = "firstword"

    def eval(self, symbol_table):
        # array of strings
        step1 = [t.eval(symbol_table) for t in self.token_list]
        step2 = "".join(step1).split()

        try:
            return step2[0]
        except IndexError:
            return ""

class LastWord(Function):
    name = "lastword"

    def eval(self, symbol_table):
        # array of strings
        step1 = [t.eval(symbol_table) for t in self.token_list]
        step2 = "".join(step1).split()

        if len(step2) == 0:
            return ""

        return step2[-1]

class Patsubst(FunctionWithArguments):
    name = "patsubst"
    num_args = 3

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

        # tricky part is I need overlapping regex matches
        #   <space1>a<space2>b<space3>
        # needs to make matches:
        #   <space1>a<space2>
        #   <space2>b<space3>
        # finditer() doesn't do overlapping
        start = 0
        new_s = ""
        while 1 :
            robj = rex.search(target, start)
            if not robj:
                new_s += target[start:]
                break
#            print(f"re_sub target={target} robj={robj}")

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

#        print(f"re_subst new_s={new_s}")
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

        # array of strings where whitespace must be carefully preserved
        text_list = [a.eval(symbol_table) for a in self.args[2] ]
#        print(f"subst text={text_list}")

        # no "from" then we just return the text list
        # $(patsubst ,z,a c d e f g) -> a b c d e f g
        # $(subst ,z,a c d e f g) -> a b c d e f gz
        # $(patsubst a,,a c d e f g) ->  b c d e f g
        if not from_s:
            # I need to return a string
            return "".join(text_list)

        # when patsubst decays to subst(ish), GNU make will only replace whole
        # whitespace delimited words (exact match required)
        # !!! whitespace must be preserved !!!

        return "".join( [ self._re_subst(from_s, to_s, str_) for str_ in text_list] )


    def eval(self, symbol_table):
        assert len(self.args)==3, len(self.args)

        # what happens with spaces in the pattern arg(s) ?
        # I think it falls into a strange case where there can be no match
        # because the target is split on whitespace.
        # e.g., $(patsubst a b,q,a b a b a b) -> no change

        pattern = "".join(flatten([a.eval(symbol_table) for a in self.args[0]]))
        replacement = "".join(flatten([a.eval(symbol_table) for a in self.args[1]]))

#        print(f"pattern={pattern} replace={replacement}")
        if not '%' in pattern:
            # decays to strange sub-case of $(subst) substitution
            return self.subst(pattern, replacement, symbol_table)

        # NOW can whitespace can be destroyed
        text = flatten([a.eval(symbol_table).split() for a in self.args[2]])

        new_ = wildcard_replace(pattern, replacement, text)
#        print(f"new={new_}")

        # This class marked whitespace preserving so need to add new whitespace
        # between the strings where we destroyed the whitespace
        return " ".join(new_)

class SortClass(Function):
    name = "sort"

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

        # list of strings
        str_list = [t.eval(symbol_table) for t in self.token_list]

        s = "".join(str_list).split()

        # set() remove duplicates
        return " ".join(sorted(set(s)))
        

class StripClass(Function):
    name = "strip"

    # "Removes leading and trailing whitespace from string and replaces each inter-
    # nal sequence of one or more whitespace characters with a single space."
    #
    def eval(self, symbol_table):
        # TODO collapse this to fewer steps

        # array of strings
        step1 = [t.eval(symbol_table) for t in self.token_list]

        step2 = [str_.split() for str_ in step1]

        return " ".join(flatten(step2))


class Subst(FunctionWithArguments):
    name = "subst"
    num_args = 3

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
            return "".join(text_list) + to_s

        # TODO make a list comprehension because more nifitier
        out_s = ""
        for t in text_list:
            s = "".join(t)
            out_s += s.replace(from_s, to_s)
        return out_s


class Word(FunctionWithArguments):
    name = "word"
    num_args = 2

    # $(word n,text)
    # "Returns the nth word of text. The legitimate values of n start from 1. If n is
    # bigger than the number of words in text, the value is empty."
    #
    # killall the whitespace! woo!
    def eval(self, symbol_table):
        # index wil be array of strings
        index = [t.eval(symbol_table) for t in self.args[0]]

        # TODO does gnu make evaluate the 2nd argument before or after
        # determining the 1st argument (the index) is correct?
        # (ie, is gnu make short circuiting the expression?)
        # Is important because the eval() might have side effects.
        text = flatten([t.eval(symbol_table).split() for t in self.args[1]])

        # TODO convert to int_parse()
        # squish together to make a single string
        index_str = "".join(index)

        try:
            index_num = int(index_str)
        except ValueError:
            errmsg = "non-numeric first argument to '{0}' function: '{1}'".format(self, index_str)
            raise InvalidFunctionArguments(pos=self.get_pos(), msg=errmsg)

        if index_num <= 0:
            errmsg = "first argument to '{.name}' must be greater than 0.".format(self)
            raise InvalidFunctionArguments(pos=self.get_pos(), msg=errmsg)

        # text is an iterable yielding strings
        counter = 0
        for word in text:
            counter += 1
            if counter == index_num:
                return word
        return ""


class WordList(FunctionWithArguments, IntegerArgument):
    name = "wordlist"
    num_args = 3

    # $(wordlist s,e,text)
    # "Returns the list of words in text starting with word s and ending with word e
    # (inclusive). The legitimate values of s start from 1; e may start from 0. If s is
    # bigger than the number of words in text, the value is empty. If e is bigger than
    # the number of words in text, words up to the end of text are returned. If s is
    # greater than e, nothing is returned." -- GNU Make manual

    # Leading/trailing whitespace is discarded.
    # Intermediate whitespace is preserved.
    def eval(self, symbol_table):
        start_idx = self.int_parse(self.args[0], symbol_table, min=1)
        end_idx = self.int_parse(self.args[1], symbol_table, min=0)

        # TODO see also Word()
        # Does gnu make short-circuit the checks?  No.
        # $(wordlist 3,2,$(shell touch /tmp/tmp.txt))  <-- /tmp/tmp.txt will exist

        # array of strings into a single string
        text = "".join([t.eval(symbol_table) for t in self.args[2]])

        # GNU make slicing is 1-based, python slicing is zero based.
        # Don't need to modify end_idx because python slicing is [) (end is not
        # included) but gnu make slicing is [] (end is included).  So the end
        # index is already one larger than it needs to be.
#        start_idx -= 1

        if start_idx >= end_idx :
            return ""

        # whitespace between symbols is preserved.
        # Leading/trailing whitespace discarded.
        text = text.strip()

        if not len(text):
            return ""

        state_word = 1
        state_ws = 2

        word_start_pos = 0
        word_counter = 0
        slice_start = -1 
        pos = 0

        # starting state
        if text[pos] in whitespace:
            state = state_ws
        else:
            state = state_word
            word_start_pos = pos
        pos += 1

        while pos < len(text) :
            if state == state_ws:
                if not text[pos] in whitespace:
                    # Transition from whitespace to word.
                    # Save the startion position of this word.
                    state = state_word
                    word_start_pos = pos

            elif state == state_word:
                if text[pos] in whitespace:
                    # Transition from word to whitespace.
                    # Check our wordlist boundaries.
                    word_counter += 1
                    if word_counter == start_idx:
                        slice_start = word_start_pos
                    elif word_counter == end_idx:
                        # yay! we're done
                        return text[slice_start:pos]

                    state = state_ws

            else:
                assert 0, state # wtf?

            pos += 1

        # at this point, we have run out of string without finding our
        # start/end
        if state == state_word:
            # end of string means end of word
            word_counter += 1
            if word_counter == start_idx:
                slice_start = word_start_pos
            elif word_counter == end_idx:
                # yay! we're done
                return text[slice_start:pos]

        if slice_start == -1:
            # we ain't found sh*t
            return ""

        # at this point, we've run off the end of the string without finding
        # the end_idx word so just return as much string from the start_idx
        # to the end
        return text[slice_start:]

        # aw fuck whitespace between symbols is preserved.
        # Leading/trailing whitespace discarded.
        # So this won't work.
#        text_list = list(flatten([str_.split() for str_ in text]))

#        return " ".join(text_list[start_idx:end_idx])

class Words(Function):
    name = "words"

    # "Returns the number of words in text." -- GNU make manual

    def eval(self, symbol_table):
        # array of strings
        step1 = [t.eval(symbol_table) for t in self.token_list]
        # array of array of strings
        step2 = [str_.split() for str_ in step1]
        # TODO is there a better way to do this? w/o creating a list() 
        # (iterate over the flatten()'d result with a counter?)
        return str(len(list(flatten(step2))))

