# SPDX-License-Identifier: GPL-2.0
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

import sys
import logging
import os
import os.path
from enum import Enum

logger = logging.getLogger("pymake.pymake")

from pymake.scanner import ScannerIterator
import pymake.vline as vline
import pymake.symbol as symbol
from pymake.symbol import *
from pymake.constants import *
from pymake.error import *
import pymake.tokenizer as tokenizer
import pymake.parser as parser
import pymake.source as source
from pymake.symtable import SymbolTable
import pymake.makedb as makedb
import pymake.rules as rules
import pymake.shell as shell
import pymake.pargs as pargs
import pymake.submake as submake
from pymake.debug import *
import pymake.constants as constants
import pymake.functions as functions

_debug = False

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]

# test/debug fn for debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

def _parse_one_vline(virt_line, vline_iter, rules):
    logger.debug("parse_vline() rules=%d", rules[0])

    # save the starting position for error reporting
    starting_pos = virt_line.get_pos()

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)

    # Closely follow GNU Make's behavior in eval() src/read.c
    # Because GNU Make doesn't have a defined grammar, parsing is very context
    # sensitive.
    #
    # 0. Check for recipe prefix aka <tab>. 
    #   0.1. if we've seen a Rule, then this is a Recipe line. Otherwise, continue.
    #   0.2. Rule without a Target aka ":foo"
    #
    #   TODO there are a lot of subtle conditions in eval() I need to study
    #   further.
    #   
    # 1. if not (0) then try assignment expressions
    # 2. if not (1) then try conditional line
    # 3. if not (2) then try export/unxport
    # 4. if not (3) then try vpath
    # 5. if not (4) then try include/sinclude/-include
    # 6. if not (5) then try 'load'  (NOT IMPLEMENTED IN PYMAKE)
    # 7. if not (6) then try rule+recipe

    if isinstance(virt_line, vline.RecipeVirtualLine):
        # FIXME 20241215 corner case. Had a horrible horrible thought about my
        # RecipeVirtualLine false positive. The backslash collapsing rules are
        # different for regular lines and recipe lines. At some point, I'll
        # need to convert the RecipeVirtualLine to a regular VirtualLine. TODO
        # find an example where this might happen.

        if rules[0]:
            # we've seen a Rule previously
            recipe = tokenizer.tokenize_recipe(vchar_scanner)
            assert recipe
            return recipe

        # fall through and attempt to parse it another way

    a = tokenizer.tokenize_assignment_statement(vchar_scanner)
    if a:
        if isinstance(a, DefineDirective):
            # we found an define block
            d = parser.parse_define_block(a, virt_line, vline_iter)
            return d

        # Is an assignment statement not a conditional.
        # We're done here.
        return a

    # make sure that my functions restore vchar_scanner to starting state if
    # they don't find what they're looking for.
    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # mimic what GNU Make conditional_line() does
    # by looking for a directive in this line
    vstr = tokenizer.seek_directive(vchar_scanner, conditional_directive )
    if vstr:
        d = parser.parse_directive( vstr, vchar_scanner, vline_iter)
        if d:   
            # we found a conditional block.
            # We're done here.
            return d
    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # seek export | unexport
    vstr = tokenizer.seek_directive(vchar_scanner, set(("export","unexport")))
    if vstr:
        e = parser.parse_directive(vstr, vchar_scanner, vline_iter)
        assert e
        return e

    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # seek vpath
    vstr = tokenizer.seek_directive(vchar_scanner, set(("vpath",)))
    if vstr:
        # TODO
        raise NotImplementedError(str(vstr))
    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()
   
    # seek include
    vstr = tokenizer.seek_directive(vchar_scanner, include_directive)
    if vstr:
        d = parser.parse_directive( vstr, vchar_scanner, vline_iter)
        assert d
        return d

    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # How does GNU Make decide something is a rule?
    # (Well, it's quite complicated.)

    rule = parser.parse_rule(vchar_scanner)
    if rule:
        if vchar_scanner.remain():
            # we have a rule+recipe continuation
            recipe = tokenizer.tokenize_recipe(vchar_scanner)
            rule.add_recipe(recipe)
            assert not vchar_scanner.remain()

        rules[0] += 1
        return rule

    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # TODO at this point, treat everything suspected of being a recipe as a
    # recipe.  I do not know if this is correctly correct.
    if isinstance(virt_line, vline.RecipeVirtualLine):
        recipe = tokenizer.tokenize_recipe(vchar_scanner)
        assert recipe
        return recipe

    # Stuff that can't be explicitly tokenzparsed as an assignment, a
    # directive, or rule winds up being a simple Expression that needs another
    # pass during eval()
    #
    # Expression is single function like $(info) or $(warning). Not all
    # functions are valid in statement context.  GNU Make expands variables
    # during parsing so an expression *might* wind up being a rule.
    # 
    # For example:
    # COLON:=:
    # all ${COLON} hello.o  # this is a rule
    #
    # A lone Expression in GNU Make usually triggers the "missing separator"
    # error because the parser gets confused. For example, the previous example if
    # COLON wasn't defined is expanded to:
    # all hello.o   # this is garbage
    #

    token_list = tokenizer.tokenize_line(vchar_scanner)
    e = Expression(token_list)
    return e


def parse_vline(vline_iter): 
    # 
    # Generator
    #

    # pull apart a single line into token/symbol(s)
    #
    # virt_line - the current line we need to tokenize (a VirtualLine)
    #
    # vline_iter - <generator> across the entire file (returns VirtualLine instances) 
    #

    # I tried hard to make the parser context free but that's not going to
    # work.  How <tab> (cmd prefix) is interpretted depends on whether a Rule
    # has been seen or not. A line with <tab> is treated as a regular line if a
    # Rule hasn't been seen yet. Once a Rule has been seen, a <tab> line
    # *might* be a Recipe. So need to preserve context across parse_vline
    # calls.
    rules_counter = [0]

    for vline in vline_iter:
        tok = _parse_one_vline(vline, vline_iter, rules_counter)
        yield tok
        

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

    statement_list = [v for v in parse_vline(vline_iter)] 

    # good time for some sanity checks
    for t in statement_list:
        assert t and isinstance(t,Symbol), t

    return Makefile(statement_list)

def parse_makefile(infilename) : 
    logger.debug("parse_makefile infilename=%s", infilename)
    src = source.SourceFile(infilename)

    return parse_makefile_from_src(src)

def find_location(tok):
    return tok.get_pos()

def _add_internal_db(symtable):
    # grab gnu make's internal db, add to our own
    #
    # NOTE! does this requires my code to be the same license as GNU Make (GPLv3 as of 20221002) ?
    # TODO 202040927 ; confirm this ---^^^ because it sounds ominious
    defaults, automatics = makedb.fetch_database()

    # FIXME fetch_database() only returns assignment statements based on '#
    # default' and '# automatic' strings in the `make -p` output.
    # I still need to capture the rules.
    # I really should be parsing the entire output of the `make -p` as a
    # makefile, not cherry-picking strings from it.

    # If I don't run this code, is my code still under GPLv3 ???

    # now have a list of strings containing Make syntax assignment statements
    for oneline in defaults:
        # mark these variables 'default'
        v = vline.VirtualLine([oneline], (-1,-1), "@defaults")
        stmt = tokenizer.tokenize_assignment_statement(iter(v))
        stmt.eval(symtable)

    # TODO parse automatics

def execute_statement_list(stmt_list, curr_rules, rulesdb, symtable):

    exit_code = 0

    def _is_recipe_comment(tok):
        # corner case to handle a line with leading <tab> and a comment
        # which will be a Recipe if we're inside a Rule but is ignored 
        # before we've seen a Rule
        try:
            tok = tok.token_list[0]
            lit = tok.literal
        except AttributeError:
            # not a literal therefore definitely can't be a comment
            return False
        return tokenizer.seek_comment(iter(tok.string))

    for statement in stmt_list:
        # sanity check; everything has to have a successful get_pos()
        _ = statement.get_pos()

        logger.debug("execute %r from %r", statement, statement.get_pos())
#        logger.info("execute tok=%r from %r", tok, tok.get_pos())

        if isinstance(statement, Recipe):
            # We've found a recipe. Have we seen a rule yet?
            # If this is just a comment line, ignore it
            # But if we haven't seen a rule, throw the infamous error.

            if not curr_rules and not _is_recipe_comment(statement):
                # So We're confused. 
                raise RecipeCommencesBeforeFirstTarget(pos=statement.get_pos())

            [rule.add_recipe(statement) for rule in curr_rules]

        elif isinstance(statement,RuleExpression):
            # restart the rules list but maintain the same ref!
            # (need the same ref because this array is passed by the caller and
            # we need to track the values across calls to this function)
            curr_rules.clear()

            rule_expr = statement
            m = rule_expr.makefile()

            # Note a RuleExpression.eval() is very different from all other
            # eval() methods (so far).  A RuleExpression.eval() returns two
            # arrays of strings: targets, prereqs
            # All other eval() returns a string.
            target_list, prereq_list = rule_expr.eval(symtable)

            if rule_expr.assignment:
                # Have a target-specific assignment expression.
                # There will be no prereqs or attached recipes.
                #
                # The assignments will not be eval'd here but rather stored in
                # the Rule and eval'd when the Rule is used.
                assert not prereq_list

            if target_list:
                for t in target_list:
                    rule = rulesdb.add(t, prereq_list, rule_expr.recipe_list, 
                            rule_expr.assignment, rule_expr.get_pos())
                    curr_rules.append(rule)
                    # we're in a big confusing loop so get rid of a name I re-use
                    del rule
            else:
                # "We accept and ignore rules without targets for
                #  compatibility with SunOS 4 make." -- GNU Make src/read.c
                # grumble grumble grumble
                # We need to have a Rule in curr_rules to correctly parse
                # ambiguous statements with have a leading Recipe Prefix 
                # (aka <tab>)
                rule = rules.Rule(None, prereq_list, rule_expr.recipe_list, rule_expr.assignment, rule_expr.get_pos())
                # don't add this Rule to the DB but do let the world know we are in a Rule
                curr_rules.append(rule)

        else:
            try:
                result = statement.eval(symtable)
                logger.debug("execute 0x%x result=\"%s\"", id(statement), result)
                #   - eval can return a string
                # or
                #   - eval can return an array of Expression|Rule which needs to be
                #     executed as well
                if isinstance(result,str):
                    if result.strip():
                        # TODO need to parse/reinterpret the result of the expression.
                        # Functions such as $(eval) and $(call) can generate new
                        # makefile rules, statements, etc.
                        # GNU Make itself seems to interpret raw text as a rule and
                        # will print a "missing separator" error
                        #
                        # Update 20260101 NOPE. The $(eval) function is
                        # completely different and cannot be handled in the way
                        # I originally hoped.
                        raise MissingSeparator(statement.get_pos())
                else:
                    # A conditional block or include eval returns an array
                    # of parsed Symbols ready for eval.  
                    assert isinstance(result,list), type(result)
                    exit_code = execute_statement_list(result, curr_rules, rulesdb, symtable)
                        
            except MakeError as err:
                # Catch our own Error exceptions. Report, break out of our execute loop and leave.
                logger.exception(err)
                error_message(statement.get_pos(), err.msg)
                # check cmdline arg to dump err.description for a more detailed error message
#                if detailed_error_explain:
#                    error_message(statement.get_pos(), err.description)
                exit_code = 1
            except SystemExit:
                raise
            except Exception as err:
                # My code crashed. For shame!
                logger.exception(err)
                logger.error("INTERNAL ERROR exception during token makefile=\"\"\"\n%s\n\"\"\"", statement.makefile())
                logger.error("INTERNAL ERROR exception during token string=%s", str(statement))
                filename,pos = statement.get_pos()
                logger.error("execute failed pos=%r file=%s statement=%r", pos, filename, statement)
                exit_code = 1
    
        # leave early on error
        if exit_code:
            break

    # bottom of loop
    return exit_code

def execute_recipe(rule, recipe, symtable, args):
    def remove_duplicates(s_list):
        # the $^ variable removes duplicates but must must must preserve order
        seen_list = []
        for s in s_list:
            if s not in seen_list:
                seen_list.append(s)
        return seen_list

    def resolve_backslashes(s):
        str_list = cmd_s.split("\n")
        cmd_list = []

        for s in str_list:
            cmd_list.append(s)
            if s.endswith(backslash):
                continue

            yield "\n".join(cmd_list)
            cmd_list.clear()

    def check_prefixes(s):
        # "To ignore errors in a recipe line, write a ‘-’ at the beginning of the line’s text (after the
        # initial tab). The ‘-’ is discarded before the line is passed to the shell for execution"
        # GNU Make 4.2 Jan 2020
        ignore_failure = False

        # "When a line starts with ‘@’, the echoing of that line is suppressed. The ‘@’ is discarded
        # before the line is passed to the shell."
        # GNU Make 4.3 Jan 2020
        silent = False

        # GNU make will eat any/all leading - + @ and whitespace
        # src/job.c start_job_command()
        while 1:
            if s[0] == '@':
                # silent command
                s = s[1:]
                silent = True

            elif s[0] == '-':
                # ignore failure
                s = s[1:]
                ignore_failure = True

            elif s[0] in whitespace:
                s = s[1:]

            elif s[0] == '+':
                raise NotImplementedError()

            else:
                break

        return s, ignore_failure, silent

    # TODO many more automatic variables
    symtable.push_layer()
    symtable.add_automatic("@", rule.target, recipe.get_pos())
    symtable.add_automatic("^", " ".join(remove_duplicates(rule.prereq_list)), rule.get_pos())
    symtable.add_automatic("+", " ".join(rule.prereq_list), rule.get_pos())
    symtable.add_automatic("<", rule.prereq_list[0] if len(rule.prereq_list) else "", rule.get_pos())

    cmd_s = recipe.eval(symtable)
#    print("execute_recipe \"%r\"" % cmd_s)

    # Defining Multi-Line Variables.
    # "However, note that using two separate lines means make will invoke the shell twice, running
    # an independent sub-shell for each line. See Section 5.3 [Recipe Execution], page 46."
    # GNU Make 4.2 2020 
    #
    # The recipe.eval() returns a single string.  However, multi-line variables
    # are treated as multiple lines given to the shell individually.
    # DefineBlock.eval() will eval its individual lines then return a \n joined
    # string.
    #
    # But can't just blindly split on \n because the recipe could actually be a
    # shell line with continuations.  
    #
    cmd_list = resolve_backslashes(cmd_s)

    exit_code = 0

    for s in cmd_list:
#        print("shell execute \"%s\"" % s)

        s, ignore_failure, silent = check_prefixes(s)

        if not silent and not args.silent:
            print(s)

        if args.dry_run:
            print(s)
            continue

        exit_code = 0
        ret = shell.execute(s, symtable)

        # 
        # !!! Run a Sub-Make !!!
        #
        # The shell.execute() determined that we ran the sub-make helper. The
        # return value of the submake is the args as interpretted by the
        # shell (whichever shell). We now take those args tokenzparse+run that
        # makefile in our same process context.
        if ret.is_submake:
            # the submake is very simple and should not fail
            if ret.exit_code != 0:
                raise InternalError(msg="running submake failed",
                        moremsg=ret.stderr,                        
                        pos=recipe.get_pos() ) 

            submake_argv = ret.stdout.strip().split("\n")
            args = pargs.parse_args(submake_argv[1:])

            currwd = os.getcwd()
            exit_code = _run_it(args)
            os.chdir(currwd)
            # clean up the output from the submake helper
            ret.stdout = ""

        exit_code = ret.exit_code
        print(ret.stdout,end="")
        if exit_code != 0:
            print("make:", ret.stderr, file=sys.stderr, end="")
            print("make: *** [%r: %s] Error %d %s" % (recipe.get_pos(), rule.target, exit_code, "(ignored)" if ignore_failure else ""), file=sys.stderr)

            if not ignore_failure:
                break
            exit_code = 0

    symtable.pop_layer()
        
    return exit_status["error"] if exit_code else exit_status["success"] 

def execute(makefile, args):
    # ha ha type checking
    assert isinstance(args, pargs.Args)

    symtable = SymbolTable(warn_undefined_variables=args.warn_undefined_variables)

    if not args.no_builtin_rules:
        _add_internal_db(symtable)

    # aim sub-makes at my helper script
    symtable.update_builtin("MAKE", submake.create_helper())
    logger.debug("submake helper=%s", symtable.fetch("MAKE"))

    # "Contains the name of each makefile that is parsed by make, in the order
    # in which it was parsed. The name is appended just before make begins to
    # parse the makefile."
    # This is tricky for me because the parse and execute happen independently.
    # GNU Make is a one pass.  I'm 2+ passes.  
    pos = makefile.get_pos()
    symtable.add("MAKEFILE_LIST", pos[0], pos=pos)

    # "For your convenience, when GNU make starts (after it has processed any -C options)
    # it sets the variable CURDIR to the pathname of the current working directory. This value
    # is never touched by make again:"
    # GNU Make 4.3 2020 
    # The -C option will be handled before this function is called.
    symtable.update_builtin("CURDIR", os.getcwd())

    target_list = []

    # GNU Make allows passing assignment statements on the command line.
    # e.g., make -f hello.mk 'CC=$(subst g,x,gcc)'
    # so the arglist must be parsed and assignment statements saved. Anything
    # not an Assignment is likely a target.
    for onearg in args.argslist:
        v = vline.VirtualLine([onearg], (-1,-1), "@commandline")
        vchar_scanner = iter(v)
        stmt = tokenizer.tokenize_assignment_statement(vchar_scanner)
        if isinstance(stmt,AssignmentExpression):
            symtable.command_line_start()
            stmt.eval(symtable)
            symtable.command_line_stop()
        else:
            target_list.append(onearg)

    rulesdb = rules.RuleDB()

    # To handle the confusing mix of conditional blocks and rules/recipes, we
    # will track the last Rule we've seen. When we find a Recipe in the token
    # stream, that Recipe will belong to the last seen Rule. If there is no
    # last seen Rule, then we throw the infamous "recipe commences before first
    # target" error.
    # 
    # Basically, we have context sensitive evaluation.
    curr_rules = []

    # For handling $(eval)  This is not my proudest moment.  I originally
    # designed my make function implementations to be truly functional (no side
    # effects). My plan was for $(eval) to return a string of Make code that
    # would be re-interpretted. But now I'm deep enough into implementation to
    # understand that won't work.  The $(eval) function is entirely a side
    # effect. The $(eval) function can add rules, execute other functions,
    # anything.  And the $(eval) has to happen exactly in the place where it's
    # called. 
    # $(info $(eval foo:bar))  # add a rule; $(info) would consume the string
    # if I simply returned "foo:bar" from $(eval)
    #
    # I need a way to send down the current state of the make (specifically,
    # rules). The symbol table is the only argument passed between make
    # functions.
    symtable.curr_rules = curr_rules
    symtable.rulesdb = rulesdb

    exit_code = execute_statement_list(makefile.token_list, curr_rules, rulesdb, symtable)

    if exit_code:
        return exit_code

    # write the rules db to graphviz if requested
    if args.dotfile:
        title = get_basename(makefile.get_pos()[0])
        rulesdb.graphviz_graph(title + "_makefile", args.dotfile)
        print("wrote %s for graphviz" % args.dotfile)

    if args.htmlfile:
        title = get_basename(makefile.get_pos()[0])
        rulesdb.html_graph(title + "_makefile", args.htmlfile)
        print("wrote %s for html" % args.htmlfile)

    try:
        if not target_list:
            target_list = [ rulesdb.get_default_target() ]
    except IndexError:
        error_message(makefile.get_pos(), "No targets" )
        return exit_status["error"]

    #
    # At this point, we start executing the makefile Rules.
    #
    logger.info("Starting run of %s", makefile.get_pos()[0])

    for target in target_list:
        exit_code = 0

        try:
            rule = rulesdb.get(target)
        except KeyError:
            error_message(None, "No rule to make target '%s'" % target)
            exit_code = exit_status["error"]
            break

        if args.dotfile:
            rule.graphviz_graph()

        if _debug:
            print("rule=",rule)
            print("target=",rule.target)
            print("recipe=",rule.recipe_list)
            print("prereqs=",rule.prereq_list)

        # walk a dependency tree
        for rule in rulesdb.walk_tree(target):
            if not rule.recipe_list:
                # this warning catches where I fail to find an implicit rule
                logger.warning("I didn't find a recipe to build target=\"%s\"", target)

            # target specific variables
            if rule.assignment_list:
                symtable.push_layer()
                for asn in rule.assignment_list:
                    asn.eval(symtable)

            for recipe in rule.recipe_list:
                exit_code = execute_recipe(rule, recipe, symtable, args)
                if exit_code != 0:
                    break
            if rule.assignment_list:
                symtable.pop_layer()
            if exit_code != 0:
                break

    return exit_status["error"] if exit_code else exit_status["success"] 
    
def _run_it(args):
    logger.debug("run_it args=\"%s\"", args)
    # -C option
    if args.directory:
        os.chdir(os.path.join(*args.directory))

    infilename = args.filename
    try : 
        makefile = parse_makefile(infilename)
    except MakeError as err:
        # TODO dump lots of lovely useful information about the failure.
        print("%s"%err, file=sys.stderr)
        if args.detailed_error_explain:
            print("%s"%err.description, file=sys.stderr)

        sys.exit(1)

    # print the S Expression
    if args.s_expr:
        print("# start S-expression")
        print("makefile={0}".format(makefile))
        print("# end S-expression")

    # regenerate the makefile
    if args.output:
        with open(args.output,"w") as outfile:
            print(makefile.makefile(), file=outfile)
        print("wrote makefile %s" % args.output)

    if args.s_expr or args.output:
        return 0

    exit_code = execute(makefile, args)
    return exit_code

# FIXME ugly hack dependency injection to solve problems with circular imports
parser.parse_vline = parse_vline 
symbol.parse_vline = parse_vline 
symbol.tokenize_line = tokenizer.tokenize_line
functions.parse_makefile_from_src = parse_makefile_from_src
functions.execute_statement_list = execute_statement_list

def main():
    args = pargs.parse_args(sys.argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    for f in args.debug_flags:
        log_s = "pymake." + f
        logr = logging.getLogger(log_s)
        if logr:
            logr.setLevel(level=logging.DEBUG)

#    if len(sys.argv) < 2 : 
#        usage()
#        sys.exit(1)

    sys.exit(_run_it(args))

if __name__=='__main__':
    main()
