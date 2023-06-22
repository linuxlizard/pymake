#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

import sys
import logging
import os
import os.path
import getopt

logger = logging.getLogger("pymake")
#logging.basicConfig(level=logging.DEBUG)

from pymake.scanner import ScannerIterator
from pymake.version import Version
import pymake.vline as vline
import pymake.symbolmk as symbolmk
from pymake.symbolmk import *
from pymake.constants import *
from pymake.error import *
from pymake.tokenizer import tokenize_statement
import pymake.parsermk as parsermk
import pymake.source as source
from pymake.symtablemk import SymbolTable
import pymake.makedb as makedb
import pymake.rules as rules
import pymake.shell as shell

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]

# test/debug fn for debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

def parse_vline_stream(virt_line, vline_iter): 
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
        if not parsermk.seek_directive(iter(virt_line)):
            recipe = parsermk.tokenize_recipe(iter(virt_line))
            return recipe

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)
    statement = tokenize_statement(vchar_scanner)

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

    statement_list = [parse_vline_stream(vline, vline_iter) for vline in vline_iter] 

    # good time for some sanity checks
    for t in statement_list:
        assert t and isinstance(t,Symbol), t

    return Makefile(statement_list)

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

    return parse_makefile_from_src(src)

def find_location(tok):
    return tok.get_pos()

#    # recursively descend into a token tree to find a token with a non-null vcharstring
#    # which will show the starting filename/position of the token
#    logger.debug("find_location tok=%s", tok)
#
#    if isinstance(tok, ConditionalBlock):
#        # conditionals don't have a token_list so we have to drill into the
#        # instance to find something that does
#        return find_location(tok.cond_exprs[0].expression)
#
#    if isinstance(tok, Directive):
#        return find_location(tok.expression)
#
#    # If the tok has a token_list, it's an Expression
#    # otherwise, is a Symbol.
#    #
#    # Expressions contain list of Symbols (although an Expression is also
#    # itself a Symbol). Expression does not have a string (VCharString)
#    # associated with it but contains the Symbols that do.
#    try:
#        for t in tok.token_list:
#            return find_location(t)
#    except AttributeError:
#        # we found a Symbol
#        c = tok.string[0]
#        return c.filename, c.pos
##        for c in tok.string:
##            logger.debug("f %s %s %s", c, c.pos, c.filename)

def _add_internal_db(symtable):
    # grab gnu make's internal db, add to our own
    # NOTE! this requires my code to be the same license as GNU Make (GPLv3 as of 20221002)
    defaults, automatics = makedb.fetch_database()

    # If I don't run this code, is my code still under GPLv3 ???

    # now have a list of strings containing Make syntax.
    for oneline in defaults:
        # TODO mark these variables 'default'
        v = vline.VirtualLine([oneline], (0,0), "...defaults")
        stmt = tokenize_statement(iter(v))
        stmt.eval(symtable)

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
#                        msg = "unexpected non-empty eval result=\"%s\"" % (result, )
                        raise MissingSeparator(tok.get_pos())
                else:
                    # A conditional block's or include's eval returns an array
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
                break
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
                break
    
        if exit_code:
            return exit_code

    # bottom of loop
    return exit_code

def execute_recipe(rule, recipe, symtable):
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

        if not silent:
            print(s)

        exit_code = 0
        ret = shell.execute(s, symtable)

        # 
        # !!! Run a Sub-Make !!!
        #
        # The shell.execute() determined that we ran the sub-make helper. The
        # return value of the submake will is the args as interpretted by the
        # shell (whichever shell). We now take those args tokenzparse+run that
        # makefile in our same process context.
        if ret.is_submake:
            submake_argv = ret.stdout.strip().split("\n")
            args = parse_args(submake_argv[1:])
#            breakpoint()
            currwd = os.getcwd()
            exit_code = _run_it(args)
            os.chdir(currwd)
            # clean up the output from the submake helper
            ret.stdout = ""

        exit_code = ret.exit_code
        print(ret.stdout,end="")
        if exit_code == 0:
            pass
#            print(ret.stdout,end="")
        else:
            print("make:", ret.stderr, file=sys.stderr, end="")
            print("make: *** [%r: %s] Error %d %s" % (recipe.get_pos(), rule.target, exit_code, "(ignored)" if ignore_failure else ""), file=sys.stderr)

            if not ignore_failure:
                break
            exit_code = 0

    return exit_status["error"] if exit_code else exit_status["success"] 

def execute(makefile, args):
    # ha ha type checking
    assert isinstance(args, Args)

    # tinkering with how to evaluate
    logger.info("Starting execute of %s", id(makefile))
    symtable = SymbolTable(warn_undefined_variables=args.warn_undefined_variables)

    if not args.no_builtin_rules:
        _add_internal_db(symtable)

    # aim sub-makes at my helper script
    symtable.add("MAKE", "py-submake")

    target_list = []

    # GNU Make allows passing assignment statements on the command line.
    # e.g., make -f hello.mk 'CC=$(subst g,x,gcc)'
    # so the arglist must be parsed and assignment statements saved. Anything
    # not an Assignment is likely a target.
    for onearg in args.argslist:
        v = vline.VirtualLine([onearg], (0,0), "...commandline")
        stmt = tokenize_statement(iter(v))
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
        rulesdb.graph(title + "_makefile", args.dotfile)
        print("wrote %s for graphviz" % args.dotfile)

    try:
        if not target_list:
            target_list = [ rulesdb.get_default_target() ]
    except IndexError:
        error_message(makefile.get_pos(), "No targets" )
        return exit_status["error"]

    #
    # At this point, we start executing the makefile Rules.
    #
    for target in target_list:
        try:
            rule = rulesdb.get(target)
        except KeyError:
            error_message(None, "No rule to make target '%s'" % target)
            exit_code = exit_status["error"]
            break

#        print("rule=",rule)
#        print("prereqs=",rule.prereq_list)

        # walk a dependency tree
        for rule in rulesdb.walk_tree(target):
            for recipe in rule.recipe_list:
                exit_code = execute_recipe(rule, recipe, symtable)
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

def usage():
    # options are designed to be 100% compatible with GNU Make
    # please keep this list in alphabetical order (but with identical commands
    # still grouped together)
    print("""Usage: pymake [options] [target] ...)
Options:
    -B
    --always-make
                TODO Unconditionally build targets.
    -C dir
    --directory dir
                change to directory before reading makefiles or doing anything else.
    -d          Print extra debugging information.
    -f FILE
    --file FILE
    --makefile FILE
                Read FILE as a makefile.
    -h
    --help
                Print this help message and exit.
    -r
    --no-builtin-rules
                Disable reading GNU Make's built-in rules.
    -v
    --version
                Print the version number and exit.
    --warn-undefined-variables
                Warn whenever an undefined variable is referenced.

Options not in GNU Make:
    --dotfile FILE  
                Write the Rules' dependency graph as a GraphViz dot file. (Work in progress.)
    --explain   Give a verbose error message for common GNU Make errors.
    --output FILE
                Rewrite the parsed makefile to FILE.
    -S          Print the makefile as an S-Expression. (Useful for debugging pymake itself.)
""")

class Args:
    def __init__(self):
        self.debug = 0

        # write rules' dependencies to graphviz .dot file
        self.dotfile = None

        # input filename to parse
        self.filename = None

        # rewrite the parsed Makefile to this file
        self.output = None

        # print the parsed makefile as an S-Expression        
        self.s_expr = False

        self.always_make = False

        self.no_builtin_rules = False

        # extra arguments on the command line, interpretted either as a target
        # or a GNU Make expression
        self.argslist = []

        # -C aka --directory option
        self.directory = None

        self.warn_undefined_variables = False
        self.detailed_error_explain = False

def parse_args(argv):
    print_version ="""PY Make %s. Work in Progress.
Copyright (C) 2014-2023 David Poole davep@mbuf.com, testcluster@gmail.com""" % (Version.vstring(),)

    args = Args()
    optlist, arglist = getopt.gnu_getopt(argv, "Bhvo:drSf:C:", 
                            [
                            "help",
                            "always-make",
                            "debug", 
                            "dotfile=",
                            "explain",
                            "file=", 
                            "makefile=", 
                            "output=", 
                            "no-builtin-rules",
                            "version", 
                            "warn-undefined-variables", 
                            "directory=",
                            ]
                        )
    for opt in optlist:
        if opt[0] in ("-B", "--always-make"):
            args.always_make = True
        elif opt[0] in ("-f", "--file", "--makefile"):
            args.filename = opt[1]                    
        elif opt[0] in ('-o', "--output"):
            args.output = opt[1]
        elif opt[0] == '-S':
            args.s_expr = True
        elif opt[0] == '-d':
            args.debug += 1            
        elif opt[0] in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt[0] in ("-r", "--no-builtin-rules"):
            args.no_builtin_rules = True
        elif opt[0] in ("-v", "--version"):
            print(print_version)
            sys.exit(0)
        elif opt[0] == "--warn-undefined-variables":
            args.warn_undefined_variables = True
        elif opt[0] == "--explain":
            args.detailed_error_explain = True
        elif opt[0] == "--dotfile":
            args.dotfile = opt[1]
        elif opt[0] in ("-C", "--directory"):
            # multiple -C options are supported for reasons I don't understand
            if args.directory is None:
                args.directory = []
            args.directory.append(opt[1])
        else:
            # wtf?
            assert 0, opt
            
    args.argslist = arglist
    return args

# FIXME ugly hack dependency injection to solve problems with circular imports
parsermk.parse_vline_stream = parse_vline_stream 
symbolmk.tokenize_statement = tokenize_statement

def main():
    args = parse_args(sys.argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

#    if len(sys.argv) < 2 : 
#        usage()
#        sys.exit(1)

    sys.exit(_run_it(args))

if __name__=='__main__':
    main()
