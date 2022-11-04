import logging

from whitespace import *
from error import *
from scanner import ScannerIterator
from symbol import Literal, Expression
import vline

_debug = True

logger = logging.getLogger("pymake.parser")

def parse_ifeq_directive(expr, directive_str, viter, virt_line):
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
    state_open  = 1
    state_paren_expr1 = 2
    state_quote_expr1 = 3
    state_comma = 4
    state_paren_expr2_start = 5
    state_paren_expr2 = 6
    state_quote_expr2 = 7
    state_closed = 8

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

        return (oc == '(' and cc == ')')\
            or (oc == '"' and cc == '"') \
            or (oc == "'" and cc == "'")

    state = state_start
    expr1 = []
    expr2 = []

    expr_token_idx = 0 # index into expr.token_list[]

    vchar_list = []

    open_chars = ( "(", "'", '"' )
    close_chars = ( ")", "'", '"' )
    open_vchar = None
    comma = ','

    # viter is vchar iterator into the incoming directive. If viter is not
    # None, we're already parsing a vline ("ifeq ..."). Otherwise, we know we
    # have an ifeq but now need to parse it (a nested conditional).
    #
    if viter is None:
        print("idx=%d token_list=%r" % (expr_token_idx, expr.token_list))
        tok = expr.token_list[expr_token_idx]
        # first token must be a literal open char
        print("tok=%r string=%r" % (tok, tok.string))
        if isinstance(tok,Literal):
            viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
        else:
            raise ParseError(
                    pos = expr.get_pos(),
                    description = "invalid syntax in conditional; %s missing opening ( or ' or \"" % directive_str
                )

        
    while True:
        try:
            vchar = next(viter)
        except StopIteration:
            vchar = None

        if vchar is None:
            print("vchar is None state=%d" % state)
            # we have run out literal chars so let's look for another one
            expr_token_idx = expr_token_idx + 1
            if expr_token_idx >= len(expr.token_list):
                # we're done parsing
                break
            tok = expr.token_list[expr_token_idx]
            print("tok=", tok.makefile())
            if isinstance(tok,Literal):
                viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
            else:
                # not a literal so just something for the new expression
                if state == state_paren_expr1:
                    if vchar_list:
                        # save any chars we've seen so far
                        expr1.append(Literal(vline.VCharString(vchar_list)))
                        vchar_list = []
                    print("save to expr1")
                    expr1.append(tok)
                elif state == state_paren_expr2_start or state == state_paren_expr2:
                    if vchar_list:
                        # save any chars we've seen so far
                        expr2.append(Literal(vline.VCharString(vchar_list)))
                        vchar_list = []
                    print("save to expr2")
                    expr2.append(tok)
                else:
                    breakpoint()
                    # TODO need a good error message
                    raise ParseError()
#                            pos = virt_line.get_pos()[1],
#                            vline=virt_line,
#                            description="extra text after 'ifeq' directive")
#                    
            # fry fry a hen
            continue

        print("parse %s c=\"%s\" at pos=%r state=%d" % (directive_str, vchar.char, vchar.get_pos(), state))

        if state == state_start:
            # seeking Open, ignore whitespace
            if vchar.char in open_chars:
                print("found open")
                # save which char we saw so can match it at the close
                open_vchar = vchar
                if vchar.char == '(':
                    state = state_paren_expr1
                else:
                    state = state_quote_expr1
            elif vchar.char in whitespace:
                # ignore
                pass
            else:
                # invalid!  # TODO need a nice error message
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
                state = state_paren_expr2_start
            else:
                vchar_list.append(vchar)

        elif state == state_paren_expr2_start:
            # start of expr2
            #  leading spaces on 2nd arg are discarded
            # trailing spaces on 2nd arg are preserved
            if vchar.char == ')':
                if not verify_close(open_vchar, vchar):
                    # TODO nice error message
                    raise ParseError(pos=open_vchar.get_pos(), 
                            description="invalid syntax in conditional; unbalanced open/close chars in %s" % directive_str)
                if vchar_list:
                    expr2.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                state = state_closed
            elif vchar.char in whitespace:
                pass
            else:
                state = state_paren_expr2
                vchar_list.append(vchar)

        elif state == state_paren_expr2:
            #  leading spaces on 2nd arg are already discarded
            # trailing spaces on 2nd arg are preserved
            # seeking closing char
            if vchar.char == ')':
                verify_close(open_vchar, vchar)
                if vchar_list:
                    expr2.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                state = state_closed
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

    print("expr1=",expr1)
    print("expr2=",expr2)
    return (Expression(expr1), Expression(expr2))
