# SPDX-License-Identifier: GPL-2.0
# Copyright (C) David Poole david.poole@ericsson.com

import logging
import string

_debug = True

logger = logging.getLogger("pymake.tokenize")
#logger.setLevel(level=logging.DEBUG)

from pymake.constants import *
from pymake.error import *
from pymake.printable import printable_char, printable_string
import pymake.vline as vline
from pymake.symbolmk import *
import pymake.functions as functions

# XXX temp for interactive debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

def comment(vchar_scanner):
    # Seems weird to character by character consume a line comment until the
    # end of line. This function used to keep the char scanner in sync with
    # expected results. There are some places where I'm making sure I've
    # consumed the entire line.
    vchar = next(vchar_scanner)
    assert vchar.char == '#', vchar.get_pos()
    for vchar in vchar_scanner:
        pass

def tokenize_define_directive(vchar_scanner):
    # multi-line macro

    # ha-ha type checking
    assert isinstance(vchar_scanner,ScannerIterator), type(vchar_scanner)

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

def tokenize_statement(vchar_scanner):
    # davep 20241116 ; rewriting the tokenizer from scratch to better match GNU Make's eval()-read.c
    assert 0, "DO NOT USE"

    # vchar_scanner == ScannerIterator
    #
    # at start of scanning, we don't know if this is a rule or an assignment
    # this is a test : foo   -> (this,is,a,test,:,)
    # this is a test = foo   -> (this is a test,=,)
    #
    # Only difference between a Rule LHS and an assignment LHS is the
    # whitespace. In a Rule, the whitespace is ignored. In an Assignment, the
    # whitespace is preserved.
    #
    # We tokenize the LHS until we find a RuleOperator, and AssignmentOperator,
    # or end of line. Depending on what operator we receive (or no operator),
    # we'll create the appropriate statement.
    #
    # Note: This function will never be called with a Recipe

    # get the starting position of this string (for error reporting)
    starting_pos = vchar_scanner.lookahead().pos

    logger.debug("tokenize_statement() pos=%s", starting_pos)

    # save current position in the token stream
    lhs, operator = tokenize_statement_LHS(vchar_scanner)

    # remove last token if it's whitespace (strip trailing whitespace)
    if lhs[-1].is_whitespace():
        lhs.pop()

    # remove leading whitespace (if any)
    if lhs and lhs[0].is_whitespace():
        del lhs[0]

    # lhs should be an array of stuff in the Symbol class hierarchy so now we
    # need to decode what kind of statement do we have based on where
    # tokenize_statement_LHS() stopped.

    logger.debug("operator=%s", operator)
#    breakpoint()

    if isinstance(operator,RuleOp): 
        logger.debug( "last_token=%s ∴ statement is Rule", operator)

        # add rule RHS
        # rule RHS  ::= assignment
        #            | prerequisite_list
        #            | <empty>
        statement = [ TargetList(lhs), 
                      operator, 
                      tokenize_rule_prereq_or_assign(vchar_scanner)
                    ]

        # don't look for recipe(s) yet
        return RuleExpression(statement) 

    if isinstance(operator,AssignOp): 
        # tough parse case:
        # define xyzzy =    <-- opening of a multi-line variable. Can be
        #                       confused with an assignment expression.
        # define =    <-- assignment expression
        # GNU Make y u no have reserved words?

        logger.debug( "last_token=%s ∴ statement is Assign", operator)

        # The statement is an assignment. Tokenize rest of line as an assignment.
        statement = [ Expression(lhs), 
                      operator, 
                      tokenize_assign_RHS(vchar_scanner)
                    ]

        return AssignmentExpression(statement)

    if operator is None:
        logger.debug( "last_token=%s ∴ statement is Expression", operator)

        # Wind up in this case when have a non-rule and non-assignment.
        # Will get here with $(varref) e.g., $(info) $(shell) $(call) 
        # Also get here with an 'export' LHS.
        # Will get here when parsing multi-line 'define'.
        # Need to find clean way to return clean Expression and catch parse
        # error

        # The statement is a directive or bare words or function call. We
        # better have consumed the whole thing.
        assert vchar_scanner.is_empty(), vchar_scanner.remain()[0].get_pos()
        
        # LHS should be one an array of Symbol. We'll dig into the Expression
        # during the 2nd pass.

        return Expression(lhs)

    # should not get here
    assert 0, operator


def tokenize_line(vchar_scanner):

    logger.debug("tokenize_line at %r", vchar_scanner.get_pos())

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4

    # array of vchar
    token = vline.VCharString()

    token_list = []

    def pushtoken(t):
        # if we have something to make a literal from then
        if len(t):
            # create the literal, save to the token_list
            token_list.append(Literal(t))
        # then start new token
        return vline.VCharString()

    state = state_start

    for vchar in vchar_scanner : 
        c = vchar.char
        logger.debug("e c={} state={} idx={} token=\"{}\" pos={} src={}".format(
            printable_char(c), state, vchar_scanner.idx, str(token), vchar.pos, vchar.filename))

        if state==state_start:
            if c in whitespace: 
                # save whitespace as its own Literal
                token += vchar
            else :
                # whatever it is, push it back so can tokenize it
                vchar_scanner.pushback()
                # save the whitespace string we've seen so far
                token = pushtoken(token)
                state = state_in_word

        elif state==state_in_word:
            if c==backslash:
                state = state_backslash
                token += vchar

            elif c in whitespace:
                # end of word
                # and start new token
                token = pushtoken(token)

                # jump back to start searching for next symbol
                vchar_scanner.pushback()
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # capture anything we might have seen 
                # and start new token
                token = pushtoken(token)
                # done with this line
                # eat the comment (which lets us cleanly drop out of the loop
                # as well as sanity check the scanner)
                vchar_scanner.pushback()
                comment(vchar_scanner)

            elif c in eol : 
                # capture any leftover when the line ended
                token = pushtoken(token)
                # end of line; bye!
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
                # save token so far (if any)
                # also starts new token
                token = pushtoken(token)
                
                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )

            state=state_in_word

        elif state==state_backslash :
            # literal '\' + somechar
            token += vchar
            state = state_in_word

        else:
            # wtf?
            assert 0, state

    # ran out of string; save anything we might have seen
    token = pushtoken(token)

    return token_list


def tokenize_statement_LHS(vchar_scanner):

    assert 0, "FIXME do not use this anymore"


    # Tokenize the LHS of a rule or an assignment statement. A rule uses
    # whitespace as a separator. An assignment statement preserves internal
    # whitespace but leading/trailing whitespace is stripped.

    # I'm using this function as the first stop in tokenizing *everything*
    # (rule, assignment, and plain expression).  A Rule or Assignment has a
    # terminating Operator (Rule uses :, Assignment uses = := += etc). 
    #
    # The problem is a plain Expression is hard to disambiguate from an
    # assignment.
    #
    # export CC=gcc is an assignment
    # ifeq (=CC,=CC) is an expression
    #
    # I can't blindly look for colon or assignment to terminate the tokenzing
    # and assume I have an LHS. I have to carefully maintain state of the
    # characters I see.
    #
    # GNU make uses raw C strings and jumps around in the string. I'm not doing
    # that. I decided to be clever and use a state machine.
    #
    
    # Expression is single function like $(info) or $(warning) or a directive
    # (ifdef, etc). Not all functions are valid in statement context.  A lone
    # Expression in GNU Make usually triggers the "missing separator" error
    # because the parser gets confused.
    #

    logger.debug("tokenize_statement_LHS()")

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4
    state_colon = 5
    state_colon_colon = 6
    state_error = 7

    # array of vchar
    token = vline.VCharString()

    token_list = []

    def pushtoken(t):
        # if we have something to make a literal from then
        if len(t):
            # create the literal, save to the token_list
            token_list.append(Literal(t))
        # then start new token
        return vline.VCharString()

    # Before can disambiguate assignment vs rule, must parse forward enough to
    # find the operator. Otherwise, the LHS between assignment and rule are
    # identical.
    #
    # BNF is sorta
    # Statement ::= Assignment | Rule | Directive | Expression
    # Assignment ::= LHS AssignmentOperator RHS
    # Rule       ::= LHS RuleOperator RHS
    # Directive  ::= define ifdef etc etc
    # Expression ::= everything else
    #
    # Directive is stuff like ifdef export vpath define. Directives get
    # slightly complicated because
    #   ifdef :  <--- not legal
    #   ifdef:   <--- legal (verified 3.81, 3.82, 4.0)
    #   ifdef =  <--- legal
    #   ifdef=   <--- legal



    # get the starting position of this scanner (for error reporting)
    starting_pos = vchar_scanner.lookahead().pos
    logger.debug("LHS starting_pos=%s", starting_pos)

    state = state_start
    start_count = 0

    for vchar in vchar_scanner : 
        # ha ha type checking
        assert vchar.filename 

        c = vchar.char
        logger.debug("s c={} state={} idx={} token=\"{}\" pos={} src={}".format(
            printable_char(c), state, vchar_scanner.idx, str(token), vchar.pos, vchar.filename))

        if state==state_start:
            # eat whitespace while in the starting state
            # NOTE: we will NEVER call this function for a Recipe so always ignore RECIPEPREFIX
            if c in whitespace: 
                # save whitespace as its own Literal
                token += vchar
            elif c==':':
                state = state_colon
                # save the whitespace string we've seen so far
                token = pushtoken(token)
                token += vchar
            else :
                # whatever it is, push it back so can tokenize it
                vchar_scanner.pushback()
                # save the whitespace string we've seen so far
                token = pushtoken(token)
                state = state_in_word
                start_count += 1

        elif state==state_in_word:
            if c==backslash:
                state = state_backslash
                token += vchar

            elif c in whitespace:
                # end of word
                # and start new token
                token = pushtoken(token)

                # jump back to start searching for next symbol
                vchar_scanner.pushback()
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # capture anything we might have seen 
                # and start new token
                token = pushtoken(token)
                # done with this line
                # eat the comment (which lets us cleanly drop out of the loop
                # as well as sanity check the scanner)
                vchar_scanner.pushback()
                comment(vchar_scanner)

            elif c==':':
                # end of LHS (don't know if rule or assignment yet)
                # start new token
                token = pushtoken(token)
                # keep scanning until we know what colon token we've seen
                token += vchar
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if vchar_scanner.lookahead().char == '=':
                    eq = vchar_scanner.next()
                    assign = AssignOp(vline.VCharString([vchar, eq]))
                    token = pushtoken(token)
                    return [token_list, assign]
                else:
                    token += vchar

            elif c=='=':
                # definitely an assignment 
                token = pushtoken(token)
                return [token_list, AssignOp(vline.VCharString([vchar]))]

            elif c in eol : 
                # capture any leftover when the line ended
                token = pushtoken(token)
                # end of line; bye!
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
                # save token so far (if any)
                # also starts new token
                token = pushtoken(token)
                
                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )

            state=state_in_word

        elif state==state_backslash :
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
                return [token_list, AssignOp(token) ]
            else:
                # Single ':' followed by something. Whatever it was, put it back!
                vchar_scanner.pushback()
                # successfully found LHS 
                return [token_list, RuleOp(token)]

        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                token += vchar
                return [token_list, AssignOp(token) ]

            vchar_scanner.pushback()
            # successfully found LHS 
            return [token_list, RuleOp(token) ]

        else:
            # should not get here
            assert 0, state

    # ran out of string; save anything we might have seen
    token = pushtoken(token)

    logger.debug("end of LHS state=%d", state)

    # hit end of scanner; what was our final state?
    if state==state_colon:
        # Found a Rule
        # ":"
        return [token_list, RuleOp(":") ]

    if state==state_colon_colon:
        # Found a Rule
        # "::"
        return [token_list, RuleOp("::") ]

    # Found a plain expression of some sort.
    # likely word(s) or a $() call. For example:
    # a b c d
    # $(info hello world)
    # davep 17-Nov-2014 ; using this function to tokenize 'export' RHS
    # which could be just a list of variables e.g., export CC LD RM 
    # Return a raw expression that will have to be tokenize/parsed
    # downstream.

    return [token_list, None ]


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
        # FIXME 20230205 I've broken this with the new LHS tokenizer
        raise NotImplementedError()

#        statement = tokenize_statement_LHS(vchar_scanner)
#        assert isinstance(statement, list)
#        assert isinstance(statement[0], Expression)
#
#        # verify the operator parsed correctly 
#        assert str(statement[-1].string) in assignment_operators
#
#        statement.append( tokenize_assign_RHS(vchar_scanner) )
#        rhs = AssignmentExpression( statement )
    else : 
        assert isinstance(rhs,PrerequisiteList)

    # stupid human check
    for token in rhs : 
        assert isinstance(token,Symbol),(type(token), token)

    return rhs

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

    # rule prerequisites are a whitespace separated collection of Expressions.
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

            elif c==backslash:
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
                # comment so ignore from here to the end of line
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
                breakpoint()
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
                token += prev_vchar # capture the literal backslash
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

        # save the vchar in case we need it in the next go round
        prev_vchar = vchar

    # bottom of loop

    # davep 07-Dec-2014 ; do we ever get here? 
    assert 0, state

def tokenize_assign_RHS(vchar_scanner):
    # davep 20241124 ; do not use this function anymore; use tokenize_line()
    assert 0, "FIXME do not use this function anymore; use tokenize_line"

    logger.debug("tokenize_assign_RHS()")

    state_start = 1
    state_dollar = 2
    state_literal = 3
    state_whitespace = 4

    state = state_start
    token = vline.VCharString()
    token_list = []

    vchar = next(vchar_scanner)
    # it's stupid to have state_start inside the loop since I'll only be in it
    # once
    if vchar.char in whitespace :
        state = state_whitespace
    else :
        vchar_scanner.pushback()
        state = state_literal

    for vchar in vchar_scanner :
        c = vchar.char
        logger.debug("r c={0} state={1} idx={2}".format(printable_char(c), state, vchar_scanner.idx, vchar_scanner.remain()))

        if state==state_whitespace :
            if not c in whitespace : 
                vchar_scanner.pushback()
                state = state_literal

        elif state==state_literal:
            if c=='$' :
                state = state_dollar
            elif c=='#':
                # save the token we've seen so far
                vchar_scanner.pushback()
                # stay in same state
                # eat comment 
                comment(vchar_scanner)
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
                if len(token):
                    token_list.append(Literal(token))
                # restart token
                token = vline.VCharString()

                # restore current char and '$' back to the scanner
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
    open_vchar = None
    # stack of open/close chars so we can report very accurate error positions
    open_vchar_stack = []

    state = state_start
    token = vline.VCharString()
    token_list = []

    close_char = None

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
                open_vchar = vchar
                open_vchar_stack.append(vchar)
                close_char = ')' if c=='(' else '}'
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
                # Yes. GNU Make 4.3 is ignoring it, depending on the context.
                raise ParseError(msg="unclosed variable ref", pos=vchar.get_pos())

        elif state==state_in_var_ref:
            assert close_char is not None
            if c==close_char:
                # end of var ref
                # () {} good
                # (} {) bad 

#                print("v found close_char={} at pos={} len(stack)={}".format(
#                    vchar.char, vchar.get_pos(), len(open_vchar_stack)))

                try:
                    previous_vchar = open_vchar_stack.pop()
                except IndexError:
                    # Unbalanced expression.
                    # TODO nice error message
                    raise ParseError()

                # if the stack is empty, we have a balanced expression so we
                # _should_ be done.

                if len(open_vchar_stack) == 0:
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
                else:
                    # another part of the literal string we're building
                    token += vchar

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

            elif c == open_vchar.char:
                # we have an embedded open char.
                # e.g., $(info ())
                # so we have carefully track the open/close matching just as
                # GNU Make does.
                # Note we don't have to track the opposite open/close char; ie,
                # if open is paren then we can safely ignore all open/close
                # curly.
#                print( "v found open vchar={} at pos={}".format(
#                    vchar.char, vchar.get_pos()))
                open_vchar_stack.append(vchar)
                token += vchar

            else:
                token += vchar

        else:
                # should not get here
            assert 0, state

    raise ParseError(pos=vchar.get_pos(), description="VarRef not closed")

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

    for vchar in vchar_scanner :
        c = vchar.char
        logger.debug("r c={} state={} idx={} token=\"{}\" pos={}".format(
            printable_char(c), state, vchar_scanner.idx, printable_string(str(token)), vchar.pos))

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
            elif c==backslash:
                vchar_stack.append(vchar)
                state = state_backslash
            else:
                token += vchar 

        elif state==state_dollar : 
            if c=='$':
                # a $$ in a rule expression needs to be preserved as a double $$
                token += prev_vchar # capture the previous '$'
                token += vchar
                state = state_recipe
            else:
                # definitely a variable ref of some sort
                # save token so far
                if len(token):
                    token_list.append(Literal(token))
                # restart token
                token = vline.VCharString()

                # restore current char and "$" to the scanner
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

        # save the vchar in case we need it in the next go round
        prev_vchar = vchar

    # bottom of loop

    logger.debug("end of scanner state=%d", state)

    # end of scanner
    # save what we've seen so far
    if state==state_recipe : 
        token_list.append(Literal(token))
    else:
        # should not get here
        assert 0, state

    return Recipe( token_list )

def tokenize_assignment_expression(vchar_scanner):

    # Assume this statement is an assignment and attempt to tokenize it as such.
    # Return None if this statement is not an assignment.

    # array of vchar
    token = vline.VCharString()

    token_list = []

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4
    state_colon = 5
    state_colon_colon = 6
    state_seek_assign = 7

    state = state_start

    def savetoken(t):
        # if we have something to make a literal from then
        if len(t):
            # create the literal, save to the token_list
            token_list.append(Literal(t))
        # then start new token
        return vline.VCharString()

    for vchar in vchar_scanner:
        c = vchar.char

        logger.debug("a c={} state={} idx={} token=\"{}\" pos={} src={}".format(
            printable_char(c), state, vchar_scanner.idx, str(token), vchar.pos, vchar.filename))

        if state==state_start:
            # eat whitespace while in the starting state
            if c in whitespace: 
                # save whitespace as its own Literal
                token += vchar
            else :
                # whatever it is, push it back so can tokenize it
                vchar_scanner.pushback()
                # save the whitespace string we've seen so far
                token = savetoken(token)
                state = state_in_word

        elif state==state_in_word:
            if c==backslash:
                state = state_backslash
                token += vchar

            elif c in whitespace:
                # end of word
                # and start new token
                token = savetoken(token)

                # Whitespace and AssignOp is the only way to separate the fields of
                # an assignment statement. We've seen a word. Now we need to
                # look for an Assignment Operator. If we don't seen an
                # Assignment Operator next, we're not an Assignment statement.
                vchar_scanner.pushback()
                state = state_seek_assign

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # at this point, we have ended useful input and 
                # we haven't found an assignment
                return None

            elif c==':':
                # start new token
                token = savetoken(token)
                # keep scanning until we know what colon token we've seen
                token += vchar
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if vchar_scanner.lookahead().char == '=':
                    token = savetoken(token)
                    # consume the character
                    eq = vchar_scanner.next()
                    operator = AssignOp(vline.VCharString([vchar, eq]))

                    statement = [ Expression(token_list), 
                                  operator, 
                                  Expression(tokenize_line(vchar_scanner))
                                ]
                    return AssignmentExpression(statement)

                else:
                    token += vchar

            elif c=='=':
                # definitely an assignment 
                token = savetoken(token)
                operator = AssignOp(vline.VCharString([vchar]))

                statement = [ Expression(token_list), 
                              operator, 
                              Expression(tokenize_line(vchar_scanner))
                            ]
                return AssignmentExpression(statement)

            elif c in eol : 
                # end of line without finding assignment operator; bye!
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
                # save token so far (if any)
                # also starts new token
                token = savetoken(token)
                
                # jump to variable_ref tokenizer
                # restore "$" + "(" in the scanner
                vchar_scanner.pushback()
                vchar_scanner.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(vchar_scanner) )

            state=state_in_word

        elif state==state_backslash :
            # literal '\' + somechar
            # FIXME I'm probably doing this wrong. Need to lookup the \x to see
            # if it's a valid char. What does GNU Make do?
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
                # end of LHS
                token += vchar
                statement = [ Expression(token_list), 
                              AssignOp(token), 
                              Expression(tokenize_line(vchar_scanner))
                            ]
                return AssignmentExpression(statement)
            else:
                # Single ':' followed by something we don't care about.
                # Might be a rule.
                return None

        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                token += vchar
                statement = [ Expression(token_list), 
                              AssignOp(token), 
                              Expression(tokenize_line(vchar_scanner))
                            ]
                return AssignmentExpression(statement)

            # double :: followed by something we don't care about. 
            # Might be a rule.
            return None

        elif state == state_seek_assign:
            # At this point we've seen one string then some whitespace.
            # Since variable names cannot contain whitespace, the next thing we
            # need to find is an assignment operator OR we're definitely not an
            # assignment statement.

            if c in whitespace: 
                # save whitespace as its own Literal
                token += vchar

            elif c == ':':
                # end of current token
                token = savetoken(token)
                token += vchar

                # allow := ::= :::=
                while len(token) <= 3:
                    peek = vchar_scanner.lookahead().char

                    if peek == '=':
                        # found :=
                        # consume the '='
                        token += vchar_scanner.next()
                        assign = AssignOp(token)
                        statement = [ Expression(token_list), 
                                      assign,
                                      Expression(tokenize_line(vchar_scanner))
                                    ]
                        return AssignmentExpression(statement)
                    elif peek == ':':
                        # consume the ':'
                        # go back for more
                        token += vchar_scanner.next()
                    else:
                        break

                return None

            elif c == '=':
                token = savetoken(token)
                # definitely an assignment!
                operator = AssignOp(vline.VCharString([vchar]))

                statement = [ Expression(token_list), 
                              operator, 
                              Expression(tokenize_line(vchar_scanner))
                            ]
                return AssignmentExpression(statement)

            elif c in set("?+!"):
                if vchar_scanner.lookahead().char == '=':
                    eq = vchar_scanner.next()
                    assign = AssignOp(vline.VCharString([vchar, eq]))

                    statement = [ Expression(token_list), 
                                  assign,
                                  Expression(tokenize_line(vchar_scanner))
                                ]
                    return AssignmentExpression(statement)

                else:
                    # TODO
                    raise ParseError(pos=vchar.pos)

            else:
                # we wind up here when we're looking for an assignment operator
                # but find something else.
                # We also wind up here with something like "export CC=gcc" where
                # we export+assign in the same statement
                return None

            # endif state == state_assign

        else:
            # should not get here
            assert 0, state

def seek_word(viter, seek):
    # seek a specific word from set 'seek'
    # used to find GNU Make's "reserved" words (define, ifdef, etc)
    #
    # viter - character iterator
    # * eat leading whitespace
    # * look for a string in set 'seek'
    #   string will always be [a-z][A-Z]+
    # * eat trailing whitespace so iterator is positioned at 
    #   next possible char
    #
    # seek - set of strings
    #
    # If we don't find something in set 'seek', restore the state of viter

    # ha ha type checking
    _ = viter.pushback
    _ = seek.union

    # if we find any non-whitespace outside this set, we definitely don't have
    # a word in set 'seek'
    charset = set(c for s in seek for c in s)

    if _debug:
        logger.debug("seek_word seek=%r", seek)
    else:
        logger.debug("seek_word")

    if viter.is_empty():
        # nothing to parse so nothing to find
        logger.debug("seek_word False")
        return None

    # we're looking ahead to see if we have a "reserved word" inside our set 'seek'
    # so we need to save the state; we'll restore it on return if we haven't
    # found a "reserved word".
    viter.push_state()

    vcstr = vline.VCharString()

    # look at first char first
    vchar = next(viter)

    state_whitespace = 1  # ignore leading whitespace
    state_char = 2
    state_trailing_whitespace = 3

    if vchar.char in whitespace:
        state = state_whitespace
    else:
        state = state_char
        vcstr += vchar

#    print("seek_word c={0} state={1}".format(printable_char(vchar.char), state))

    for vchar in viter:
        c = vchar.char

        # continue to ignore leading whitespace
#        print("seek_word c={0} state={1} pos={2}".format(printable_char(vchar.char), state, vchar.get_pos()))
        if state == state_whitespace:
            if not c in whitespace:
                state = state_char
                viter.pushback()

        elif state == state_char:
            if c in whitespace|eol:
                state = state_trailing_whitespace
            elif c == '#':
                viter.pushback()
                comment(viter)                
            elif c not in charset:
                # definitely not something we are looking for
                vcstr.clear()
                viter.pushback()
                break
            else:
                vcstr += vchar

        elif state == state_trailing_whitespace:
            if c == '#':
                viter.pushback()
                comment(viter)                
            elif c not in whitespace|eol:
                # push back the char we just looked at
                # so caller gets a clean iterator
                viter.pushback()
                break

    # did we find a "reserved word" amidst all this whitespace?
    s = str(vcstr)
    if s in seek:
        # yay! we found a "reserved word"!
        logger.debug("seek_word found \"%s\" at %r", s, vcstr.get_pos())
        viter.clear_state()
        return vcstr

    # nope, not a "reserved word"
    viter.pop_state()
    logger.debug("seek_word False")
    return None

def tokenize_assignment_statement(vchar_scanner):
    # look for an assignment expression
    # if that fails, look for a modified assignment expression, one with 
    # export | unexport | override | private | define | undefine
    # can have multiple modifiers e.g.,
    # export private override CC=gcc
    
    pos = vchar_scanner.get_pos()
    logger.debug("tokenize_assignment_statement at %r", pos)

    modifier_list = []

    vchar_scanner.push_state()

    while True:
        # loop to capture multiple modifiers
        vchar_scanner.push_state()

        e = tokenize_assignment_expression(vchar_scanner)
        if isinstance(e, AssignmentExpression):
            assert vchar_scanner.is_empty(), "".join([v.char for v in vchar_scanner.remain()])

            # clear the pushed state at top of the loop
            vchar_scanner.clear_state()
            # clean the pushed state at top of the function
            vchar_scanner.clear_state()

            if modifier_list:
                e.add_modifiers(modifier_list)
            return e

        vchar_scanner.pop_state()

        # start over looking for export, etc.
        token = seek_word(vchar_scanner, directive)

        m = str(token)
        if m not in assignment_modifier:
            logger.debug("not an assignment statement at %r", pos)
            # restore scanner to state it was at start of function
            vchar_scanner.pop_state()
            return None

        logger.debug("assignment_modifier \"%m\" found", m)
        modifier_list.append(m)


