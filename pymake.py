#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

import sys
import logging

logger = logging.getLogger("pymake")
#logging.basicConfig(level=logging.DEBUG)

# require Python 3.x for best Unicode handling
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import hexdump
from scanner import ScannerIterator
import vline
from vline import VirtualLine
from printable import printable_char, printable_string
from symbol import *
from error import *
from version import Version
import functions 
import source

#whitespace = set( ' \t\r\n' )
whitespace = set(' \t')

# davep 04-Dec-2014 ; FIXME ::= != are not in Make 3.81, 3.82 (Introduced in 4.0)
assignment_operators = {"=", "?=", ":=", "::=", "+=", "!="}
rule_operators = {":", "::"}
eol = set("\r\n")

# eventually will need to port this thing to Windows' CR+LF
platform_eol = "\n"

recipe_prefix = "\t"

# 4.8 Special Built-In Target Names
built_in_targets = {
    ".PHONY",
    ".SUFFIXES",
    ".DEFAULT",
    ".PRECIOUS",
    ".INTERMEDIATE",
    ".SECONDARY",
    ".SECONDEXPANSION",
    ".DELETE_ON_ERROR",
    ".IGNORE",
    ".LOW_RESOLUTION_TIME",
    ".SILENT",
    ".EXPORT_ALL_VARIABLES",
    ".NOTPARALLEL",
    ".ONESHELL",
    ".POSIX",
}

#
# Stuff from Appendix A.
#

# Conditionals separate because conditionals can be multi-line and require some
# complex handling.
conditional_directive = {
    "ifdef", "ifndef", 
    # newer versions of Make? (TODO verify when these appeared)
    "ifeq", "ifneq"
}

# all directives
directive = {
    "define", "enddef", "undefine",
    "else", "endif",
    "include", "-include", "sinclude",
    "override", 
    "export", "unexport",
    "private", 
    "vpath",
} | conditional_directive

automatic_variables = {
    "@",
    "%",
    "<",
    "?",
    "^",
    "+",
    "*",
    "@D",
    "@F",
    "*D",
    "*F",
    "%D",
    "%F",
    "<D",
    "<F",
    "^D",
    "^F",
    "+D",
    "+F",
    "?D",
    "?F",
}

builtin_variables = {
    "MAKEFILES",
    "VPATH",
    "SHELL",
    "MAKESHELL",
    "MAKE",
    "MAKE_VERSION",
    "MAKE_HOST",
    "MAKELEVEL",
    "MAKEFLAGS",
    "GNUMAKEFLAGS",
    "MAKECMDGOALS",
    "CURDIR",
    "SUFFIXES",
    ".LIBPATTEREN",
}

def comment(string):
    state_start = 1
    state_eat_comment = 2

    state = state_start

    # this could definitely be faster (method in ScannerIterator to eat until EOL?)
    for vchar in string : 
        c = vchar["char"]
        print("# c={0} state={1}".format(printable_char(c),state))
        if state==state_start:
            if c=='#':
                state = state_eat_comment
            else:
                # shouldn't be here unless we're eating a comment
                raise ParseError()

        elif state==state_eat_comment:
            # comments finish at end of line
            if c in eol :
                return
            # otherwise char is eaten

        else:
            # should not get here
            assert 0, state

depth = 0
def depth_reset():
    # reset the depth (used when testing the depth checker)
    global depth
    depth = 0

def depth_checker(func):
    # Avoid very deep recurssion into tokenizers.
    # Note this uses a global so is NOT thread safe.
    def check_depth(*args):
        global depth
        depth += 1
        if depth > 10 : 
            raise NestedTooDeep(depth)
        ret = func(*args)
        depth -= 1

        # shouldn't happen!
        assert depth >= 0, depth 

        return ret

    return check_depth

#@depth_checker
def tokenize_statement(string):
    # at start of scanning, we don't know if this is a rule or an assignment
    # this is a test : foo   -> (this,is,a,test,:,)
    # this is a test = foo   -> (this is a test,=,)
    #
    # I first tokenize assuming it's an assignment statement. If the final
    # token is a rule token, then I re-tokenize as a rule.
    #
    # Only difference between a rule LHS and an assignment LHS is the
    # whitespace. In a rule, the whitespace is ignored. In an assignment, the
    # whitespace is preserved.

    # get the starting position of this string (for error reporting)
    starting_pos = string.lookahead()["pos"]

    logger.debug("tokenize_statement() pos=%s", starting_pos)

    # save current position in the token stream
    string.push_state()
    lhs = tokenize_statement_LHS(string)
    
    # should get back a list of stuff in the Symbol class hierarchy
    assert type(lhs)==type(()), (type(lhs),)
    for token in lhs : 
        assert isinstance(token,Symbol),(type(token),token)

    # decode what kind of statement do we have based on where
    # tokenize_statement_LHS() stopped.
    last_symbol = lhs[-1]

    logger.debug("lhs=%s len=%d", lhs[-1], len(lhs))

    if isinstance(last_symbol,RuleOp): 
        statement_type = "rule"

        # I'm including Unicode literal in the string to force myself to learn
        # Python3 Unicode handling
#        print( u"last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
#        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        logger.debug( "last_token=%s ∴ statement is %s so re-run as rule", last_symbol, statement_type)

        # jump back to starting position
        string.pop_state()
        # re-tokenize as a rule (backtrack)
        lhs = tokenize_statement_LHS(string,whitespace)
    
        # add rule RHS
        # rule RHS  ::= assignment
        #           ::= prerequisite_list
        #           ::= <empty>
        statement = list(lhs)
        statement.append( tokenize_rule_prereq_or_assign(string) )

        # don't look for recipe(s) yet
        return RuleExpression( statement ) 

    elif isinstance(last_symbol,AssignOp): 
        statement_type = "assignment"

#        print( u"last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
#        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        logger.debug( "last_token=%s ∴ statement is %s", last_symbol, statement_type)

        # The statement is an assignment. Tokenize rest of line as an assignment.
        statement = list(lhs)
        statement.append(tokenize_assign_RHS( string ))
        return AssignmentExpression( statement )

    elif isinstance(last_symbol,Expression) :
        statement_type="expression"
#        print( u"last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        logger.debug( "last_token=%s ∴ statement is %s", last_symbol, statement_type)

        # davep 17-Nov-2014 ; the following code makes no sense 
        # Wind up in this case when have a non-rule and non-assignment.
        # Will get here with $(varref) e.g., $(info) $(shell) $(call) 
        # Also get here with an 'export' RHS.
        # Will get here when parsing multi-line 'define'.
        # Need to find clean way to return clean Expression and catch parse
        # error

        # The statement is a directive or bare words or function call. We
        # better have consumed the whole thing.
        assert len(string.remain())==0, (len(string.remain(),starting_pos))
        
        # Should be one big Expression. We'll dig into the Expression during
        # the 2nd pass.
        assert len(lhs)==1,(len(lhs),str(lhs),starting_pos)

        return lhs[0]

    else:
        statement_type="????"
#        print( "last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type))

        # should not get here
        assert 0,last_symbol

#@depth_checker
def tokenize_statement_LHS(string,separators=""):
    # Tokenize the LHS of a rule or an assignment statement. A rule uses
    # whitespace as a separator. An assignment statement preserves internal
    # whitespace but leading/trailing whitespace is stripped.

    logger.debug("tokenize_statement_LHS()")

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4
    state_colon = 5
    state_colon_colon = 6

    state = state_start
    token = ""

    token_list = []

    # Before can disambiguate assignment vs rule, must parse forward enough to
    # find the operator. Otherwise, the LHS between assignment and rule are
    # identical.
    #
    # BNF is sorta
    # Statement ::= Assignment | Rule | Directive | Expression
    # Assignment ::= LHS AssignmentOperator RHS
    # Rule       ::= LHS RuleOperator RHS
    # Directive  ::= TODO
    # Expression ::= TODO
    #
    # Directive is stuff like ifdef export vpath define. Directives get
    # slightly complicated because
    #   ifdef :  <--- not legal
    #   ifdef:   <--- legal (verified 3.81, 3.82, 4.0)
    #   ifdef =  <--- legal
    #   ifdef=   <--- legal
    # 
    # Expression is single function like $(info) $(warning). Not all functions
    # are valid in statement context. TODO finish directive.mk to discover
    # which directives are legal in statement context.
    # A lone expression in GNU make usually triggers the "missing separator"
    # error.
    #

    # get the starting position of this string (for error reporting)
    starting_pos = string.lookahead()["pos"]
    logger.debug("starting_pos=%s",starting_pos)

    for vchar in string : 
        c = vchar["char"]
#        print("s c={0} state={1} idx={2} ".format(printable_char(c),state,string.idx,token))
        if state==state_start:
            # always eat whitespace while in the starting state
            if c in whitespace : 
                # eat whitespace
                pass
            elif c==':':
                state = state_colon
            else :
                # whatever it is, push it back so can tokenize it
                string.pushback()
                state = state_in_word

        elif state==state_in_word:
            if c=='\\':
                state = state_backslash

            # whitespace in LHS of assignment is significant
            # whitespace in LHS of rule is ignored
            elif c in separators :
                # end of word
                token_list.append( Literal(token) )

                # restart token
                token = ""

                # jump back to start searching for next symbol
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # capture anything we might have seen 
                if token : 
                    token_list.append(Literal(token))
                # eat the comment 
                string.pushback()
                comment(string)

            elif c==':':
                # end of LHS (don't know if rule or assignment yet)
                # strip trailing whitespace
                token_list.append( Literal(token.rstrip()) )
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if string.lookahead()["char"]=='=':
                    string.next()
                    token_list.append(Literal(token.rstrip()))
                    return Expression(token_list),AssignOp(c+'=')
                else:
                    token += c

            elif c=='=':
                # definitely an assignment 
                # strip trailing whitespace
                token_list.append(Literal(token.rstrip()))
                return Expression(token_list),AssignOp("=")

            elif c in eol : 
                # end of line; bail out
                if token : 
                    # capture any leftover when the line ended
                    token_list.append(Literal(token))
                break
                
            else :
                token += c

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token so far; note no rstrip()!
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state=state_in_word

        elif state==state_backslash :
            if c in eol : 
                # line continuation
                # davep 04-Oct-2014 ; XXX   should not see anymore
                print("string={0} data={1}".format(type(string),type(string.data)))
                print(string.data)
                assert 0, (string, vchar)
            else :
                # literal '\' + somechar
                token += '\\'
                token += c
            state = state_in_word

        elif state==state_colon :
            # assignment end of LHS is := or ::= 
            # rule's end of target(s) is either a single ':' or double colon '::'
            if c==':':
                # double colon
                state = state_colon_colon
            elif c=='=':
                # :=
                # end of RHS
                return Expression(token_list), AssignOp(":=") 
            else:
                # Single ':' followed by something. Whatever it was, put it back!
                string.pushback()
                # successfully found LHS 
                return Expression(token_list),RuleOp(":")

        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                return Expression(token_list), AssignOp("::=") 
            string.pushback()
            # successfully found LHS 
            return Expression(token_list), RuleOp("::") 

        else:
            # should not get here
            assert 0,state

    # hit end of string; what was our final state?
    if state==state_colon:
        # Found a Rule
        # ":"
        assert len(token_list),starting_pos
        return Expression(token_list), RuleOp(":") 
    elif state==state_colon_colon:
        # Found a Rule
        # "::"
        assert len(token_list),starting_pos
        return Expression(token_list), RuleOp("::") 
    elif state==state_in_word :
        # Found a ????
        # likely word(s) or a $() call. For example:
        # a b c d
        # $(info hello world)
        # davep 17-Nov-2014 ; using this function to tokenize 'export' RHS
        # which could be just a list of variables e.g., export CC LD RM 
        # Return a raw expression that will have to be tokenize/parsed
        # downstream.
        return Expression(token_list), 

    # should not get here
    assert 0, (state,starting_pos)

#@depth_checker
def tokenize_rule_prereq_or_assign(string):
    # We are on the RHS of a rule's : or ::
    # We may have a set of prerequisites
    # or we may have a target specific assignment.
    # or we may have nothing at all!
    #
    # End of the rule's RHS is ';' or EOL.  The ';' may be followed by a
    # recipe.

    logger.debug("tokenize_rule_prereq_or_assign()")

    # save current position in the token stream
    string.push_state()
    rhs = tokenize_rule_RHS(string)

    # Not a prereq. We found ourselves an assignment statement.
    if rhs is None : 
        string.pop_state()

        # We have target-specifc assignment. For example:
        # foo : CC=intel-cc
        # retokenize as an assignment statement
        lhs = tokenize_statement_LHS(string)
        statement = list(lhs)

        assert lhs[-1].string in assignment_operators

        statement.append( tokenize_assign_RHS(string) )
        rhs = AssignmentExpression( statement )
    else : 
        assert isinstance(rhs,PrerequisiteList)

    # stupid human check
    for token in rhs : 
        assert isinstance(token,Symbol),(type(token),token)

    return rhs

#@depth_checker
def tokenize_rule_RHS(string):

    # RHS ::=                       -->  empty perfectly valid
    #     ::= symbols               -->  simple rule's prerequisites
    #     ::= symbols : symbols     -->  implicit pattern rule
    #     ::= symbols | symbols     -->  order only prerequisite
    #     ::= assignment            -->  target specific assignment 
    #
    # RHS terminated by comment, EOL, ';'

    logger.debug("tokenize_rule_RHS()")

    state_start = 1
    state_word = 2
    state_colon = 3
    state_double_colon = 4
    state_dollar = 5
    state_whitespace = 6
    state_backslash = 7

    state = state_start
    token = ""
    prereq_list = []
    token_list = []

    # davep 07-Dec-2014 ;  rule prerequisites are a whitespace separated
    # collection of Expressions. 
    # foo : a$(b)c  <--- one Expression, three terms
    #   vs
    # foo : a $(b) c    <--- three Expressions
    #
    # Collect the tokens (e.g., Literal, VarRef) into token_list[]
    # On whitespace, create Expression(token_list), add to prereq_list
    # At end of prereqs, create PrerequisiteList(prereq_list)

    def save_prereq(token_list):
        if token_list : 
            prereq_list.append( Expression(token_list) )
        return []
    
    for vchar in string :
        c = vchar["char"]
        print("p c={0} state={1} idx={2}".format(printable_char(c),state,string.idx))

        if state==state_start :
            if c==';':
                # End of prerequisites; start of recipe.  Note we don't
                # preserve token because it will be empty at this point.
                # bye!
                # pushback ';' because I need it for the recipe tokenizer.
                string.pushback()
                return PrerequisiteList(prereq_list)
            elif c in whitespace :
                # eat whitespace until we find something interesting
                state = state_whitespace
            else :
                string.pushback()
                state = state_word

        elif state==state_whitespace :
            # eat whitespaces between symbols (a symbol is a prerequisite or a
            # field in an assignment)
            if not c in whitespace : 
                string.pushback()
                state = state_start

        elif state==state_word:
            if c in whitespace :
                # save what we've seen so far
                if token : 
                    token_list.append(Literal(token))
                token_list = save_prereq(token_list)
                # restart the current token
                token = ""
                # start eating whitespace
                state = state_whitespace

            elif c=='\\':
                state = state_backslash

            elif c==':':
                state = state_colon
                # assignment? 
                # implicit pattern rule?

            elif c=='|':
                # We have hit token indicating order-only prerequisite.
                raise TODO()

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if string.lookahead()["char"]=='=':
                    # definitely an assign; bail out and we'll retokenize as assign
                    return None
                else:
                    token += c

            elif c=='=':
                # definitely an assign; bail out and we'll retokenize as assign
                return None

            elif c=='#':
                # eat comment 
                string.pushback()
                comment(string)
                # save the token we've captured
                if token :
                    token_list.append(Literal(token))
                    token_list = save_prereq(token_list)

                # line comment terminates the line (nothing after the comment)
                return PrerequisiteList(prereq_list)

            elif c=='$':
                state = state_dollar

            elif c==';' :
                # recipe tokenizer expects to start with a ';' or a <tab>
                string.pushback()
                # end of prerequisites; start of recipe
                if token : 
                    token_list.append(Literal(token))
                    token_list = save_prereq(token_list)
                # prereqs terminated
                return PrerequisiteList(prereq_list)
            
            elif c in eol :
                # end of prerequisites; start of recipe
                if token : 
                    token_list.append(Literal(token))
                    token_list = save_prereq(token_list)
                return PrerequisiteList(prereq_list)

            else:
                token += c
            
        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token(s) so far but do NOT push to prereq_list (only
                # push to prereq_list on whitespace)
                if token : 
                    token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state = state_word

        elif state==state_colon : 
            if c==':':
                # maybe ::= 
                state = state_double_colon
            elif c=='=':
                # found := so definitely a rule specific  assignment; bail out
                # and we'll retokenize as assignment
                return None
            else:
                # implicit pattern rule
                raise TODO()

        elif state==state_double_colon : 
            # at this point, we found ::
            if c=='=':
                # definitely assign
                # bail out and retokenize as assign
                return None
            else:
                # is this an implicit pattern rule?
                # or a parse error?
                raise TODO()

        elif state==state_backslash : 
            if not c in eol : 
                # literal backslash
                token += '\\'
                state = state_word
            else:
                # The prerequisites (or whatever) are continued on the next
                # line. We treat the EOL as a boundary between symbols
                # davep 07-Dec-2014 ; shouldn't see this anymore (VirtualLine
                # hides the line continuations)
                assert 0
                state = state_start
                
        else : 
            # should not get here
            assert 0, state

    # davep 07-Dec-2014 ; do we ever get here? 
    assert 0, state

    if state==state_word:
        # save the token we've seen so far
        token_list.append(Literal(token.rstrip()))
    elif state in (state_whitespace, state_start) :
        pass
    else:
        # premature end of file?
        raise ParseError()

    return PrerequisiteList(prereq_list)

#@depth_checker
def tokenize_assign_RHS(string):
    logger.debug("tokenize_assign_RHS()")

    state_start = 1
    state_dollar = 2
    state_literal = 3
    state_whitespace = 4

    state = state_start
    token = ""
    token_list = []

    for vchar in string :
        c = vchar["char"]
        print("a c={0} state={1} idx={2}".format(
                printable_char(c),state,string.idx, string.remain()))
        if state==state_start :
            if c in whitespace :
                state = state_whitespace
            else :
                string.pushback()
                state = state_literal

        elif state==state_whitespace :
            if not c in whitespace : 
                string.pushback()
                state = state_literal

        elif state==state_literal:
            if c=='$' :
                state = state_dollar
            elif c=='#':
                # save the token we've seen so far
                string.pushback()
                # eat comment 
                comment(string)
                # stay in same state
            elif c in eol :
                # assignment terminates at end of line
                # end of string
                # save what we've seen so far
                token_list.append(Literal(token))
                return Expression(token_list)
            else:
                token += c

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token so far; note no rstrip()!
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state = state_literal

        else:
            # should not get here
            assert 0, state

    # end of string
    # save what we've seen so far
    token_list.append(Literal(token))
    return Expression(token_list)

#@depth_checker
def tokenize_variable_ref(string):
    # Tokenize a variable reference e.g., $(expression) or $c 
    # Handles nested expressions e.g., $( $(foo) )
    # Returns a VarExp object.

    logger.debug("tokenize_variable_ref()")

    state_start = 1
    state_dollar = 2
    state_in_var_ref = 3

    state = state_start
    token = ""
    token_list = []

    for vchar in string : 
        c = vchar["char"]
#        print("v c={0} state={1} idx={2}".format(printable_char(c),state,string.idx))
        if state==state_start:
            if c=='$':
                state=state_dollar
            else :
                raise ParseError(pos=vchar["pos"])

        elif state==state_dollar:
            # looking for '(' or '$' or some char
            if c=='(' or c=='{':
                opener = c
                state = state_in_var_ref
            elif c=='$':
                # literal "$$"
                token += "$"
            elif not c in whitespace :
                # single letter variable, e.g., $@ $x $_ etc.
                token_list.append( Literal(c) )
                return VarRef(token_list)
                # done tokenizing the var ref

        elif state==state_in_var_ref:
            if c==')' or c=='}':
                # end of var ref
                # TODO make sure to match the open/close chars

                # save what we've read so far
                token_list.append( Literal(token) )

                # do we have a function call?
                try:
                    fn = functions.make_function(token_list)
                except KeyError:
                    # nope, not a function call
                    return VarRef(token_list)
                else:
                    return fn
                # done tokenizing the var ref

            elif c=='$':
                # nested expression!  :-O
                # if lone $$ token, preserve the $$ in the current token string
                # otherwise, recurse into parsing a $() expression
                if string.lookahead()["char"]=='$':
                    token += "$"
                    # skip the extra $
                    c = next(string)
                    state = state_in_var_ref
                else:
                    # save token so far
                    token_list.append( Literal(token) )
                    # restart token
                    token = ""
                    # push the '$' back onto the scanner
                    string.pushback()
                    # recurse into this scanner again
                    token_list.append( tokenize_variable_ref(string) )
            else:
                token += c

        else:
                # should not get here
            assert 0, state

    raise ParseError(pos=vchar["pos"])

#@depth_checker
def tokenize_recipe(string):
    # Collect characters together into a token. 
    # At token boundary, store token as a Literal. Add to token_list. Reset token.
    # A variable ref is a token boundary, and EOL is a token boundary.
    # At recipe boundary, create a Recipe from the token_list. 

    logger.debug("tokenize_recipe()")

    state_start = 1
    state_lhs_white = 2
    state_recipe = 3
    state_space = 4
    state_dollar = 5
    state_backslash = 6
    
    state = state_start
    token = ""
    token_list = []

    sanity_count = 0

    for vchar in string :
        c = vchar["char"]
        print("r c={0} state={1} idx={2} ".format(
                printable_char(c),state,string.idx,token))

        sanity_count += 1
#        assert sanity_count < 50

        if state==state_start : 
            # Must arrive here right after the end of the prerequisite list.
            # Should find either a ; or an EOL
            # example:
            #
            # foo : <eol>
            # <tab>@echo bar
            #
            # foo : ; @echo bar
            #
            if c==';' or c==recipe_prefix :
                state = state_lhs_white
                
        elif state==state_lhs_white :
            # Whitespace after the <tab> (or .RECIPEPREFIX) until the first
            # shell-able command is eaten.
            if not c in whitespace : 
                string.pushback()
                state = state_recipe
            # otherwise eat the whitespace

        elif state==state_recipe :
            if c in eol : 
                # save what we've seen so far
                token_list.append( Literal(token) )
                # bye!
                return Recipe( token_list ) 
            elif c=='$':
                state = state_dollar
            elif c=='\\':
                state = state_backslash
            else:
                token += c

        elif state==state_dollar : 
            if c=='$':
                # literal $
                token += "$"
                state = state_recipe
            else:
                # definitely a variable ref of some sort
                # save token so far; note no rstrip()!
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state=state_recipe

        elif state==state_backslash : 
            # literal \ followed by some char
            token += '\\'
            token += c
            state = state_recipe

        else:
            # should not get here
            assert 0,state

    print("end of string state={0}".format(state))

    # end of string
    # save what we've seen so far
    if state==state_recipe : 
        token_list.append( Literal(token) )
    else:
        # should not get here
        assert 0,(state,string.starting_file_line)

    return Recipe( token_list )

def parse_recipes( line_iter, semicolon_vline=None ) : 

    print("parse_recipes()")
#    print( file_lines.remain() )

    state_start = 1
    state_comment_backslash = 2
    state_recipe_backslash = 3

    state = state_start

    # array of Recipe
    recipe_list = []

    # array of text lines (recipes with \)
    lines_list = []

    if semicolon_vline : 
        # we have something that trails a ; on the rule
        recipe = tokenize_recipe(iter(semicolon_vline))
        print("recipe={0}".format(recipe.makefile()))
        recipe.set_code( semicolon_vline )
        recipe_list.append(recipe)

    # we're working with the raw strings (not VirtualLine) here so need to
    # carefully handle backslashes ourselves

    for line in line_iter : 
        print( "r state={0}".format(state))

        if state==state_start : 
            if line.startswith(recipe_prefix):
                # TODO handle DOS line ending
                if line.endswith('\\\n'):
                    lines_list = [ line ] 
                    state = state_recipe_backslash
                else :
                    # single line
                    recipe_vline = vline.RecipeVirtualLine([line],line_iter.idx)
                    recipe = tokenize_recipe(iter(recipe_vline))
                    print("recipe={0}".format(recipe.makefile()))
                    recipe.set_code(recipe_vline)
                    recipe_list.append(recipe)
            else : 
                line_stripped = line.strip()
                if len(line_stripped)==0:
                    # ignore blank lines
                    pass
                elif line_stripped.startswith("#"):
                    # ignore makefile comments
                    # TODO handle DOS line ending
                    print("recipe comment",line_stripped)
                    if line.endswith('\\\n'):
                        lines_list = [ line ] 
                        state = state_comment_backslash
                else:
                    # found a line that doesn't belong to the recipe;
                    # done with recipe list
                    line_iter.pushback()
                    break

        elif state==state_comment_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # end of the makefile comment (is ignored)
                state = state_start

        elif state==state_recipe_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # now have an array of lines that need to be one line for the
                # recipes tokenizer
                recipe_vline = vline.RecipeVirtualLine(lines_list,line_iter.idx)
                recipe = tokenize_recipe(iter(recipe_vline))
                recipe.set_code(recipe_vline)
                recipe_list.append(recipe)

                # go back and look for more
                state = state_start

        else : 
            # should not get here
            assert 0,state

    print("bottom of parse_recipes()")

    return RecipeList(recipe_list)

def seek_directive(s):
    def get_directive(s):
        # (did I need this function outside seek???)
        # Split apart a line seeking a directive. Handle stuff like:
        #   else   <--- legal (duh)
        #   else#  <--- legal
        #
        fields = s.strip().split()[0].split("#")
        return fields[0]
    # split apart a line seeking a directive
    d = get_directive(s)
    if d in directive:
        return d
    return None

def seek_elseif(virt_line):
    # Look for an "else if" directive (e.g., else ifdef, else ifeq, etc)
    #
    # Luckily Make seems to require whitespace after the else conditional
    #   else ifeq(  <--- fail
    #   else ifeq#  <--- incorrect syntax
    #   else ifeq ( <--- ok
    #
    # Returns the physical string and virtual line with the "else" removed
    # else ifdef FOO    -> ifdef FOO
    # else ifeq ($a,$b) -> ifeq ($a,$b)
    # The returning value will be passed to the tokenizer recursively.

    VirtualLine.validate([virt_line])

    # "When in doubt, use brute force."
    phys_line = str(virt_line)
    phys_line = phys_line.lstrip()
    assert phys_line.startswith("else"),phys_line
    phys_line = phys_line[4:].lstrip()
    if not phys_line or phys_line[0]=='#' :
        # rest of line is empty or a comment
        return None

    d = seek_directive(phys_line)
    if d in conditional_directive :
        print("found elseif condition=\"{0}\"".format(d))
        return d,VirtualLine.from_string(phys_line)

    # found junk after else
    # .e.g, 
    #   else export iamnotlegal
    #   else $(info I am not legal)
    # (TODO need a better error message)
    errmsg = "Extra stuff after else"
    raise ParseError(vline=virt_line,pos=virt_line.starting_pos(),
                description=errmsg)

#@depth_checker
def handle_conditional_directive(directive_inst,vline_iter,line_iter):
    # GNU make doesn't parse the stuff inside the conditional unless the
    # conditional expression evaluates to True. But Make does allow nested
    # conditionals. Read line by line, looking for nested conditional
    # directives
    #
    # directive_inst - an instance of DirectiveExpression
    # vline_iter - <generator>across VirtualLine instances (does NOT support
    #               pushback)
    # line_iter - ScannerIterator instance of physical lines from the file
    #               (does support pushback)
    #
    # vline_iter is from get_vline() and reads from line_iter underneath. The
    # line_iter and vline_iter will operate in lockstep.
    #
    # It's very confusing. But need to pass around both the iterators because
    # the backslash rules change depending on where we are. And the contents of
    # the conditional directives aren't parsed unless the condition is true.

    # call should have sent us a Directive instance (stupid human check)
    assert isinstance(directive_inst,ConditionalDirective), type(directive_inst)

    print( "handle_conditional_directive() \"{0}\" line={1}".format(
        directive_inst.name,line_iter.idx-1))

    state_if = 1
    state_else = 3
    state_endif = 4

    state = state_if

    # gather file lines; will be VirtualLine instances
    # Passed to LineBlock constructor.
    line_list = []

    cond_block = ConditionalBlock()
    cond_block.add_conditional( directive_inst )

    def save_block(line_list):
        if len(line_list) :
            cond_block.add_block( LineBlock(line_list) )
        return []

    # save where this directive block begins so we can report errors about big
    # if/else/endif problems (such as missing endif)
    starting_pos = directive_inst.code.starting_pos()

    for virt_line in vline_iter : 
        print("c state={0}".format(state))
#        print("={0}".format(str(virt_line)),end="")

        # search for nested directive in the physical line (consolidates the
        # line continuations)
        phys_line = str(virt_line)

        # directive is the first substring surrounded by whitespace
        # or None if substring is not a directive
        directive_str = seek_directive(phys_line)

        if directive_str in conditional_directive : 
            # save the block of stuff we've read
            line_list = save_block(line_list)

            # recursive function is recursive
            sub_block = tokenize_directive(directive_str,virt_line,vline_iter,line_iter)
            cond_block.add_block( sub_block )
            
        elif directive_str=="else" : 
            if state==state_else : 
                errmsg = "too many else"
                raise ParseError(vline=virt_line,pos=virt_line.starting_pos(),
                            description=errmsg)

            # save the block of stuff we've read
            line_list = save_block(line_list)

            print("phys_line={0}".format(printable_string(phys_line)))

            # handle "else if"
            elseif = seek_elseif(virt_line)
            if elseif : 
                # found an "else if"something
                directive_str, virt_line = elseif

                lut = { "ifdef" : IfdefDirective,
                        "ifndef" : IfndefDirective,
                        "ifeq"  : IfeqDirective,
                        "ifneq" : IfneqDirective 
                      }
                viter = iter(virt_line)
                viter.lstrip().eat(directive_str).lstrip()
                expression = tokenize_assign_RHS(viter)
                directive_inst = lut[directive_str](expression)
                cond_block.add_conditional( directive_inst )
            else : 
                # Just the else case. Must be the last conditional we see.
                cond_block.start_else()
                state = state_else 

        elif directive_str=="endif":
            # save the block of stuff we've read
            line_list = save_block(line_list)
            state = state_endif

        else : 
            # save the line into the block
            print("save \"{0}\"".format(printable_string(str(virt_line))))
            line_list.append(virt_line)

        if state==state_endif : 
            # close the if/else/endif collection
            break

    # did we hit bottom of file before finding our end?
    if state != state_endif :
        errmsg = "missing endif"
        raise ParseError(pos=starting_pos, description=errmsg)
    
    return cond_block

def tokenize_define_directive(string):
    # multi-line macro

    logger.debug("tokenize_define_directive()")

    state_start = 1
    state_name = 2
    state_seeking_eol = 3

    state = state_start
    macro_name = ""

    # 3.81 treats the = as part of the name
    # 3.82 and beyond introduced the "=" after the macro name
    if not(Version.major==3 and Version.minor==81) : 
        raise TODO()

    # get the starting position of this string (for error reporting)
    starting_pos = string.lookahead()["pos"]
    print("starting_pos=",starting_pos)

    for vchar in string : 
        c = vchar["char"]
        print("m c={0} state={1} idx={2} ".format( 
                printable_char(c),state,string.idx))

        if state==state_start:
            # always eat whitespace while in the starting state
            if c in whitespace : 
                # eat whitespace
                pass
            else:
                string.pushback()
                state = state_name

        elif state==state_name : 
            # save the name until EOL (we'll strip off the trailing RHS
            # whitespace later)
            #
            # TODO if Version > 3.81 then add support for "="
            macro_name += c

    return macro_name.rstrip()

def handle_define_directive(define_inst,vline_iter,line_iter):

    # array of VirtualLine
    line_list = []

    # save where this define block begins so we can report errors about 
    # missing enddef 
    starting_pos = define_inst.code.starting_pos()

    for virt_line in vline_iter : 

        # seach for enddef in physical line
        phys_line = str(virt_line).lstrip()
        if phys_line.startswith("endef"):
            phys_line = phys_line[5:].lstrip()
            if not phys_line or phys_line[0]=='#':
                break
            errmsg = "extraneous text after 'enddef' directive"
            raise ParseError(vline=virt_line,pos=virt_line.starting_pos(),
                        description=errmsg)

        line_list.append(virt_line)
    else :
        errmsg = "missing enddef"
        raise ParseError(pos=starting_pos, description=errmsg)

    define_inst.set_block(LineBlock(line_list))
    return define_inst

#@depth_checker
def tokenize_directive(directive_str,virt_line,vline_iter,line_iter):
    logger.debug("tokenize_directive() \"%s\" at line=%d",
            directive_str,virt_line.starting_file_line)

    # TODO probably need a lot of parse checking here eventually
    # (Most parse checking is in the Directive constructor)
    #
    # 'private' is weird. Only applies to implicit pattern rules? 
    #
    # if* conditional will require very careful handling. The content of the
    # conditional branches aren't parsed until the conditional is evaluated.
    #
    # export/unexport/override all apply to define blocks as well. So if find
    # an {export,unexport,override} need to check for a define block before
    # passing to tokenizer.
    #

    directive_lut = { 
        "export" : { "constructor" : ExportDirective,
                     "tokenizer"   : tokenize_statement,
                   },
        "unexport" : { "constructor" : UnExportDirective,
                       "tokenizer"   : tokenize_statement,
                     },

        "include" : { "constructor" : IncludeDirective,
                       "tokenizer"   : tokenize_assign_RHS,
                     },
        "-include" : { "constructor" : SIncludeDirective,
                       "tokenizer"   : tokenize_assign_RHS,
                     },
        "sinclude" : { "constructor" : SIncludeDirective,
                       "tokenizer"   : tokenize_assign_RHS,
                     },

        "vpath" : { "constructor" : VpathDirective,
                    "tokenizer" : tokenize_assign_RHS,
                  },

        "override" : { "constructor" : OverrideDirective,
                       "tokenizer" : tokenize_statement,
                     },

        "ifdef" : { "constructor" : IfdefDirective,
                    "tokenizer"   : tokenize_assign_RHS,
                  },
        "ifndef" : { "constructor" : IfndefDirective,
                     "tokenizer"   : tokenize_assign_RHS,
                   },

        "ifeq" : { "constructor" : IfeqDirective,
                    "tokenizer"   : tokenize_assign_RHS,
                 },
        "ifneq" : { "constructor" : IfneqDirective,
                     "tokenizer"   : tokenize_assign_RHS,
                  },

        "define" : { "constructor" : DefineDirective,
                     "tokenizer" : tokenize_define_directive,
                   },  

        # TODO add rest of opening directives
    }

    if directive_str=="else" or directive_str=="endif" :
        errmsg = "extraneous " + directive_str
        raise ParseError(vline=virt_line,pos=virt_line.starting_pos(),
                    description=errmsg)

    d = directive_lut[directive_str]
    
    # ScannerIterator across characters in the virtual line (supports pushback)
    viter = iter(virt_line)

    # eat any leading whitespace, eat the directive, eat any more whitespace
    # we'll get StopIteration if we eat everything (directive with no
    # expression such as lone "export" or "vpath")
    try : 
        viter.lstrip().eat(directive_str).lstrip()
    except StopIteration:
        # No expression with this directive. For example, lone "export" which
        # means all variables exported by default
        expression = None
    else:
        # now feed to the chosen tokenizer
        expression = d["tokenizer"](viter)

    print("{0} expression={1}".format(directive_str,expression))

    # construct a Directive instance
    try : 
        directive_instance = d["constructor"](expression)
    except ParseError as err:
        err.vline = virt_line
        err.pos = virt_line.starting_pos()
        raise err

    directive_instance.set_code(virt_line)

    # gather the contents of the conditional block (raw lines
    # and maybe nested conditions)
    if directive_str in conditional_directive :
        return handle_conditional_directive(directive_instance,vline_iter,line_iter)

    if directive_str == "define": 
        return handle_define_directive(directive_instance,vline_iter,line_iter)

    return directive_instance

#@depth_checker
def tokenize(virt_line,vline_iter,line_iter): 
    # pull apart a single line into token/symbol(s)
    #
    # virt_line - the current line we need to tokenize (a VirtualLine)
    #
    # vline_iter - <generator> across the entire file (returns VirtualLine instances) 
    #
    # line_iter - ScannerIterator across the file lines (supports pushback)
    #               Need this because we need the raw file lines to support the
    #               different backslash usage in recipes.
    #

    logger.debug("tokenize()")

    # Is this a directive statement (e.g., ifdef ifeq define)?  Read the full
    # concatenated line from virtual line looking for first whitespace
    # surrounded string being a directive. (the vline will clean up the
    # backslash line continuations)
    directive_str = seek_directive(str(virt_line))
    if directive_str:
        token = tokenize_directive(directive_str,virt_line,vline_iter,line_iter)
        return token

    # tokenize character by character across a VirtualLine
    string_iter = iter(virt_line)
    token = tokenize_statement(string_iter)

    # If we found a rule, we need to change how we're handling the
    # lines. (Recipes have different whitespace and backslash rules.)
    if isinstance(token,RuleExpression) : 
        # rule line can contain a recipe following a ; 
        # for example:
        # foo : bar ; @echo baz
        #
        # The rule parser should stop at the semicolon. Will leave the
        # semicolon as the first char of iterator
        # 
        print("rule={0}".format(str(token)))

        # truncate the virtual line that precedes the recipe (cut off
        # at a ";" that might be lurking)
        #
        # foo : bar ; @echo baz
        #          ^--- truncate here
        #
        # I have to parse the full like as a rule to know where the
        # rule ends and the recipe(s) begin. The backslash makes me
        # crazy.
        #
        # foo : bar ; @echo baz\
        # I am more recipe hur hur hur
        #
        # The recipe is "@echo baz\\\nI am more recipe hur hur hur\n"
        # and that's what needs to exec'd.
        remaining_vchars = string_iter.remain()
        if len(remaining_vchars)>0:
            # truncate at position of first char of whatever is
            # leftover from the rule
            truncate_pos = remaining_vchars[0]["pos"]

            recipe_str_list = virt_line.truncate(truncate_pos)

            # make a new virtual line from the semicolon trailing
            # recipe (using a virtual line because backslashes)
            dangling_recipe_vline = vline.RecipeVirtualLine(recipe_str_list,truncate_pos[vline.VCHAR_ROW])
            print("dangling={0}".format(dangling_recipe_vline))
            print("dangling={0}".format(dangling_recipe_vline.virt_lines))
            print("dangling={0}".format(dangling_recipe_vline.phys_lines))

            recipe_list = parse_recipes( line_iter, dangling_recipe_vline )
        else :
            recipe_list = parse_recipes( line_iter )

        assert isinstance(recipe_list,RecipeList)

        print("recipe_list={0}".format(str(recipe_list)))

        # attach the recipe(s) to the rule
        token.add_recipe_list(recipe_list)

    token.set_code(virt_line)

    return token

def xxx_get_vline(line_iter): 
    # GENERATOR
    #
    # line_iter is an iterator that supports pushback
    # iterates across an array of strings, the makefile
    #
    # The line_iter can also be passed around to other tokenizers (e.g., the
    # recipe tokenizer). So this function cannot assume it's the only line_iter
    # user.
    #
    # Each string should be terminated by an EOL.  Handle cases where line is
    # continued after the EOL by a \+EOL (backslash).

    state_start = 1
    state_backslash = 2
    state_tokenize = 3
    
    state = state_start 

    # can't use enumerate() because the line_iter will also be used inside
    # parse_recipes(). 
    for line in line_iter :
        # line_iter.idx is the *next* line number counting from zero 
        line_number = line_iter.idx-1
#        print("line_num={0} state={1}".format(line_number,state))
#        print("{0}".format(hexdump.dump(line),end=""))

        if state==state_start : 
            start_line_stripped = line.strip()

            # ignore blank lines
            if len(start_line_stripped)==0:
                continue

            line_list = [ line ] 

            starting_line_number = line_number
            if vline.is_line_continuation(line):
                # We found a line with trailing \+eol
                # We will start collecting the next lines until we see a line
                # that doesn't end with \+eol
                state = state_backslash
            else :
                # We found a single line of makefile. Tokenize!
                state = state_tokenize

        elif state==state_backslash : 
            line_list.append( line )
            if not vline.is_line_continuation(line):
                # This is the last line of our continuation block. Create a
                # virtual block for this array of lines.
                state = state_tokenize

        else:
            # should not get here
            assert 0, state

        if state==state_tokenize: 
            # is this a line comment?
            if start_line_stripped.startswith("#") :
                # ignore
                state = state_start
                continue

            # make a virtual line (joins together backslashed lines into one
            # line visible through an iterator)
            virt_line = VirtualLine(line_list, starting_line_number)
            del line_list # detach the ref (VirtualLine keeps the array)

            # caller can also use line_iter
            yield virt_line

            # back around the horn
            state = state_start

    return None

def parse_makefile_from_src(src):
    # file_lines is an array of Python strings.
    # The newlines must be preserved.

    logger.debug("parse from src=%s", src.name)

    # trigger getting an array of python strings from the source
    src.load()

    # ScannerIterator across the file_lines array (to support pushback of an
    # entire line). 
    line_iter = ScannerIterator(src.file_lines)

    # get_vline() returns a Python <generator> that walks across makefile
    # lines, joining backslashed lines into VirtualLine instances.
    vline_iter = vline.get_vline(line_iter)

    # The vline_iter will read from line_iter. But line_iter should be at the
    # proper place at all times. In other words, there are two readers from
    # line_iter: this function and tokenize_vline()
    # Recipes need to read from line_iter (different backslash rules).
    # Rest of tokenizer reads from vline_iter.
    token_list = [tokenize(vline, vline_iter, line_iter) for vline in vline_iter] 

    return Makefile(token_list)

#def parse_makefile_string(s):
#    import io
#    with io.StringIO(s) as infile:
#        file_lines = infile.readlines()
#    try : 
#        return parse_makefile_from_strlist(file_lines)
#    except ParseError as err:
#        err.filename = "<string id={0}>".format(id(s)) 
#        print(err,file=sys.stderr)
#        raise

def parse_makefile(infilename) : 

    src = source.SourceFile(infilename)

    try : 
        return parse_makefile_from_src(src)
#        return parse_makefile_from_strlist(file_lines)
    except ParseError as err:
        err.filename = infilename
        print(err,file=sys.stderr)
        raise

def round_trip(makefile):
    dumpmakefile="""
print("# start makefile")
print("\\n".join( [ "{0}".format(m.makefile()) for m in makefile ] ) )
print("# end makefile")
"""

    with open("out.py","w") as outfile:
        print("#!/usr/bin/env python3",file=outfile)
        print("from pymake import *",file=outfile)
        print("from vline import VirtualLine",file=outfile)
        print("makefile="+str(makefile),file=outfile)
#        print("makefile=",",\\\n".join( [ "{0}".format(block) for block in makefile ] ),file=outfile )
#        print("print(\"{0}\".format(makefile))",file=outfile)
        print(dumpmakefile,file=outfile)
        

def execute(makefile):
    # tinkering with how to evaluate
    logger.info("Starting execute of %s", id(makefile))
    from symtable import SymbolTable
    symtable = SymbolTable()
    for sym in makefile.token_list:
        s = sym.eval(symtable)
        logger.debug("s=%s", s)

def usage():
    # TODO
    print("usage: TODO")

if __name__=='__main__':
#    logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2 : 
        usage()
        sys.exit(1)

    infilename = sys.argv[1]
    try : 
        makefile = parse_makefile(infilename)
    except ParseError:
        sys.exit(1)

    # the following is just test code to printf the results. 
#    print("makefile=",",\\\n".join( [ "{0}".format(block) for block in makefile ] ) )
    print("makefile={0}".format(makefile))

#    print("# start makefile")
#    print(makefile.makefile())
#    print("# end makefile")

    execute(makefile)
