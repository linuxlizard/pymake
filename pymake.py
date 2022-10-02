#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

import sys
import logging
import argparse

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
from whitespace import whitespace

#whitespace = set( ' \t\r\n' )
#whitespace = set(' \t')

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

def comment(vchar_scanner):
    state_start = 1
    state_eat_comment = 2

    state = state_start

    # this could definitely be faster (method in ScannerIterator to eat until EOL?)
    for vchar in vchar_scanner : 
        c = vchar.char
#        print("# c={0} state={1}".format(printable_char(c), state))
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
def tokenize_statement(vchar_scanner):
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
    starting_pos = vchar_scanner.lookahead().pos

    logger.debug("tokenize_statement() pos=%s", starting_pos)

    # save current position in the token stream
    vchar_scanner.push_state()
    lhs = tokenize_statement_LHS(vchar_scanner)
    
    # should get back a list of stuff in the Symbol class hierarchy
    assert len(lhs)>=0, type(lhs)
    for symbol in lhs : 
        assert isinstance(symbol,Symbol),(type(symbol), symbol)
        logger.debug("symbol=%s", symbol)

    # decode what kind of statement do we have based on where
    # tokenize_statement_LHS() stopped.
    last_symbol = lhs[-1]

    logger.debug("last_symbol=%s", last_symbol)

    if isinstance(last_symbol,RuleOp): 
        statement_type = "rule"

#        print( u"last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
#        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        logger.debug( "last_token=%s ∴ statement is %s so re-run as rule", last_symbol, statement_type)

        # jump back to starting position
        vchar_scanner.pop_state()
        # re-tokenize as a rule (backtrack)
        lhs = tokenize_statement_LHS(vchar_scanner, whitespace)
    
        # add rule RHS
        # rule RHS  ::= assignment
        #           ::= prerequisite_list
        #           ::= <empty>
        statement = list(lhs)
        statement.append( tokenize_rule_prereq_or_assign(vchar_scanner) )

        # don't look for recipe(s) yet
        return RuleExpression( statement ) 

    elif isinstance(last_symbol,AssignOp): 
        statement_type = "assignment"

#        print( u"last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
#        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
        logger.debug( "last_token=%s ∴ statement is %s", last_symbol, statement_type)

        # The statement is an assignment. Tokenize rest of line as an assignment.
        statement = list(lhs)
        statement.append(tokenize_assign_RHS(vchar_scanner))
        return AssignmentExpression(statement)

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
        assert len(vchar_scanner.remain())==0, (len(vchar_scanner.remain(), starting_pos))
        
        # Should be one big Expression. We'll dig into the Expression during
        # the 2nd pass.
        assert len(lhs)==1,(len(lhs), str(lhs), starting_pos)

        return lhs[0]

    else:
        statement_type="????"
#        print( "last_token={0} \u2234 statement is {1}".format(last_symbol,statement_type).encode("utf-8"))
#        print( "last_token={0} ∴ statement is {1}".format(last_symbol, statement_type))

        # should not get here
        assert 0, last_symbol

#@depth_checker
def tokenize_statement_LHS(vchar_scanner, separators=""):
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
    # array of vchar
    token = vline.VCharString()

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

    # get the starting position of this scanner (for error reporting)
    starting_pos = vchar_scanner.lookahead().pos
    logger.debug("LHS starting_pos=%s", starting_pos)

    for vchar in vchar_scanner : 
        assert vchar.filename 
        c = vchar.char
        logger.debug("s c={} state={} idx={} token=\"{}\" pos={} src={}".format(
            printable_char(c), state, vchar_scanner.idx, str(token), vchar.pos, vchar.filename))
#        print("s c={} state={} idx={} token=\"{}\" pos={} src={}".format(
#            printable_char(c), state, vchar_scanner.idx, str(token), vchar.pos, vchar.filename))

        if state==state_start:
            # always eat whitespace while in the starting state
            if c in whitespace : 
                # eat whitespace
                pass
            elif c==':':
                state = state_colon
                token += vchar
            else :
                # whatever it is, push it back so can tokenize it
                vchar_scanner.pushback()
                state = state_in_word

        elif state==state_in_word:
            if c=='\\':
                state = state_backslash
                token += vchar

            # whitespace in LHS of assignment is significant
            # whitespace in LHS of rule is ignored
            elif c in separators :
                # end of word
                if len(token):
                    token_list.append(Literal(token))

                # start new token
                token = vline.VCharString()

                # jump back to start searching for next symbol
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # capture anything we might have seen 
                if len(token) : 
                    token_list.append(Literal(token))
                # eat the comment 
                vchar_scanner.pushback()
                comment(vchar_scanner)

            elif c==':':
                # end of LHS (don't know if rule or assignment yet)
                # strip trailing whitespace
                token_cleaned = token.rstrip()
                if len(token_cleaned):
                    token_list.append( Literal(token_cleaned) )
                # start new token
                token = vline.VCharString()
                token += vchar
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if vchar_scanner.lookahead().char == '=':
                    eq = vchar_scanner.next()
                    assign = AssignOp(vline.VCharString([vchar, eq]))
                    token_list.append(Literal(token.rstrip()))
                    return Expression(token_list), assign
                else:
                    token += vchar

            elif c=='=':
                # definitely an assignment 
                # strip trailing whitespace
                t = token.rstrip()
                if len(t):
                    token_list.append(Literal(t))
                return Expression(token_list), AssignOp(vline.VCharString([vchar]))

            elif c in eol : 
                # end of line; bail out
                if len(token) : 
                    # capture any leftover when the line ended
                    token_list.append(Literal(token))
                break
                
            else :
                assert isinstance(token, vline.VCharString), type(token)
                assert isinstance(vchar, vline.VChar), type(vchar)
                token += vchar

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += vchar 
            else:
                # save token so far (if any); note no rstrip()!
                if len(token):
                    token_list.append(Literal(token))
                # start new token
                token = vline.VCharString()

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )

            state=state_in_word

        elif state==state_backslash :
            if c in eol : 
                # line continuation
                # davep 04-Oct-2014 ; XXX   should not see anymore
#                print("vchar_scanner={0} data={1}".format(type(vchar_scanner), type(vchar_scanner.data)))
#                print(vchar_scanner.data)
                assert 0, (vchar_scanner, vchar)
            else :
                # literal '\' + somechar
                token += vchar
            state = state_in_word

        elif state==state_colon :
            # assignment end of LHS is := or ::= 
            # rule's end of target(s) is either a single ':' or double colon '::'
            if c==':':
                # double colon
                state = state_colon_colon
                token += vchar
            elif c=='=':
                # :=
                # end of RHS
                token += vchar
                return Expression(token_list), AssignOp(token) 
            else:
                # Single ':' followed by something. Whatever it was, put it back!
                vchar_scanner.pushback()
                # successfully found LHS 
                return Expression(token_list), RuleOp(token)

        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                return Expression(token_list), AssignOp("::=") 
            vchar_scanner.pushback()
            # successfully found LHS 
            return Expression(token_list), RuleOp("::") 

        else:
            # should not get here
            assert 0, state

    # hit end of scanner; what was our final state?
    if state==state_colon:
        # Found a Rule
        # ":"
        assert len(token_list), starting_pos
        return Expression(token_list), RuleOp(":") 

    if state==state_colon_colon:
        # Found a Rule
        # "::"
        assert len(token_list), starting_pos
        return Expression(token_list), RuleOp("::") 

    if state==state_in_word :
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
    assert 0, (state, starting_pos)

#@depth_checker
def tokenize_rule_prereq_or_assign(vchar_scanner):
    # We are on the RHS of a rule's : or ::
    # We may have a set of prerequisites
    # or we may have a target specific assignment.
    # or we may have nothing at all!
    #
    # End of the rule's RHS is ';' or EOL.  The ';' may be followed by a
    # recipe.

    logger.debug("tokenize_rule_prereq_or_assign()")

    # save current position in the token stream
    vchar_scanner.push_state()
    rhs = tokenize_rule_RHS(vchar_scanner)

    # Not a prereq. We found ourselves an assignment statement.
    if rhs is None : 
        vchar_scanner.pop_state()

        # We have target-specifc assignment. For example:
        # foo : CC=intel-cc
        # retokenize as an assignment statement
        lhs = tokenize_statement_LHS(vchar_scanner)
        statement = list(lhs)

        # verify the operator parsed correctly 
        assert str(lhs[-1].string) in assignment_operators

        statement.append( tokenize_assign_RHS(vchar_scanner) )
        rhs = AssignmentExpression( statement )
    else : 
        assert isinstance(rhs,PrerequisiteList)

    # stupid human check
    for token in rhs : 
        assert isinstance(token,Symbol),(type(token), token)

    return rhs

#@depth_checker
def tokenize_rule_RHS(vchar_scanner):

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
    token = vline.VCharString()
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
    
    for vchar in vchar_scanner :
        c = vchar.char
        logger.debug("p state={1} c={0} pos={2}".format(printable_char(c), state, vchar.pos))

        if state==state_start :
            if c==';':
                # End of prerequisites; start of recipe.  Note we don't
                # preserve token because it will be empty at this point.
                # bye!
                # pushback ';' because I need it for the recipe tokenizer.
                vchar_scanner.pushback()
                return PrerequisiteList(prereq_list)
            elif c in whitespace :
                # eat whitespace until we find something interesting
                state = state_whitespace
            else :
                vchar_scanner.pushback()
                state = state_word

        elif state==state_whitespace :
            # eat whitespaces between symbols (a symbol is a prerequisite or a
            # field in an assignment)
            if not c in whitespace : 
                vchar_scanner.pushback()
                state = state_start

        elif state==state_word:
            if c in whitespace :
                # save what we've seen so far
                if token : 
                    token_list.append(Literal(token))
                token_list = save_prereq(token_list)
                # restart the current token
                token = vline.VCharString()
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
                raise NotImplementedError

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if vchar_scanner.lookahead().char=='=':
                    # definitely an assign; bail out and we'll retokenize as assign
                    return None
                else:
                    token += vchar 

            elif c=='=':
                # definitely an assign; bail out and we'll retokenize as assign
                return None

            elif c=='#':
                # eat comment 
                vchar_scanner.pushback()
                comment(vchar_scanner)
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
                vchar_scanner.pushback()
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
                token += vchar
            
        elif state==state_dollar :
            if c=='$':
                # literal $
                token += vchar
            else:
                # save token(s) so far but do NOT push to prereq_list (only
                # push to prereq_list on whitespace)
                if token : 
                    token_list.append(Literal(token))
                # restart token
                token = vline.VCharString()

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )
#                print("token_list=",token_list)
#                print("token_list=", " ".join([t.makefile() for t in token_list]))

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
                raise NotImplementedError()

        elif state==state_double_colon : 
            # at this point, we found ::
            if c=='=':
                # definitely assign
                # bail out and retokenize as assign
                return None
            else:
                # is this an implicit pattern rule?
                # or a parse error?
                raise NotImplementedError()

        elif state==state_backslash : 
            if not c in eol : 
                # literal backslash + some char
                token += vchar_scanner.peek_back() # capture the literal backslash
                token += vchar
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
def tokenize_assign_RHS(vchar_scanner):
    logger.debug("tokenize_assign_RHS()")

    state_start = 1
    state_dollar = 2
    state_literal = 3
    state_whitespace = 4

    state = state_start
    token = vline.VCharString()
    token_list = []

    for vchar in vchar_scanner :
        c = vchar.char
        logger.debug("a c={0} state={1} idx={2}".format(printable_char(c), state, vchar_scanner.idx, vchar_scanner.remain()))
        if state==state_start :
            if c in whitespace :
                state = state_whitespace
            else :
                vchar_scanner.pushback()
                state = state_literal

        elif state==state_whitespace :
            if not c in whitespace : 
                vchar_scanner.pushback()
                state = state_literal

        elif state==state_literal:
            if c=='$' :
                state = state_dollar
            elif c=='#':
                # save the token we've seen so far
                vchar_scanner.pushback()
                # eat comment 
                comment(vchar_scanner)
                # stay in same state
            elif c in eol :
                # assignment terminates at end of line
                # end of scanner
                # save what we've seen so far
                if len(token):
                    token_list.append(Literal(token))
                return Expression(token_list)
            else:
                token += vchar

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += vchar
            else:
                # save token so far; note no rstrip()!
                if len(token):
                    token_list.append(Literal(token))
                # restart token
                token = vline.VCharString()

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )

            state = state_literal

        else:
            # should not get here
            assert 0, state

    # end of scanner
    # save what we've seen so far (if any)
    if len(token):
        token_list.append(Literal(token))
    return Expression(token_list)

#@depth_checker
def tokenize_variable_ref(vchar_scanner):
    # Tokenize a variable reference e.g., $(expression) or $c 
    # Handles nested expressions e.g., $( $(foo) )
    # Returns a VarExp object.

    logger.debug("tokenize_variable_ref()")

    state_start = 1
    state_dollar = 2
    state_in_var_ref = 3

    # open char .e.g. ( or {
    # (so we can match open/close chars)
    open_char = None

    state = state_start
    token = vline.VCharString()
    token_list = []

    # TODO optimization opportunity.  Move state==state_start outside the loop
    # since we're only hitting it once
    for vchar in vchar_scanner : 
        c = vchar.char
#        print("v c={0} state={1} idx={2}".format(printable_char(c), state, vchar_scanner.idx))
        if state==state_start:
            if c=='$':
                state=state_dollar
            else :
                raise ParseError(pos=vchar.pos)

        elif state==state_dollar:
            # looking for '(' or '$' or some char
            if c=='(' or c=='{':
                open_char = c
                state = state_in_var_ref
            elif c=='$':
                # literal "$$"
                token += vchar
            elif not c in whitespace :
                # single letter variable, e.g., $@ $x $_ etc.
                token += vchar
                token_list.append(Literal(token))
                return VarRef(token_list)
                # done tokenizing the var ref
            else:
                # Can I hit a case of $<whitespace> ?
                # Yes. GNU Make 4.3 is ignoring it.
                breakpoint()
                assert 0, "TODO"
                return VarRef([])

        elif state==state_in_var_ref:
            if c==')' or c=='}':
                # end of var ref
                # TODO make sure to match the open/close chars
                # () {} good
                # (} {) bad 

                # save what we've read so far
                if len(token):
                    token_list.append( Literal(token) )

                # do we have a function call?
                try:
                    return functions.make_function(token_list)
                except KeyError:
                    # nope, not a function call
                    return VarRef(token_list)
                # done tokenizing the var ref

            elif c=='$':
                # nested expression!  :-O
                # if lone $$ token, preserve the $$ in the current token scanner
                # otherwise, recurse into parsing a $() expression
                if vchar_scanner.lookahead().char=='$':
                    token += vchar
                    # skip the extra $
                    c = next(vchar_scanner)
                else:
                    # save token so far (if any)
                    if len(token):
                        token_list.append( Literal(token) )
                    # restart token
                    token = vline.VCharString()
                    # push the '$' back onto the scanner
                    vchar_scanner.pushback()
                    # recurse into this scanner again
                    token_list.append( tokenize_variable_ref(vchar_scanner) )
            else:
                token += vchar

        else:
                # should not get here
            assert 0, state

    raise ParseError(pos=vchar.pos, description="VarRef not closed")

#@depth_checker
def tokenize_recipe(vchar_scanner):
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
    token = vline.VCharString()
    token_list = []
    vchar_stack = []

    sanity_count = 0

    for vchar in vchar_scanner :
        c = vchar.char
        logger.debug("r c={} state={} idx={} token=\"{}\" pos={}".format(
            printable_char(c), state, vchar_scanner.idx, printable_string(str(token)), vchar.pos))

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
                vchar_scanner.pushback()
                state = state_recipe
            # otherwise eat the whitespace

        elif state==state_recipe :
            if c in eol : 
                # save what we've seen so far
                if len(token):
                    token_list.append(Literal(token))
                # bye!
                return Recipe(token_list) 
            elif c=='$':
                state = state_dollar
            elif c=='\\':
                vchar_stack.append(vchar)
                state = state_backslash
            else:
                token += vchar 

        elif state==state_dollar : 
            if c=='$':
                # a $$ in a rule expression needs to be preserved as a double $$
                token += vchar_scanner.peek_back() # capture the previous '$'
                token += vchar
                state = state_recipe
            else:
                # definitely a variable ref of some sort
                # save token so far; note no rstrip()!
                if len(token):
                    token_list.append(Literal(token))
                # restart token
                token = vline.VCharString()

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append(tokenize_variable_ref(vchar_scanner))

            state=state_recipe

        elif state==state_backslash : 
            # literal \ followed by some char
            token += vchar_stack.pop()
            token += vchar
            state = state_recipe

        else:
            # should not get here
            assert 0, state

    logger.debug("end of scanner state=%d", state)

    # end of scanner
    # save what we've seen so far
    if state==state_recipe : 
        token_list.append(Literal(token))
    else:
        # should not get here
        assert 0,(state, vchar_scanner.starting_file_line)

    return Recipe( token_list )

def parse_recipes(line_scanner, semicolon_vline=None): 
    logger.debug("parse_recipes()")

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
        recipe.save(semicolon_vline)
        recipe_list.append(recipe)

    # we're working with the raw strings (not VirtualLine) here so need to
    # carefully handle backslashes ourselves

    # start iterating over the array of strings in the line_scanner
  
    # sometimes need to maintain a previous position across states
    starting_row = []

    for line in line_scanner : 
        logger.debug( "r state={0}".format(state))

        # file line of 'line'
        row = line_scanner.idx - 1

        if state==state_start : 
            if line.startswith(recipe_prefix):
                # TODO handle DOS line ending
                if line.endswith('\\\n'):
                    starting_row.append(row)
                    lines_list = [ line ] 
                    state = state_recipe_backslash
                else :
                    # single line
                    recipe_vline = vline.RecipeVirtualLine([line], (row,0), line_scanner.filename)
                    recipe = tokenize_recipe(iter(recipe_vline))
                    logger.debug("recipe=%s", recipe.makefile())
                    recipe.save(recipe_vline)
                    recipe_list.append(recipe)
            else : 
                line_stripped = line.strip()
                if len(line_stripped)==0:
                    # ignore blank lines
                    pass
                elif line_stripped.startswith("#"):
                    # ignore makefile comments
                    # TODO handle DOS line ending
                    logger.debug("recipe comment %s", line_stripped)
                    if line.endswith('\\\n'):
                        lines_list = [ line ] 
                        state = state_comment_backslash
                else:
                    # found a line that doesn't belong to the recipe;
                    # done with recipe list
                    line_scanner.pushback()
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
                recipe_vline = vline.RecipeVirtualLine(lines_list, (starting_row.pop(),0), line_scanner.filename)
                recipe = tokenize_recipe(iter(recipe_vline))
                recipe.save(recipe_vline)
                recipe_list.append(recipe)

                # go back and look for more
                state = state_start

        else : 
            # should not get here
            assert 0, state

    logger.debug("bottom of parse_recipes()")

    return RecipeList(recipe_list)

def seek_directive(s):
    # s - raw python string
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

    VirtualLine.validate(virt_line)

    # "When in doubt, use brute force."
    phys_line = str(virt_line)
    phys_line = phys_line.lstrip()
    assert phys_line.startswith("else"), phys_line
    phys_line = phys_line[4:].lstrip()
    if not phys_line or phys_line[0]=='#' :
        # rest of line is empty or a comment
        return None

    d = seek_directive(phys_line)
    if d in conditional_directive :
#        print("found elseif condition=\"{0}\"".format(d))
        return d,VirtualLine.from_string(phys_line)

    # found junk after else
    # .e.g, 
    #   else export iamnotlegal
    #   else $(info I am not legal)
    # (TODO need a better error message)
    errmsg = "Extra stuff after else"
    raise ParseError(vline=virt_line, pos=virt_line.starting_pos(),
                description=errmsg)

#@depth_checker
def handle_conditional_directive(directive_inst, vline_iter, line_scanner):
    # GNU make doesn't parse the stuff inside the conditional unless the
    # conditional expression evaluates to True. But Make does allow nested
    # conditionals. Read line by line, looking for nested conditional
    # directives
    #
    # directive_inst - an instance of DirectiveExpression
    # vline_iter - <generator>across VirtualLine instances (does NOT support
    #               pushback)
    # line_scanner - ScannerIterator instance of physical lines from the file
    #               (does support pushback)
    #
    # vline_iter is from get_vline() and reads from line_scanner underneath. The
    # line_scanner and vline_iter will operate in lockstep.
    #
    # It's very confusing. But need to pass around both the iterators because
    # the backslash rules change depending on where we are. And the contents of
    # the conditional directives aren't parsed unless the condition is true.

    # call should have sent us a Directive instance (stupid human check)
    assert isinstance(directive_inst,ConditionalDirective), type(directive_inst)

#    print( "handle_conditional_directive() \"{0}\" line={1}".format(
#        directive_inst.name, line_scanner.idx-1))

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
    starting_pos = directive_inst.code.starting_pos

    for virt_line in vline_iter : 
#        print("c state={0}".format(state))
#        print("={0}".format(str(virt_line)), end="")

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
            sub_block = tokenize_directive(directive_str, virt_line, vline_iter, line_scanner)
            cond_block.add_block( sub_block )
            
        elif directive_str=="else" : 
            if state==state_else : 
                errmsg = "too many else"
                raise ParseError(vline=virt_line, pos=virt_line.starting_pos(),
                            description=errmsg)

            # save the block of stuff we've read
            line_list = save_block(line_list)

#            print("phys_line={0}".format(printable_string(phys_line)))

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
#            print("save \"{0}\"".format(printable_string(str(virt_line))))
            line_list.append(virt_line)

        if state==state_endif : 
            # close the if/else/endif collection
            break

    # did we hit bottom of file before finding our end?
    if state != state_endif :
        errmsg = "missing endif"
        raise ParseError(pos=starting_pos, description=errmsg)
    
    return cond_block

def tokenize_define_directive(vchar_scanner):
    # multi-line macro

    logger.debug("tokenize_define_directive()")

    state_start = 1
    state_name = 2
    state_eol = 3

    state = state_start
    macro_name = vline.VCharString()

    # 3.81 treats the = as part of the name
    # 3.82 and beyond introduced the "=" after the macro name
    if Version.major<=3 and Version.minor<=81: 
        raise NotImplementedError()

    # get the starting position of this scanner (for error reporting)
    starting_pos = vchar_scanner.lookahead().pos
#    print("starting_pos=", starting_pos)

    for vchar in vchar_scanner : 
        c = vchar.char
        logger.debug("m c={0} state={1} pos={2} ".format( 
                printable_char(c), state, vchar.pos))

        if state==state_start:
            # always eat whitespace while in the starting state
            if c in whitespace : 
                # eat whitespace
                pass
            else:
                vchar_scanner.pushback()
                state = state_name

        elif state==state_name : 
            # save the name until EOL (we'll strip off the trailing RHS
            # whitespace later)
            #
            # TODO if Version > 3.81 then add support for "="
            if c in whitespace or c in eol or c == '=':
                state = state_eol
                break
            else:
                macro_name += vchar

        else:
            assert 0, state

    return macro_name

def tokenize_undefine_directive(vchar_scanner):
    raise NotImplementedError("undefine")

def handle_define_directive(define_inst, vline_iter, vchar_scanner):

    # array of VirtualLine
    line_list = []

    # save where this define block begins so we can report errors about 
    # missing enddef 
    starting_pos = define_inst.code.starting_pos

    for virt_line in vline_iter : 

        # seach for enddef in physical line
        phys_line = str(virt_line).lstrip()
        if phys_line.startswith("endef"):
            phys_line = phys_line[5:].lstrip()
            if not phys_line or phys_line[0]=='#':
                break
            errmsg = "extraneous text after 'enddef' directive"
            raise ParseError(vline=virt_line, pos=virt_line.starting_pos(),
                        description=errmsg)

        line_list.append(virt_line)
    else :
        errmsg = "missing enddef"
        raise ParseError(pos=starting_pos, description=errmsg)

    define_inst.set_block(LineBlock(line_list))
    return define_inst

#@depth_checker
def tokenize_directive(directive_str, virt_line, vline_iter, line_scanner):
    logger.debug("tokenize_directive() \"%s\" at pos=%r",
            directive_str, virt_line.starting_pos)

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
        # TODO the way I'm doing this dict is stupid. fix it.
        "export" : { "constructor" : ExportDirective,
                     "tokenizer"   : tokenize_statement,
                   },
        "unexport" : { "constructor" : UnExportDirective,
                       "tokenizer"   : tokenize_statement,
                     },

        "include" : { "constructor" : IncludeDirective,
                       "tokenizer"   : tokenize_assign_RHS,
                     },
        "-include" : { "constructor" : MinusIncludeDirective,
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
        
        "undefine" : { "constructor" : UnDefineDirective,
                     "tokenizer" : tokenize_undefine_directive,
                   },  
        # TODO add rest of opening directives
    }

    if directive_str=="else" or directive_str=="endif" :
        errmsg = "extraneous " + directive_str
        raise ParseError(vline=virt_line, pos=virt_line.starting_pos(),
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

#    print("{0} expression=\"{1}\"".format(directive_str, printable_string(str(expression))))

    # construct a Directive instance
    try : 
        directive_instance = d["constructor"](expression)
    except ParseError as err:
        err.vline = virt_line
        err.pos = virt_line.starting_pos()
        raise err

    directive_instance.save(virt_line)

    # gather the contents of the conditional block (raw lines
    # and maybe nested conditions)
    if directive_str in conditional_directive :
        return handle_conditional_directive(directive_instance, vline_iter, line_scanner)

    if directive_str == "define": 
        return handle_define_directive(directive_instance, vline_iter, line_scanner)

    return directive_instance

#@depth_checker
def tokenize(virt_line, vline_iter, line_scanner): 
    # pull apart a single line into token/symbol(s)
    #
    # virt_line - the current line we need to tokenize (a VirtualLine)
    #
    # vline_iter - <generator> across the entire file (returns VirtualLine instances) 
    #
    # line_scanner - ScannerIterator across the file lines (supports pushback)
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
        token = tokenize_directive(directive_str, virt_line, vline_iter, line_scanner)
        return token

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)
    statement = tokenize_statement(vchar_scanner)

    # If we found a rule, we need to change how we're handling the
    # lines. (Recipes have different whitespace and backslash rules.)
    if not isinstance(statement,RuleExpression) : 
        logger.debug("statement=%s", str(statement))
        return statement

    # At this point we have a Rule.
    # rule line can contain a recipe following a ; 
    # for example:
    # foo : bar ; @echo baz
    #
    # The rule parser should stop at the semicolon. Will leave the
    # semicolon as the first char of iterator
    # 
#    logger.debug("rule=%s", str(token))

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
    remaining_vchars = vchar_scanner.remain()
    if len(remaining_vchars) > 0:
        # truncate at position of first char of whatever is
        # leftover from the rule
        truncate_pos = remaining_vchars[0].pos
#            print("remaining=%s" % remaining_vchars)
#            print("first remaining=%s pos=%r" % (remaining_vchars[0].char,remaining_vchars[0].pos))
#            print("truncate_pos=%r" % (truncate_pos,))

        recipe_str_list = virt_line.truncate(truncate_pos)

        # make a new virtual line from the semicolon trailing
        # recipe (using a virtual line because backslashes)
        dangling_recipe_vline = vline.RecipeVirtualLine(recipe_str_list, truncate_pos, remaining_vchars[0].filename)
#            print("dangling={0}".format(dangling_recipe_vline))
#            print("dangling={0}".format(dangling_recipe_vline.virt_chars))
#            print("dangling={0}".format(dangling_recipe_vline.phys_lines))

        recipe_list = parse_recipes(line_scanner, dangling_recipe_vline)
    else :
        recipe_list = parse_recipes(line_scanner)

    assert isinstance(recipe_list,RecipeList)

    logger.debug("recipe_list=%s", str(recipe_list))

    # attach the recipe(s) to the rule
    statement.add_recipe_list(recipe_list)

    logger.debug("statement=%s", str(statement))
    return statement

def parse_makefile_from_src(src):
    # file_lines is an array of Python strings.
    # The newlines must be preserved.

    logger.debug("parse from src=%s", src.name)

    # trigger getting an array of python strings from the source
    src.load()

    # ScannerIterator across the file_lines array (to support pushback of an
    # entire line). 
    line_scanner = ScannerIterator(src.file_lines, src.name)

    # get_vline() returns a Python <generator> that walks across makefile
    # lines, joining backslashed lines into VirtualLine instances.
    vline_iter = vline.get_vline(src.name, line_scanner)

    # The vline_iter will read from line_scanner. But line_scanner should be at the
    # proper place at all times. In other words, there are two readers from
    # line_scanner: this function and tokenize_vline()
    # Recipes need to read from line_scanner (different backslash rules).
    # Rest of tokenizer reads from vline_iter.
    token_list = [tokenize(vline, vline_iter, line_scanner) for vline in vline_iter] 

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
    logger.debug("parse_makefile infilename=%s", infilename)
    src = source.SourceFile(infilename)

    try : 
        return parse_makefile_from_src(src)
#        return parse_makefile_from_strlist(file_lines)
    except ParseError as err:
        err.filename = infilename
        print(err, file=sys.stderr)
        raise

def round_trip(makefile):
    dumpmakefile="""
print("# start makefile")
print("\\n".join( [ "{0}".format(m.makefile()) for m in makefile ] ) )
print("# end makefile")
"""

    with open("out.py", "w") as outfile:
        print("#!/usr/bin/env python3", file=outfile)
        print("from pymake import *", file=outfile)
        print("from vline import VirtualLine", file=outfile)
        print("makefile="+str(makefile), file=outfile)
#        print("makefile=",",\\\n".join( [ "{0}".format(block) for block in makefile ] ),file=outfile )
#        print("print(\"{0}\".format(makefile))", file=outfile)
        print(dumpmakefile, file=outfile)
        

def find_location(tok):
    # recursively descend into a token tree to find a token with a non-null vcharstring
    # which will show the starting filename/position of the token
    logger.debug("find_location tok=%s", tok)

    if isinstance(tok, ConditionalBlock):
        # conditionals don't have a token_list so we have to drill into the
        # instance to find something that does
        return find_location(tok.cond_exprs[0].expression)

    # If the tok has a token_list, it's an Expression
    # otherwise, is a Symbol.
    #
    # Expressions contain list of Symbols (although an Expression is also
    # itself a Symbol). Expression does not have a string (VCharString)
    # associated with it but contains the Symbols that do.
    try:
        for t in tok.token_list:
            return find_location(t)
    except AttributeError:
        # we found a Symbol
        c = tok.string[0]
        return c.filename, c.pos
#        for c in tok.string:
#            logger.debug("f %s %s %s", c, c.pos, c.filename)

def execute(makefile):
    # tinkering with how to evaluate
    logger.info("Starting execute of %s", id(makefile))
    from symtable import SymbolTable
    symtable = SymbolTable()

    for tok in makefile.token_list:
        try:
            s = tok.eval(symtable)
            logger.debug("execute result s=\"%s\"", s)
        except MakeError:
            # let ParseError propagate
            raise
        except:
            # My code crashed. For shame!
            logger.error("INTERNAL ERROR eval exception during token makefile=%s", tok.makefile())
            logger.error("INTERNAL ERROR eval exception during token string=%s", tok.string)
#            logger.error("eval exception during token token_list=%s", tok.token_list)
#            for t in tok.token_list:
#                logger.error("token=%s string=%s", t, t.string)
            filename,pos = find_location(tok)
#            logger.exception("INTERNAL ERROR")
            logger.error("eval failed tok file=%s pos=%s", filename, pos)
            raise

def usage():
    # TODO
    print("usage: TODO")

def parse_args():
    print_version ="""PY Make %d.%d\n
Copyright (C) 2006-2022 David Poole davep@mbuf.com, testcluster@gmail.com""" % (0,0)

    parser = argparse.ArgumentParser(description="Makefile Debugger")
    parser.add_argument('-o', '--output', help="write regenerated makefile to file") 
    parser.add_argument('-d', '--debug', action='count', help="set log level to DEBUG (default is INFO)") 
    parser.add_argument('-S', dest='s_expr', action='store_true', help="output the S-expression to stdout") 

    # var assignment(s)
    #    e.g. make CC=gcc 
    # or a target(s)
    #    e.g. make clean all
    parser.add_argument("args", metavar='args', nargs='*')
    # result (if any) will be in args.args
    
    # arguments 100% compatible with GNU Make
    parser.add_argument('-f', '--file', '--makefile', dest='filename', help='read FILE as a makefile', default="Makefile" )
    parser.add_argument('-v', '--version', action='version', version=print_version, help="Print the version number of make and exit.")

    args = parser.parse_args()

    # TODO additional checks

    return args

if __name__=='__main__':
    args = parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2 : 
        usage()
        sys.exit(1)

    infilename = args.filename
    try : 
        makefile = parse_makefile(infilename)
    except ParseError:
        # TODO dump lots of lovely useful information about the failure.
        sys.exit(1)

    # print the S Expression
    if args.s_expr:
        print("# start S-expression")
        print("makefile={0}".format(makefile))
        print("# end S-expression")

    # regenerate the makefile
    if args.output:
        print("# start makefile")
        with open(args.output,"w") as outfile:
            print(makefile.makefile(), file=outfile)
        print("# end makefile")

    execute(makefile)

