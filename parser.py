import logging

from whitespace import *
from error import *
from scanner import ScannerIterator
from symbol import Literal, Expression
import vline

_debug = True

logger = logging.getLogger("pymake.parser")

def parse_ifeq_directive(ifeq_expr, directive_str, viter, virt_line):
    logger.debug("parse_ifeq_directive() \"%s\" at pos=??",
            directive_str)

    # ifeq/ifneq 
    # Open => ( ' "
    # Argument => Expression
    # Comma => ,
    # Argument => Expression
    # Close => ) ' "
    #
    # More notes see ifeq.mk
    # GNU Make 4.3
    # ***************************
    #  leading spaces on 1st arg are preserved
    # trailing spaces on 1st arg are discarded
    #  leading spaces on 2nd arg are discarded
    # trailing spaces on 2nd arg are preserved
    # ***************************

    state_start = 0
#    state_open  = 1
    state_quote_expr = 2
    state_paren_expr1 = 3
#    state_comma = 4
    state_paren_expr2_start = 5
    state_paren_expr2 = 6
#    state_quote_expr2 = 7
    state_closed = 8

#    open_chars = ( "(", "'", '"' )
#    close_chars = ( ")", "'", '"' )
    quotes = ( "'", '"' )
    open_paren = '('
    close_paren = ')'
    comma = ','

    def kill_trailing_ws(token):
        idx = len(token)-1
        while idx >= 0 and token[idx].char in whitespace:
            token[idx].hide = True
            idx = idx - 1
        # allow chaining
        return token

#    def kill_leading_ws(token):
#        idx = 0
#        while idx < len(token) and token[idx].char in whitespace:
#            token[idx].hide = True
#            idx += 1
#        # allow chaining
#        return token

    def verify_close(open_vchar, close_vchar):
        oc = open_vchar.char
        cc = close_vchar.char

        if not ((oc == '(' and cc == ')')\
            or (oc == '"' and cc == '"') \
            or (oc == "'" and cc == "'")):
            # TODO nice error message
            raise ParseError(pos=open_vchar.get_pos(), 
                    description="invalid syntax in conditional; unbalanced open/close chars in %s" % directive_str)

    state = state_start
    expr1 = []
    expr2 = []
    curr_expr = None
    vchar_list = []

    # index into ifeq_expr.token_list[]
    ifeq_expr_token_idx = 0 

    # opening character of the expression's pair; need to match () or "" or ''
    open_vchar = None

    # we're using the same state to parse quoted expression so we need to make
    # sure we only see two quoted expressions.
    qexpr_counter = 0

    # viter is a vchar iterator into the incoming directive. If viter is not
    # None, we're already parsing a vline ("ifeq ..."). Otherwise, we know we
    # have an ifeq but now need to parse it (a nested conditional).
    if viter is None:
#        print("idx=%d token_list=%r" % (ifeq_expr_token_idx, ifeq_expr.token_list))
        tok = ifeq_expr.token_list[ifeq_expr_token_idx]
        # first token must be a literal open char
#        print("tok=%r string=%r" % (tok, tok.string))
        if isinstance(tok,Literal):
            viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
        else:
            raise ParseError(
                    pos = ifeq_expr.get_pos(),
                    description = "invalid syntax in conditional; %s missing opening ( or ' or \"" % directive_str
                )
        
    while True:
        try:
            vchar = next(viter)
        except StopIteration:
            vchar = None

        # In this giant first if block, we've run out of literal characters to
        # parse. We need to find the next Literal in the ifeq_expr so we can
        # parse for the internal expressions.
        if vchar is None:
#            print("vchar is None state=%d" % state)
            # we have run out literal chars so let's look for another one

            if vchar_list:
                # save any chars we've seen so far
                if curr_expr is None:
                    # we're not in a state where we should be saving characters
                    # so we've been saving garbage
                    raise DirectiveParseError()

#                print("save to curr_expr")
                curr_expr.append(Literal(vline.VCharString(vchar_list)))
                vchar_list = []

            while vchar is None:
                ifeq_expr_token_idx = ifeq_expr_token_idx + 1
                if ifeq_expr_token_idx >= len(ifeq_expr.token_list):
                    # we're done parsing
                    break
                tok = ifeq_expr.token_list[ifeq_expr_token_idx]
#                print("tok=", tok.makefile())
                if isinstance(tok,Literal):
                    viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
                    vchar = next(viter)
                else:
                    # Not a literal so just something for the new expression.
                    # Go back to token_list looking for another token
                    curr_expr.append(tok)

            if vchar is None:
                # we're done parsing
                break

#        print("parse %s c=\"%s\" at pos=%r state=%d" % (directive_str, vchar.char, vchar.get_pos(), state))

        if state == state_start:
            assert curr_expr is None
            # seeking Open, ignore whitespace
            if vchar.char in quotes:
#                print("found open quote")
                open_vchar = vchar
                state = state_quote_expr
                qexpr_counter = qexpr_counter + 1
                if qexpr_counter == 1:
                    curr_expr = expr1
                elif qexpr_counter == 2:
                    curr_expr = expr2
                else:
                    # too many expressions in our ifeq
                    # ifeq "expr1" "expr2" "expr3" <-- bad bad!
                    raise ParseError()

            elif vchar.char == open_paren:
#                print("found open paren")
                open_vchar = vchar
                state = state_paren_expr1
                curr_expr = expr1
                if qexpr_counter:
                    # started as a quoted expr but now we find a '('
                    # (we're re-using the quoted expression state)
                    raise ParseError()

            elif vchar.char not in whitespace:
                # Ignore whitespace but anything else is invalid.  
                # TODO need a nice error message
                raise ParseError(pos=vchar.get_pos(), description="invalid character")

        elif state == state_paren_expr1:
            if vchar.char == comma:
                # end of expr1
                # clean it up, make a new Literal
                # move to next state.
                if vchar_list:
                    #  leading spaces on 1st arg are preserved
                    # trailing spaces on 1st arg are discarded
                    expr1.append(Literal(vline.VCharString(kill_trailing_ws(vchar_list))))
                    vchar_list = []
                curr_expr = expr2
                state = state_paren_expr2_start
            else:
                vchar_list.append(vchar)

        elif state == state_paren_expr2_start:
            # start of expr2
            #  leading spaces on 2nd arg are discarded
            # trailing spaces on 2nd arg are preserved
            if vchar.char == close_paren:
                verify_close(open_vchar, vchar)
                if vchar_list:
                    expr2.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                state = state_closed
            elif vchar.char not in whitespace:
                # ignore leading whitespace; save everything else
                state = state_paren_expr2
                vchar_list.append(vchar)

        elif state == state_paren_expr2:
            #  leading spaces on 2nd arg are already discarded
            # trailing spaces on 2nd arg are preserved
            # seeking closing char
            if vchar.char == close_paren:
                verify_close(open_vchar, vchar)
                if vchar_list:
                    expr2.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                state = state_closed
            else:
                vchar_list.append(vchar)
                
        elif state == state_quote_expr:
            if vchar.char in quotes:
                # found a close quote
                verify_close(open_vchar, vchar)
                if vchar_list:
                    curr_expr.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                curr_expr = None
                # go back to start of state machine
                state = state_start
            else:
                vchar_list.append(vchar)
                
                
        elif state == state_closed:
            # anything but whitespace is an error
            if vchar.char not in whitespace:
                raise ParseError(
                        pos = virt_line.get_pos(),
                        description="extra text after 'ifeq' directive")

        else:
            # wtf???
            assert 0, state

#    print("expr1=",expr1)
#    print("expr2=",expr2)
    return (Expression(expr1), Expression(expr2))
