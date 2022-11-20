import logging

from constants import *
from error import *
from symbol import *
from scanner import ScannerIterator
from tokenizer import tokenize_recipe
import vline

_debug = True

logger = logging.getLogger("pymake.parser")

# used by the tokenzparser to match a directive name with its class
conditional_directive_lut = {
  "ifdef" : IfdefDirective,
  "ifndef": IfndefDirective,
  "ifeq"  : IfeqDirective,
  "ifneq" : IfneqDirective 
}

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


def handle_define_directive(define_inst, vline_iter):

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

def parse_ifeq_conditionals(ifeq_expr, directive_str, viter):
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
    state_quote_expr = 1
    state_paren_expr1 = 2
    state_paren_expr2_start = 3
    state_paren_expr2 = 4
    state_closed = 5

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
        print("idx=%d token_list=%r" % (ifeq_expr_token_idx, ifeq_expr.token_list))
        tok = ifeq_expr.token_list[ifeq_expr_token_idx]
        # first token must be a literal open char
        print("tok=%r string=%r" % (tok, tok.string))
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
            print("vchar is None state=%d" % state)
            # we have run out literal chars so let's look for another one

            if vchar_list:
                # save any chars we've seen so far
                if curr_expr is None:
                    # we're not in a state where we should be saving characters
                    # so we've been saving garbage
                    # TODO error message
                    raise ParseError()

#                print("save to curr_expr")
                curr_expr.append(Literal(vline.VCharString(vchar_list)))
                vchar_list = []

            while vchar is None:
                ifeq_expr_token_idx = ifeq_expr_token_idx + 1
                if ifeq_expr_token_idx >= len(ifeq_expr.token_list):
                    # we're done parsing
                    break
                tok = ifeq_expr.token_list[ifeq_expr_token_idx]
                print("tok=", tok.makefile())
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

        print("parse %s c=\"%s\" at pos=%r state=%d" % (directive_str, vchar.char, vchar.get_pos(), state))

        if state == state_start:
            assert curr_expr is None
            # seeking Open, ignore whitespace
            if vchar.char in quotes:
                print("found open quote")
                open_vchar = vchar
                state = state_quote_expr
                qexpr_counter = qexpr_counter + 1
                if qexpr_counter == 1:
                    curr_expr = expr1
                elif qexpr_counter == 2:
                    curr_expr = expr2
                else:
                    # should not get here
                    assert 0
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
                        msg="extraneous text after '%s' directive" % directive_str)
                # leave the state machine, ignoring rest of line
                break

        else:
            # wtf???
            assert 0, state

        prev_vchar = vchar
    # end of while True around the state machine

    if state != state_closed:
        if state == state_paren_expr2_start:
            raise ParseError( pos=prev_vchar.get_pos(),
                        description="invalid syntax in conditional; missing closing )")
        elif state == state_quote_expr:
            raise ParseError( pos=prev_vchar.get_pos(),
                        description="invalid syntax in conditional; missing closing quote")
        else:
            # TODO can we find good error messages for other closing conditions?
            raise ParseError( pos=prev_vchar.get_pos(),
                        description="invalid syntax in conditional")

#    print("expr1=",expr1)
#    print("expr2=",expr2)
    return (Expression(expr1), Expression(expr2))


def parse_ifeq_directive(expr, directive_str, viter, virt_line, vline_iter):
    logger.debug("parse_ifeq_directive() \"%s\" at pos=%r",
            directive_str, virt_line.starting_pos)

    expr1,expr2 = parse_ifeq_conditionals(expr, directive_str, viter)

    if directive_str == "ifeq":
        dir_ = IfeqDirective(expr1, expr2)
    else:
        dir_ = IfneqDirective(expr1, expr2)

    cond_block = handle_conditional_directive(dir_, vline_iter)
    return cond_block


def parse_ifdef_directive(expr, directive_str, viter, virt_line, vline_iter ):
    # arguments same as parse_directive
    raise NotImplementedError(directive_str)


def parse_define_directive(expr, directive_str, viter, virt_line, vline_iter ):
    # arguments same as parse_directive
    raise NotImplementedError(directive_str)

def seek_directive(viter, seek=directive):
    # viter - character iterator
    assert isinstance(viter, ScannerIterator), type(viter)

    logger.debug("seek_directive")

    if not len(viter.remain()):
        # nothing to parse so nothing to find
        return None

    # we're looking ahead to see if we have a directive inside our set 'seek'
    # so we need to save the state; we'll restore it on return if we haven't
    # found a directive.
    viter.push_state()

    # Consume leading whitespace; throw a fit if first char is the recipeprefix.
    # We never call this fn for a recipe so we know there's a confusing parse
    # ahead of us if we see a recipeprefix as first char.
    s = ""

    # look at first char first
    vchar = next(viter)
    if vchar.char == recipe_prefix:
        # TODO need to mimic how GNU Make handles an ambiguous recipe char
        raise NotImplementedError(vchar.get_pos())

    state_whitespace = 1  # ignore leading whitespace
    state_char = 2

    if vchar.char in whitespace:
        state = state_whitespace
    else:
        state = state_char
        s += vchar.char
#    print("seek_directive c={0} state={1}".format(printable_char(vchar.char), state))

    for vchar in viter:
        # continue to ignore leading whitespace
#        print("seek_directive c={0} state={1} pos={2}".format(printable_char(vchar.char), state, vchar.get_pos()))
        if state == state_whitespace:
            if vchar.char in whitespace:
                continue
            state = state_char

        if state == state_char:
            if vchar.char not in directive_chars:
                # we've found something that's not part of a directive word so
                # pppfffttt we're done
                viter.pop_state()
                return None

            s += vchar.char
            if s in seek:
                # we have a substring match
                break
    else:
        # end of string w/o seeing a directive so nothing to see here
        viter.pop_state()
        return None

    # we've found at least a substring match; next char might be whitespace or EOL
    try:
        vchar = next(viter)        
    except StopIteration:
        # bare string matching a directive which is weird
        pass
    else:
        if vchar.char not in whitespace and vchar.char not in eol:
            # we found a substring e.g. "definefoo" which is not what we want
            viter.pop_state()
            return None

    # success!
    logger.debug("seek_directive found \"%s\"", s)
    return s


def handle_conditional_directive(directive_inst, vline_iter):
    # GNU make doesn't parse the stuff inside the conditional unless the
    # conditional expression evaluates to True. But Make does allow nested
    # conditionals. Read line by line, looking for nested conditional
    # directives
    #
    # directive_inst - an instance of DirectiveExpression
    # vline_iter - <generator>across VirtualLine instances (does NOT support
    #               pushback)
    #
    # vline_iter is from get_vline() and reads from line_scanner underneath.
    #
    # Big fate note! In GNU Make, nested directives are only parsed when the
    # surrounding directive tests True. In the following example, G-Make won't
    # complain about the bad (internal) directive unless $a,$b evaluates True.
    # Otherwise, the ifeq is detected as a conditional directive (else/endif
    # rules are enforced) but not parsed
    #
    # ifeq ($a,$b)
    #     ifeq ($b,$c foo bar baz  
    #                ^^^^^--------- "invalid syntax in conditional"
    #
    # This creates a problem for us because we were thinking we could tokenize
    # the entire makefile assuming correct syntax OR raise a syntax error.
    # Unfortunately, invalid syntax is now detected at run-time. My bad. 

    logger.debug("handle_conditional_directive \"%s\"", directive_inst)

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

    # Pass in the tokenize() fn because will eventually need to parse the
    # contents of the block. Sending in the fn because the circular references
    # between pymake.py and symbol.py make calling tokenize from
    # ConditionalBlock impossible. A genuine fancy-pants dependency injection!
    cond_block = ConditionalBlock(tokenize)
    cond_block.add_conditional( directive_inst )

    def save_block(line_list):
        if len(line_list) :
            cond_block.add_block( LineBlock(line_list) )
        return []

    # save where this directive block begins so we can report errors about big
    # if/else/endif problems (such as missing endif)
#    starting_pos = directive_inst.code.starting_pos

    for virt_line in vline_iter : 
#        print("c state={0}".format(state))
#        print("={0}".format(str(virt_line)), end="")

        # search for nested directive in the physical line (consolidates the
        # line continuations)
        # directive is the first substring surrounded by whitespace
        # or None if substring is not a directive

        viter = iter(virt_line)
        directive_str = seek_directive(viter)

        if directive_str in conditional_directive : 
            # save the block of stuff we've read
            line_list = save_block(line_list)

#            breakpoint()
            # recursive function is recursive
            dir_ = conditional_directive_lut[directive_str](None, None )
            dir_.partial_init( vline.VCharString(viter.remain()) )
            sub_block = handle_conditional_directive(dir_, vline_iter)
#            sub_block = tokenize_directive(directive_str, viter, virt_line, vline_iter)
            cond_block.add_block( sub_block )
            
        elif directive_str=="else" : 
            if state==state_else : 
                errmsg = "too many else"
                raise ParseError(vline=virt_line, pos=virt_line.starting_pos(),
                            description=errmsg)

            # save the block of stuff we've read
            line_list = save_block(line_list)

#            print("phys_line={0}".format(printable_string(phys_line)))

            # handle "else ifCOND"

            # look for a following conditional directive
            directive_str = seek_directive(viter, conditional_directive)
            if directive_str : 
                # found an "else ifsomething"
                raise NotImplementedError # replace with new vcstring constructor
                expression = tokenize_assign_RHS(viter)
                directive_inst = conditional_directive_lut[directive_str](expression)
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
def parse_directive(expr, directive_str, viter, virt_line, vline_iter):
    # expr - Expression instance
    #       We've started to consume token_list[0] which is a Literal containing the name of the directive 
    #       (ifdef, ifeq, etc). The directive_str and viter come from token_list[0]
    # directive_str - python string indicating which directive we found at the start of the Expression token_list[0]
    # viter - scanneriterator across the rest of the Literal that started the Expression's token_list[0]
    # virt_line - the entire directive as a virtual line (XXX do I need this? probably not)
    # vline_iter - virtualline iterator across the input; need this to make
    #              LineBlock et al for contents of the ifdef/ifeq directives
    #
    logger.debug("parse_directive() \"%s\" at pos=%r",
            directive_str, virt_line.starting_pos)

    lut = {
        "ifeq" : parse_ifeq_directive,
        "ifneq" : parse_ifeq_directive,
        "ifdef" : parse_ifdef_directive,
        "ifndef" : parse_ifdef_directive,
        "define" : parse_define_directive,
    }

    return lut[directive_str](expr, directive_str, viter, virt_line, vline_iter)

def parse_expression(expr, virt_line, vline_iter):
    # This is a second pass through an Expression.
    # An Expression could be something like:
    #   $(info blah blah)  # fn call ; most are invalid in standalone context
    #   export 
    #   export something
    #   define foo   # start of multi-line variable
#    breakpoint()

    assert isinstance(expr,Expression), type(expr)

    # If we do find a directive, we'll wind up re-parsing the entire line as a
    # directive. Unnecessary and ugly but I first tried to handle directives
    # before assignment and rules which didn't work (too much confusion in
    # handling the case of directive names as as rule or assignments). So I'm
    # parsing the line first, determining if it's a rule or staement or
    # expression. If expression, look for a directive string, then connect
    # to the original Directive handling code here.

    assign_expr = None
    if isinstance(expr, AssignmentExpression):
        # weird case showing GNU Make's lack of reserved words and the
        # sloppiness of my grammar tokenparser.  
        # define xyzzy :=    <-- multi-line variable masquerading as an Assignment
        # ifdef := 123  <-- totally legal but I want to throw a warning
        # dig into the assignment to get the LHS
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
    directive_str = seek_directive(viter)
    if not directive_str:
        # nope, not a directive. Ignore this expression and let execute figure it out
        return assign_expr if assign_expr else expr

    # at this point, we definitely have some sort of directive.

    if assign_expr:
        # If we've peeked into an assignment and decided this is re-using a
        # directive name as an assign, throw a warning about using directive
        # name in a weird context.
        #
        # yet another corner case:
        # define = foo        <-- totally legit
        # define = <nothing>  <-- totally legit
        # I'm growing weary of finding all these corner cases. I need to
        # rewrite my tokenize/parser with these sort of things in mind.
        if directive_str == "define" and viter.remain():
            # at this point, we have something after the "define" so probably
            # an actual factual directive.
            dir_ = parse_directive(assign_expr, directive_str, viter, virt_line, vline_iter)
        else:
            # GNU Make doesn't warn like this (pats self on back).
            logger.warning("re-using a directive name \"%s\" in an assignment at %r", directive_str, assign_expr.get_pos())
            return assign_expr
    else:
        dir_ = parse_directive(expr, directive_str, viter, virt_line, vline_iter)

    return dir_

