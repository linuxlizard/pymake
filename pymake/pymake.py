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

logger = logging.getLogger("pymake")
#logging.basicConfig(level=logging.DEBUG)

from pymake.scanner import ScannerIterator
import pymake.vline as vline
import pymake.symbolmk as symbolmk
from pymake.symbolmk import *
from pymake.constants import *
from pymake.error import *
import pymake.tokenizer as tokenizer
import pymake.parsermk as parsermk
import pymake.source as source
from pymake.symtablemk import SymbolTable
import pymake.makedb as makedb
import pymake.rules as rules
import pymake.shell as shell
import pymake.pargs as pargs
import pymake.submake as submake
from pymake.debug import *

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]

# test/debug fn for debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

def parse_vline(virt_line, vline_iter): 
    # pull apart a single line into token/symbol(s)
    #
    # virt_line - the current line we need to tokenize (a VirtualLine)
    #
    # vline_iter - <generator> across the entire file (returns VirtualLine instances) 
    #
    logger.debug("parse_vline()")

    # save the starting position for error reporting
    starting_pos = virt_line.get_pos()

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)

    # closely follow GNU Make's behavior eval() src/read.c
    #
    # 1. try assignment expressions
    # 2. if not (1) then try conditional line
    # 3. if not (2) then try export/unxport
    # 4. if not (3) then try vpath
    # 5. if not (4) then try include/sinclude/-include
    # 6. if not (5) then try 'load'  (NOT IMPLEMENTED IN PYMAKE)
    # 7. if not (6) then try rule+recipe

    a = tokenizer.tokenize_assignment_statement(vchar_scanner)
    if a:
        if isinstance(a, DefineDirective):
            # we found an define block
            d = parsermk.parse_define_block(a, virt_line, vline_iter)
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
        d = parsermk.parse_directive( vstr, vchar_scanner, vline_iter)
        if d:   
            # we found a conditional block.
            # We're done here.
            return d
    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # seek export | unexport
    vstr = tokenizer.seek_directive(vchar_scanner, set(("export","unexport")))
    if vstr:
        # TODO
        e = parsermk.parse_directive(vstr, vchar_scanner, vline_iter)
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
        # TODO
        raise NotImplementedError(str(vstr))
    assert vchar_scanner.is_starting(), vchar_scanner.get_pos()

    # How does GNU Make decide something is a rule?
    # (Well, it's quite complicated.)

    rule = parsermk.parse_rule(vchar_scanner)
    if rule:
        if vchar_scanner.remain():
            # we have a rule+recipe continuation
            recipe = tokenizer.tokenize_recipe(vchar_scanner)
            rule.add_recipe(recipe)
            assert not vchar_scanner.remain()

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


def parse_vline_stream(virt_line, vline_iter): 
    assert 0, "OBSOLETE DO NOT USE use parse_vline() instead"

    # pull apart a single line into token/symbol(s)
    #
    # virt_line - the current line we need to tokenize (a VirtualLine)
    #
    # vline_iter - <generator> across the entire file (returns VirtualLine instances) 
    #

    logger.debug("tokenize()")

    # A line with a leading RP (RECIPEPREFIX) aka <tab> by will FOR NOW always
    # tokenize to a Recipe. Will later add a step to dig deeper into the line
    # to determine if it should be treated as a statement instead. GNU-Make has
    # several cases where it allows RP lines to plain statements.
    if isinstance(virt_line,vline.RecipeVirtualLine):
        # This is where we need test the line to see if the RP falls under one
        # of several GNU Make exceptions to the recipeprefix rule.
        # Using GNU Make 4.1 eval() - src/read.c as baseline behavior.
        # 
        # TODO test for assignment before first recipe omg why do you do this
        # to me, GNU Make?
        if not tokenizer.seek_directive(iter(virt_line)):
            recipe = parsermk.tokenize_recipe(iter(virt_line))
            return recipe

#    if get_line_number(virt_line) > 150:
#        breakpoint()

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)
    statement = tokenizer.tokenize_line(vchar_scanner)

    if not isinstance(statement,RuleExpression) : 
        logger.debug("statement=%s", str(statement))

        # we found a bare Expression that needs a second pass
        assert isinstance(statement,Expression), type(statement)
        return parsermk.parse_expression(statement, virt_line, vline_iter)

    # At this point we have a Rule.
    # rule line can contain a recipe following a ; 
    # for example:
    # foo : bar ; @echo baz
    #
    # The rule parser should stop at the semicolon. Will leave the
    # semicolon as the first char of iterator

#    logger.debug("rule=%s", str(statement))

    # truncate the virtual line that precedes the recipe (cut off
    # at a ";" that might be lurking)
    #
    # foo : bar ; @echo baz
    #          ^--- truncate here
    #
    # I have to parse the full line as a rule to know where the rule ends and
    # the recipe(s) begin.  A backslash makes me crazy. For example:
    #
    # foo : bar ; @echo baz\
    # I am more recipe hur hur hur
    #
    # The recipe is "@echo baz\\\nI am more recipe hur hur hur\n"
    # and that's what needs to exec'd.
    if not vchar_scanner.is_empty():
        # truncate at position of first char of whatever is
        # leftover from the rule
        recipe = parsermk.tokenize_recipe(vchar_scanner)
        # attach the recipe to the rule
        statement.add_recipe(recipe)

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

    statement_list = [parse_vline(vline, vline_iter) for vline in vline_iter] 

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
        v = vline.VirtualLine([oneline], (0,0), "@defaults")
        stmt = tokenizer.tokenize_assignment_statement(iter(v))
        stmt.eval(symtable)

    # TODO parse automatics

def _execute_statement_list(stmt_list, curr_rules, rulesdb, symtable):

    exit_code = 0

    for tok in stmt_list:
        # sanity check; everything has to have a successful get_pos()
        _ = tok.get_pos()

        logger.debug("execute %r from %r", tok, tok.get_pos())

        if isinstance(tok, Recipe):
            if not curr_rules:
                # We're confused. 
                raise RecipeCommencesBeforeFirstTarget(pos=tok.get_pos())
            [rule.add_recipe(tok) for rule in curr_rules]

        elif isinstance(tok,RuleExpression):
            # restart the rules list but maintain the same ref!
            curr_rules.clear()

            rule_expr = tok

            # Note a RuleExpression.eval() is very different from all other
            # eval() methods (so far).  A RuleExpression.eval() returns two
            # arrays of strings: targets, prereqs
            # All other eval() returns a string.
            target_list, prereq_list = rule_expr.eval(symtable)
               
            for t in target_list:
                rule = rules.Rule(t, prereq_list, rule_expr.recipe_list, rule_expr.get_pos())
                rulesdb.add(rule)
                curr_rules.append(rule)

        else:
            try:
                result = tok.eval(symtable)
                logger.debug("execute result=\"%s\"", result)
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
                        raise MissingSeparator(tok.get_pos())
                else:
                    # A conditional block or include eval returns an array
                    # of parsed Symbols ready for eval.  
                    assert isinstance(result,list), type(result)
                    exit_code = _execute_statement_list(result, curr_rules, rulesdb, symtable)
                        
            except MakeError as err:
                # Catch our own Error exceptions. Report, break out of our execute loop and leave.
                logger.exception(err)
                error_message(tok.get_pos(), err.msg)
                # check cmdline arg to dump err.description for a more detailed error message
#                if detailed_error_explain:
#                    error_message(tok.get_pos(), err.description)
                exit_code = 1
            except SystemExit:
                raise
            except Exception as err:
                # My code crashed. For shame!
                logger.exception(err)
                logger.error("INTERNAL ERROR eval exception during token makefile=\"\"\"\n%s\n\"\"\"", tok.makefile())
                logger.error("INTERNAL ERROR eval exception during token string=%s", str(tok))
                filename,pos = tok.get_pos()
                logger.error("eval failed tok=%r file=%s pos=%s", tok, filename, pos)
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
                raise NotImplementedError

            else:
                break

        return s, ignore_failure, silent

    # TODO many more automatic variables
    symtable.push("@")
    symtable.push("^")
    symtable.push("+")
    symtable.push("<")
    symtable.add_automatic("@", rule.target, recipe.get_pos())
    symtable.add_automatic("^", " ".join(remove_duplicates(rule.prereq_list)), rule.get_pos())
    symtable.add_automatic("+", " ".join(rule.prereq_list), rule.get_pos())
    symtable.add_automatic("<", rule.prereq_list[0] if len(rule.prereq_list) else "", rule.get_pos())

    cmd_s = recipe.eval(symtable)
#    print("execute_recipe \"%r\"" % cmd_s)

    symtable.pop("@")
    symtable.pop("^")
    symtable.pop("+")
    symtable.pop("<")
        
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

    return exit_status["error"] if exit_code else exit_status["success"] 

def execute(makefile, args):
    # ha ha type checking
    assert isinstance(args, pargs.Args)

    # tinkering with how to evaluate
    symtable = SymbolTable(warn_undefined_variables=args.warn_undefined_variables)

    if not args.no_builtin_rules:
        _add_internal_db(symtable)

    # aim sub-makes at my helper script
#    symtable.add("MAKE", "py-submake")
    symtable.add("MAKE", submake.create_helper())
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
    symtable.add("CURDIR", os.getcwd())

    target_list = []

    # GNU Make allows passing assignment statements on the command line.
    # e.g., make -f hello.mk 'CC=$(subst g,x,gcc)'
    # so the arglist must be parsed and assignment statements saved. Anything
    # not an Assignment is likely a target.
    for onearg in args.argslist:
        v = vline.VirtualLine([onearg], (0,0), "@commandline")
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

    exit_code = _execute_statement_list(makefile.token_list, curr_rules, rulesdb, symtable)

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
        try:
            rule = rulesdb.get(target)
        except KeyError:
            error_message(None, "No rule to make target '%s'" % target)
            exit_code = exit_status["error"]
            break

        if args.dotfile:
            rule.graphviz_graph()

#        print("rule=",rule)
#        print("target=",rule.target)
#        print("recipe=",rule.recipe_list)
#        print("prereqs=",rule.prereq_list)

        # walk a dependency tree
        for rule in rulesdb.walk_tree(target):
            if not rule.recipe_list:
                # this warning catches where I fail to find an implicit rule
                logger.warning("I didn't find a recipe to build target=\"%s\"", target)

            for recipe in rule.recipe_list:
                exit_code = execute_recipe(rule, recipe, symtable, args)
                if exit_code != 0:
                    break
            if exit_code != 0:
                break

    return exit_status["error"] if exit_code else exit_status["success"] 
    
def _run_it(args):
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
        print("# start makefile %s" % args.output)
        with open(args.output,"w") as outfile:
            print(makefile.makefile(), file=outfile)
        print("# end makefile %s" % args.output)

    exit_code = execute(makefile, args)
    return exit_code

# FIXME ugly hack dependency injection to solve problems with circular imports
parsermk.parse_vline = parse_vline 
symbolmk.parse_vline = parse_vline 
symbolmk.tokenize_line = tokenizer.tokenize_line

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
