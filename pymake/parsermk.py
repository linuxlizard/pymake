# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com

import logging

from pymake.constants import *
from pymake.error import *
from pymake.symbolmk import *
from pymake.printable import printable_char
from pymake.scanner import ScannerIterator
import pymake.tokenizer as tokenizer
import pymake.vline as vline
from pymake.debug import *

_debug = False

logger = logging.getLogger("pymake.parser")
#logger.setLevel(level=logging.DEBUG)

# hack dependency injection
parse_vline_stream = None

# used by the tokenzparser to match a directive name with its class
conditional_directive_lut = {
  "ifdef" : IfdefDirective,
  "ifndef": IfndefDirective,
  "ifeq"  : IfeqDirective,
  "ifneq" : IfneqDirective 
}

include_directive_lut = {
    "include" : IncludeDirective,
    "-include" : MinusIncludeDirective,
    "sinclude" : SIncludeDirective
}

# test/debug fn for debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

def read_expression(vchar_scanner):
    # utility function to tokenize a string into a token_list then create an
    # Expression around it.
    # Will consume the rest of the line.
    # Created to capture the expression in ifdef and ifeq
    
    # ha ha type checking
    _ = vchar_scanner.remain

    token_list = tokenizer.tokenize_line(vchar_scanner)
    assert vchar_scanner.is_empty()
    if not token_list:
        raise ParseError("TODO")
    expr = Expression(token_list)
    return expr

def parse_ifeq_conditionals(ifeq_expr, directive_vstr):
    if not ifeq_expr.token_list:
        raise InvalidSyntaxInConditional(pos=directive_vstr.get_pos(), 
            moremsg="missing conditional expression")

    logger.debug("parse_ifeq_conditionals \"%s\" at %r", directive_vstr, ifeq_expr.get_pos())

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
    state_quote_expr = 1
    state_paren_expr1 = 2
    state_paren_expr2_start = 3
    state_paren_expr2 = 4
    state_closed = 5

    quotes = ( "'", '"' )

    # added some extra local debugging printf
    def kill_trailing_ws(token_list):
        if _debug:
            print("kill trailing whitespace")
        if token_list and token_list[-1].is_whitespace():
            token_list.pop()

    def verify_close(open_vchar, close_vchar):
        oc = open_vchar.char
        cc = close_vchar.char

        if not ((oc == '(' and cc == ')')\
            or (oc == '"' and cc == '"') \
            or (oc == "'" and cc == "'")):
            raise InvalidSyntaxInConditional(pos=open_vchar.get_pos(), 
                    moremsg="unbalanced open/close chars in %s" % directive_vstr)

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

    # counting for balanced parenthesis check
    paren_count = 0

    # need to prime the viter pump.
    if _debug:
        print("idx=%d token_list=%r" % (ifeq_expr_token_idx, ifeq_expr.token_list))
    tok = ifeq_expr.token_list[ifeq_expr_token_idx]

    if _debug:
        print("tok=%r string=%r" % (tok, tok.string))

    # first token must be a literal (one of the open chars)
    if isinstance(tok,Literal):
        viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
    else:
        raise InvalidSyntaxInConditional(
                pos = ifeq_expr.get_pos(),
                moremsg = "%s missing opening ( or ' or \"" % directive_vstr
            )

    while True:
        try:
            vchar = next(viter)
            # ha ha type checking
            vchar.pos
        except StopIteration:
            vchar = None

        if _debug and vchar:
            print("top vchar=>>%s<< at %r" %  (vchar.char, vchar.get_pos()))

        # In this giant first if block, we've run out of literal characters to
        # parse. We need to find the next Literal in the ifeq_expr so we can
        # parse for the internal expressions.
        if vchar is None:
            if _debug:
                print("vchar is None state=%d" % state)

            # we have run out literal chars so let's look for another one

            if vchar_list:
                # save any chars we've seen so far
                if _debug:
                    print("vchar_list=>>%s<<" % " ".join([str(v) for v in vchar_list]))
                    print("save to curr_expr")

                if curr_expr is None:
                    # we're not in a state where we should be saving characters
                    # so we've been saving garbage
                    # TODO error message
                    breakpoint()
                    raise ParseError()

                curr_expr.append(Literal(vline.VCharString(vchar_list)))
                if _debug:
                    print("curr_expr=>>%s<<" % "".join([t.makefile() for t in curr_expr]))
                vchar_list = []

            # Dig into the token_list to find the next Literal.
            # Anything not a Literal is saved.
            while vchar is None:
                ifeq_expr_token_idx = ifeq_expr_token_idx + 1
                if ifeq_expr_token_idx >= len(ifeq_expr.token_list):
                    # we're done parsing
                    break

                tok = ifeq_expr.token_list[ifeq_expr_token_idx]

                if _debug:
                    print("tok=%s %s" % (tok, tok.makefile()))

                if isinstance(tok,Literal):
                    # we'll start scanning inside this Literal string
                    viter = ScannerIterator(tok.string, tok.string.get_pos()[0])
                    vchar = next(viter)
                else:
                    # Not a literal so just something for the new expression.
                    # Go back to token_list looking for another token
                    if curr_expr is None:
                        raise InvalidSyntaxInConditional( pos=ifeq_expr.get_pos(),
                                    moremsg="missing opening (")
                    curr_expr.append(tok)

            if vchar is None:
                # we're done parsing
                break

        if _debug:
            print("parse %s c=\"%s\" at pos=%r pcount=%d state=%d" % (directive_vstr, vchar.char, vchar.get_pos(), paren_count, state))

        if state == state_start:
            assert curr_expr is None
            # seeking Open, ignore whitespace
            if vchar.char in quotes:
                if _debug:
                    print("found open quote")
                open_vchar = vchar
                state = state_quote_expr
                qexpr_counter = qexpr_counter + 1
                if qexpr_counter == 1:
                    curr_expr = expr1
                elif qexpr_counter == 2:
                    curr_expr = expr2
                else:
                    breakpoint()
                    # should not get here
                    assert 0
                    # too many expressions in our ifeq
                    # ifeq "expr1" "expr2" "expr3" <-- bad bad!
                    # TODO better error message
                    raise ParseError()

            elif vchar.char == '(':
                if _debug:
                    print("found open paren")
                open_vchar = vchar
                state = state_paren_expr1
                curr_expr = expr1
                if qexpr_counter:
                    breakpoint()
                    # started as a quoted expr but now we find a '('
                    # (we're re-using the quoted expression state)
                    # TODO better error message
                    raise ParseError()

            elif vchar.char not in whitespace:
                # Ignore whitespace but anything else is invalid.  
                # TODO need a nice error message
                raise InvalidSyntaxInConditional(pos=vchar.get_pos(), 
                        moremsg="invalid character %r at %r" % (vchar.char, vchar.get_pos()))

        elif state == state_paren_expr1:
            if vchar.char == ',':
                if _debug:
                    print("found comma at pos=%r ∴ end of expr1" % (vchar.get_pos(),))
                # end of expr1
                # clean it up, make a new Literal
                # move to next state.

                if vchar_list:
                    #  leading spaces on 1st arg are preserved
                    # trailing spaces on 1st arg are discarded
                    expr1.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                # trailing ws on 1st arg are discarded
                kill_trailing_ws(expr1)
                curr_expr = expr2
                state = state_paren_expr2_start
            elif vchar.char == '(':
                paren_count += 1
                vchar_list.append(vchar)
            elif vchar.char == ')':
                if paren_count == 0:
                    raise InvalidSyntaxInConditional(pos=vchar.get_pos(), 
                            moremsg="unbalanced parenthesis in first expression")
                paren_count -= 1
                vchar_list.append(vchar)
            else:
                vchar_list.append(vchar)

        elif state == state_paren_expr2_start:
            if paren_count != 0:
                raise InvalidSyntaxInConditional(pos=vchar.get_pos(), 
                        moremsg="unbalanced parenthesis in first expression")
                
            # start of expr2
            #  leading spaces on 2nd arg are discarded
            # trailing spaces on 2nd arg are preserved
            if vchar.char == ')':
                verify_close(open_vchar, vchar)
                if vchar_list:
                    expr2.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                state = state_closed

            elif vchar.char not in whitespace:
                # ignore leading whitespace; save everything else
                if vchar.char == '(':
                    paren_count += 1
                state = state_paren_expr2
                vchar_list.append(vchar)

        elif state == state_paren_expr2:
            #  leading spaces on 2nd arg are already discarded
            # trailing spaces on 2nd arg are preserved
            # seeking closing char
            if vchar.char == ')':
                if paren_count == 0:
                    verify_close(open_vchar, vchar)
                    if vchar_list:
                        expr2.append(Literal(vline.VCharString(vchar_list)))
                        vchar_list = []
                    state = state_closed
                else:
                    paren_count -= 1
                    vchar_list.append(vchar)
            elif vchar.char == '(':
                paren_count += 1
                vchar_list.append(vchar)
            else:
                vchar_list.append(vchar)
                
        elif state == state_quote_expr:
            if vchar.char in quotes:
                # found a close quote
                if _debug:
                    print("found close quote")
                verify_close(open_vchar, vchar)
                if vchar_list:
                    curr_expr.append(Literal(vline.VCharString(vchar_list)))
                    vchar_list = []
                curr_expr = None
                # go back to start of state machine
                if qexpr_counter == 2:
                    state = state_closed
                else:
                    state = state_start
            else:
                vchar_list.append(vchar)
                
                
        elif state == state_closed:
            # anything but whitespace is a stern warning
            if vchar.char not in whitespace:
                # GNU Make prints a warning then ignores the rest of the line.
                warning_message(
                        pos = vchar.get_pos(),
                        msg="extraneous text after '%s' directive" % directive_vstr)
                # leave the state machine, ignoring rest of line
                break

        else:
            # wtf???
            assert 0, state

        # save the last char we looked at so we can report errors
        prev_vchar = vchar
    # end of while True around the state machine

    if state != state_closed:
        if state == state_paren_expr2_start:
            raise InvalidSyntaxInConditional( pos=prev_vchar.get_pos(),
                        moremsg="missing closing )")
        elif state == state_quote_expr:
            raise InvalidSyntaxInConditional( pos=prev_vchar.get_pos(),
                        moremsg="missing closing quote")
        else:
            # TODO can we find good error messages for other closing conditions?
            raise InvalidSyntaxInConditional( pos=prev_vchar.get_pos(), 
                    moremsg="???")

    if _debug:
        print("expr1=",Expression(expr1))
        print("expr2=",Expression(expr2))

    return (Expression(expr1), Expression(expr2))


def parse_ifeq_directive(directive_vstr, vchar_scanner, vline_iter):
    logger.debug("parse_ifeq_directive() \"%s\" at pos=%r",
            directive_vstr, directive_vstr.get_pos())

    # ha ha type checking
    _ = vchar_scanner.remain

    expr = read_expression(vchar_scanner)

    expr1,expr2 = parse_ifeq_conditionals(expr, directive_vstr)

    dir_str = str(directive_vstr)
    assert dir_str in ("ifeq","ifneq"), dir_str
    dir_ = conditional_directive_lut[dir_str](directive_vstr, expr1, expr2)

    cond_block = handle_conditional_directive(dir_, vline_iter)
    return cond_block


def parse_ifdef_directive(directive_vstr, vchar_scanner, vline_iter ):
    logger.debug("parse_ifdef_directive() \"%s\" at pos=%r",
            directive_vstr, directive_vstr.get_pos())

    # ha ha type checking
    _ = vchar_scanner.remain

    expr = read_expression(vchar_scanner)

    dir_str = str(directive_vstr)

    assert dir_str in ("ifdef","ifndef"), dir_str
    dir_ = conditional_directive_lut[dir_str](directive_vstr, expr)

    cond_block = handle_conditional_directive(dir_, vline_iter)
    return cond_block


def parse_define_block(expr, virt_line, vline_iter ):
    # save where this define block begins so we can report errors about 
    # missing enddef 
    starting_pos = expr.get_pos()
    assert isinstance(expr, DefineDirective)

    # array of VirtualLine
    vline_list = []

    # Supports nested blocks.
    # GNU make supports nesting define/endef. For example:
    # define outer
    # define inner
    # endef
    # endef

    depth = 1

    for virt_line in vline_iter : 
        # search for endef or a nested define
        viter = iter(virt_line)
        token = tokenizer.seek_word(viter, {"endef","define"})
        if token:
            s = str(token)
            # we found 'endef'
            if s == "endef":
                depth -= 1
                assert depth >= 0
                if depth == 0:
                    # final endef; we're done 
                    if viter.remain():
                        # report leftover grunge
                        warning_message(pos=virt_line.starting_pos,
                            msg="extraneous text after 'endef' directive")
                    break
            elif s == "define":
                depth += 1
            else:
                assert 0, s

        vline_list.append(virt_line)
    else :
        raise ParseError(pos=starting_pos, msg="missing endef")

    block = DefineBlock(vline_list)
    expr.add_block(block)
    return expr


#def parse_undefine_directive(expr, directive_vstr, *ignore):
#    # TODO check for validity of expr (space in literals I suppose?)
#    return UnDefineDirective(directive_vstr, expr)

#def parse_override_directive(expr, directive_vstr, virt_line, vline_iter ):
#    # TODO any validity checks I need to do here? (Probably)
#    raise NotImplementedError(directive_vstr)

def parse_include_directive(expr, directive_vstr, *ignore):
    # TODO any validity checks I need to do here? (Probably)
    dir_str = str(directive_vstr)
    
    klass = include_directive_lut[dir_str]

    # note we're passing in the parse function
    return klass(directive_vstr, expr)

def handle_conditional_directive(directive_inst, vline_iter):
    # GNU make doesn't parse the stuff inside the conditional unless the
    # conditional expression evaluates to True. But Make does allow nested
    # conditionals. Read line by line, looking for nested conditional
    # directives
    #
    # directive_inst - an instance of DirectiveExpression
    # vline_iter - <generator> across VirtualLine instances (does NOT support
    #               pushback)
    #
    # vline_iter is from get_vline() and reads from line_scanner underneath.
    #
    # Big fat note! In GNU Make, nested directives are only parsed when the
    # surrounding directive tests True. In the following example, G-Make won't
    # complain about the bad (internal) directive unless $a,$b evaluates True.
    # Otherwise, the ifeq is detected as a conditional directive (else/endif
    # rules are enforced) but not parsed
    #
    # ifeq ($a,$b)
    #     ifeq ($b,$c foo bar baz  
    #                ^^^^^--------- "invalid syntax in conditional"
    #
    # This creates a problem for me because I was thinking I could tokenize
    # the entire makefile assuming correct syntax OR raise a syntax error.
    # Unfortunately, invalid syntax is now detected at eval-time. My bad. 

    logger.debug("handle_conditional_directive \"%s\" at %r", directive_inst, directive_inst.get_pos())

    # ha ha type checking
    assert isinstance(directive_inst,ConditionalDirective), type(directive_inst)

    state_if = 1
    state_else = 3
    state_endif = 4

    state = state_if

    # Gather file lines; will be VirtualLine instances.
    # Passed to LineBlock constructor.
    line_list = []

    cond_block = ConditionalBlock()
    cond_block.add_conditional( directive_inst )

    def make_conditional(dir_str, directive_vstr, expr1=None, expr2=None):
        klass = conditional_directive_lut[dir_str]
        if dir_str in ("ifeq", "ifneq"):
            # two expressions (not yet parsed)
            dir_ = klass(directive_vstr, expr1, expr2 )
        elif dir_str in ("ifdef", "ifndef"):
            # one expression (not yet parsed)
            dir_ = klass(directive_vstr, expr1)
        else:
            # wtf?
            assert 0, dir_str

        return dir_

    def save_block(line_list):
        if len(line_list) :
            cond_block.add_block( LineBlock(line_list) )
        return []

    # save where this directive block begins so we can report errors about big
    # if/else/endif problems (such as missing endif)
    starting_pos = directive_inst.get_pos()

    for virt_line in vline_iter : 
#        print("h state={0}".format(state))
#        print("={0}".format(str(virt_line)), end="")

        vchar_scanner = iter(virt_line)

        # first check if this is an assignment statement
        # (mimic exactly what GNU Make eval() does)
        # need to do this first to catch stuff like
        # ifdef:=12345 
        stmt = tokenizer.tokenize_assignment_statement(vchar_scanner)
        if stmt:
            # found an assignment
            line_list.append(virt_line)
            continue

        # search for nested directive 

        directive_vstr = tokenizer.seek_directive(vchar_scanner, conditional_directive)

        if directive_vstr is None:
            # not another conditional, just plain normal everyday "something"
            # save the line into the block
            line_list.append(virt_line)
            continue

        # we found something that's a conditional directive
        dir_str = str(directive_vstr)

        if dir_str in conditional_open : 
            # save the block of stuff we've read
            line_list = save_block(line_list)

            # At this point we have a nested conditional.  Can't parse the new
            # conditional expression yet because it could be garbage that won't
            # ever be interpreted because it's inside a negative branch of
            # another conditional.

            d = make_conditional(dir_str, directive_vstr)
            d.partial_init( vline.VCharString(vchar_scanner.remain()) )
            # recursive function is recursive
            sub_block = handle_conditional_directive(d, vline_iter)
            cond_block.add_block( sub_block )
            
        elif dir_str=="else" : 
            if state==state_else : 
                errmsg = "too many else"
                raise ParseError(vline=virt_line, pos=virt_line.get_pos(),
                            description=errmsg)

            # save the block of stuff we've read
            line_list = save_block(line_list)

            # handle "else ifCOND"

            # look for a following conditional directive
            directive_vstr = seek_word(vchar_scanner, seek=conditional_open)
            if directive_vstr: 
                # found an "else ifsomething"
                dir_str = str(directive_vstr)

                expression = read_expression(vchar_scanner)

                if dir_str in ("ifeq", "ifneq"):
                    # parse the conditional Expression, making two new Expressions
                    assert vchar_scanner.is_empty(), vchar_scanner.remain()[0].get_pos()
                    expr1,expr2 = parse_ifeq_conditionals(expression, directive_vstr)
                    dir_ = make_conditional(dir_str, directive_vstr, expr1, expr2)
                else:
                    dir_ = make_conditional(dir_str, directive_vstr, expression)

                cond_block.add_conditional( dir_ )
            else : 
                # Just the else case. Must be the last conditional we see.
                cond_block.start_else()
                state = state_else 

        elif dir_str=="endif":
            # save the block of stuff we've read
            line_list = save_block(line_list)
            state = state_endif

        else : 
            # we found stuff to be parsed later
            line_list.append(virt_line)

        if state==state_endif : 
            # close the if/else/endif collection
            break

    # did we hit bottom of file before finding our end?
    if state != state_endif :
        errmsg = "missing endif"
        raise ParseError(pos=starting_pos, msg=errmsg)
    
    return cond_block

def parse_export_directive(expr, directive_vstr, *ignore):
    dir_str = str(directive_vstr)
    if dir_str == "export":
        klass = ExportDirective
    elif dir_str == "unexport":
        klass = UnExportDirective
    else:
        assert 0, dir_str

    # "If you want all variables to be exported by default, you can use export by itself"
    # We have nothing left to parse so a bare export/unexport
    if not expr.token_list:
        return klass(directive_vstr)

    return klass(directive_vstr, expr)

def error_extraneous(expr, directive_str, virt_line, vline_iter):
    starting_pos = virt_line.get_pos()
    errmsg = "extraneous '%s'" % directive_str
    raise ParseError(pos=starting_pos, msg=errmsg)

def parse_directive(directive_vstr, virt_line, vline_iter):
    # directive_str - python string indicating which directive we found at the
    #       start of the Expression token_list[0] 
    #
    # vchar_scanner - the a virtual line scanner positioned after the directive
    #
    # vline_iter - virtualline iterator across the input; need this to make
    #       LineBlock et al for contents of the ifdef/ifeq directives
    #
    logger.debug("parse_directive() \"%s\" at pos=%r",
            directive_vstr, virt_line.get_pos())

    # ha ha type checking
    _ = virt_line.remain

    lut = {
        "ifeq" : parse_ifeq_directive,
        "ifneq" : parse_ifeq_directive,
        "ifdef" : parse_ifdef_directive,
        "ifndef" : parse_ifdef_directive,
        "define" : parse_define_directive,
#        "export" : parse_export_directive,
#        "unexport" : parse_export_directive,
        "endif" : error_extraneous,
#        "undefine" : parse_undefine_directive,
#        "override" : parse_override_directive,
        "include" : parse_include_directive,
        "-include" : parse_include_directive,
        "sinclude" : parse_include_directive,
    }

    return lut[str(directive_vstr)](directive_vstr, virt_line, vline_iter)

def parse_expression(expr, virt_line, vline_iter):
    # davep 20241123 ; obsolete 
    assert 0, "TODO"

    # This is a second pass through an Expression.
    # An Expression could be something like:
    #   $(info blah blah)  # fn call ; most are invalid in standalone context
    #   export 
    #   export something
    #   define foo   # start of multi-line variable

    logger.debug("parse %s", expr.__class__.__name__)
#    if get_line_number(expr) > 151:
#        breakpoint()
    assert isinstance(expr,Expression), type(expr)

    # If we do find a directive, we'll wind up re-parsing the entire line as a
    # directive. Unnecessary and ugly but I first tried to handle directives
    # before assignment and rules which didn't work (too much confusion in
    # handling the case of directive names as as rule or assignments). So I'm
    # parsing the line first, determining if it's a rule or statement or
    # expression. If expression, look for a directive string, then connect
    # to the original Directive handling code here.

    assign_expr = None
    if isinstance(expr, AssignmentExpression):
        # weird case showing GNU Make's lack of reserved words and the
        # sloppiness of my grammar tokenparser.  
        # define xyzzy :=    <-- multi-line variable masquerading as an Assignment
        # ifdef := 123  <-- totally legal but I want to throw a warning
        # export CC=gcc  <-- looks like an assignment
        # Need to dig into the assignment to get the LHS.
        assign_expr = expr
        expr = expr.token_list[0]
    
    # We're only interested in Directives at this point. A Directive will be
    # inside string Literal. 
    #
    # Leave anything else alone. Invalid context function calls will error out
    # during execute().  For example,  $(subst ...) alone on a line will error
    # with "*** missing separator. Stop."

    # If the first token isn't a Literal, we're done.
    tok = expr.token_list[0]
    if not isinstance(tok, Literal):
        return assign_expr if assign_expr else expr

    # seek_directive() needs a character iterator 
    viter = ScannerIterator(tok.string, tok.string.get_pos()[0])

    # peek at the first character of the line. If it's a <tab> aka recipeprefix then 
    # WOW does our life get complicated.  GNU Make allows directives (with a
    # couple exceptions) to be recipeprefix'd. 
    # TODO not handling recipeprefix yet
    first_vchar = viter.lookahead()

    directive_vstr = seek_directive(viter)
    if not directive_vstr:
        # nope, not a directive. Ignore this expression and let execute figure it out
        return assign_expr if assign_expr else expr

    # at this point, we definitely have some sort of directive.
    assert viter.is_empty()

    # delete the whitespace token after the directive if it exists
    if len(expr.token_list) > 1 and expr.token_list[1].is_whitespace():
        del expr.token_list[1]
        
    dir_str = str(directive_vstr)

    if assign_expr:
        # If we've peeked into an assignment and decided this is re-using a
        # directive name as an assign, throw a warning about using directive
        # name in a weird context.
        #
        # yet another corner case of totally legit directive syntax:
        # define = foo
        # define = <nothing>
        # export CC=gcc
        # override CC=xcc
        # override define foo=

        if dir_str in ("define", "export", "override") and len(expr.token_list) > 1:
            # These directives can validly be an assignment so parse them as
            # a directive.  The len() above checks that there's multiple
            # symbols on the LHS before the assignment operator.

            # extract the directive from the expression
            # We want to throw away the first Literal containing the directive
            # expr is a ref into assign_expr.token_list[0]
            # so I should be able to delete expr.token_list[0] and kill the directive literal
            assert assign_expr.token_list[0].token_list[0] is expr.token_list[0]

            del expr.token_list[0]

            dir_ = parse_directive(assign_expr, directive_vstr, virt_line, vline_iter)
        else:
            # GNU Make doesn't warn like this (pats self on back).
            logger.warning("re-using a directive name \"%s\" in an assignment at %r", dir_str, assign_expr.get_pos())
            return assign_expr
    else:
        # extract the directive from the expression
        # We want to throw away the first Literal containing the directive
        del expr.token_list[0] 

        dir_ = parse_directive(expr, directive_vstr, virt_line, vline_iter)

#    print("parse directive=%s" % dir_.makefile())
    return dir_

def parse_rule(vchar_scanner):
    lhs = tokenizer.tokenize_rule(vchar_scanner)
    if lhs is None:
        assert vchar_scanner.is_starting()
        return None

    targets, rule_op = lhs

    # ha ha type checking
    assert isinstance(targets,list), (type(targets),)

    rhs = tokenizer.tokenize_rule_RHS(vchar_scanner)

    if vchar_scanner.remain():
        # if we have anything left, it must be a recipe after the ';'
        vchar = vchar_scanner.lookahead()
        assert vchar.char == ';', vchar.char

    statement = [ TargetList(targets), rule_op, rhs ]

    # don't look for recipe(s) yet
    return RuleExpression(statement) 

