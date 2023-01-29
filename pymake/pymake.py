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
import getopt

logger = logging.getLogger("pymake")
#logging.basicConfig(level=logging.DEBUG)

from pymake.scanner import ScannerIterator
from pymake.version import Version
import pymake.vline as vline
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
    # 
#    logger.debug("rule=%s", str(token))

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
    remaining_vchars = vchar_scanner.remain()
    dangling_recipe_vline = None
    if len(remaining_vchars) > 0:
        # truncate at position of first char of whatever is
        # leftover from the rule
        truncate_pos = remaining_vchars[0].pos

        recipe_str_list = virt_line.truncate(truncate_pos)

        # make a new virtual line from the semicolon trailing
        # recipe (using a virtual line because backslashes)
        dangling_recipe_vline = vline.RecipeVirtualLine(recipe_str_list, truncate_pos, 
                                    remaining_vchars[0].filename)
        recipe = parsermk.tokenize_recipe(iter(dangling_recipe_vline))

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

    # XXX temp hack dependency injection
    parsermk.parse_vline_stream = parse_vline_stream 

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
        v = vline.VirtualLine([oneline], (0,0), "/dev/null")
        stmt = tokenize_statement(iter(v))
        stmt.eval(symtable)

def execute(makefile, args):
    # ha ha type checking
    assert isinstance(args, Args)

    # tinkering with how to evaluate
    logger.info("Starting execute of %s", id(makefile))
    symtable = SymbolTable(warn_undefined_variables=args.warn_undefined_variables)

    # XXX temp disabled while debugging
    _add_internal_db(symtable)

    target_list = []

    # GNU Make allows passing assignment statements on the command line.
    # e.g., make -f hello.mk 'CC=$(subst g,x,gcc)'
    # so the arglist must be parsed and assignment statements saved. Anything
    # not an Assignment is likely a target.
    for onearg in args.argslist:
        v = vline.VirtualLine([onearg], (0,0), "/dev/null")
        stmt = tokenize_statement(iter(v))
        if isinstance(stmt,AssignmentExpression):
            symtable.command_line_start()
            stmt.eval(symtable)
            symtable.command_line_stop()
        else:
            target_list.append(onearg)

    rulesdb = rules.RuleDB()
    exit_code = 0

    # To handle the confusing mix of conditional blocks and rules/recipes, we
    # will track the last Rule we've seen. When we find a Recipe in the token
    # stream, that Recipe will belong to the last seen Rule. If there is no
    # last seen Rule, then we throw the infamous "recipe commences before first
    # target" error.
    # 
    # Basically, we have context sensitive evaluation.
    last_rules = []

    for tok in makefile.token_list:
#        print("tok=",tok)

        if isinstance(tok, Recipe):
            # We're confused. 
            if not last_rules:
                raise RecipeCommencesBeforeFirstTarget(pos=tok.get_pos())
            [rule.add_recipe(tok) for rule in last_rules]

        elif isinstance(tok,RuleExpression):
            last_rules = []
            rule_expr = tok

            # Note a RuleExpression.eval() is very different from all other
            # eval() methods (so far).  A RuleExpression.eval() returns a dict;
            # everything else returns a string.
            rule_dict = rule_expr.eval(symtable)

            for target_str, prereq_list in rule_dict.items():
                rule = rules.Rule(target_str, prereq_list, rule_expr.recipe_list, rule_expr.get_pos())
                rulesdb.add(rule)
                last_rules.append(rule)
        else:
            try:
#                breakpoint()
                result = tok.eval(symtable)
                logger.info("execute result=\"%s\"", result)
                # eval can return a string
                # or
                # eval can return an array of TODO something I haven't figured out yet
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
                    # TODO eval of ConditionalBlocks can return array of "stuff".
                    # For example, the eval of include returns TODO "stuff"
                    # A conditional block's eval returns TODO "stuff"
                    assert isinstance(result,list), type(result)
#                    if len(result):
#                        line_scanner = ScannerIterator(result, "(name TODO)")
#                        vline_iter = vline.get_vline("(name TODO)", line_scanner)
#                        statement_list = [tokenize(vline, vline_iter, line_scanner) for vline in vline_iter] 
                        
            except MakeError as err:
                # Catch our own Error exceptions. Report, break out of our execute loop and leave.
                error_message(tok.get_pos(), err.msg)
                # check cmdline arg to dump err.description for a more detailed error message
                if args.detailed_error_explain:
                    error_message(tok.get_pos(), err.description)
                exit_code = 1
                break
            except SystemExit:
                raise
            except Exception as err:
                # My code crashed. For shame!
                logger.error("INTERNAL ERROR eval exception during token makefile=\"\"\"\n%s\n\"\"\"", tok.makefile())
                logger.error("INTERNAL ERROR eval exception during token string=%s", str(tok))
                filename,pos = tok.get_pos()
                logger.error("eval failed tok=%r file=%s pos=%s", tok, filename, pos)
                raise

    if exit_code != 0:
        return exit_code

    # write the rules db to graphviz if requested
    if args.dotfile:
        title = get_basename(makefile.get_pos()[0])
        rulesdb.graph(title + "_makefile", args.dotfile)
        print("wrote %s for graphviz" % args.dotfile)

    if not target_list:
        target_list = [ rulesdb.get_default_target() ]

    #
    # At this point, we start executing the makefile Rules.
    #
    for target in target_list:
        rule = rulesdb.get(target)
#        print("rule=",rule)
#        print("prereqs=",rule.prereq_list)

        # walk a dependency tree
        for rule in rulesdb.walk_tree(target):
#            print(rule)
#            print(rule.recipe_list.makefile())
            for recipe in rule.recipe_list:
#                print(recipe)
                symtable.push("@")
                symtable.push("^")
                symtable.add_automatic("@", rule.target, recipe.get_pos())
                symtable.add_automatic("^", " ".join(rule.prereq_list), rule.get_pos())
                s = recipe.eval(symtable)
#                print("shell execute \"%s\"" % s)
                if s[0] == '@':
                    # silent command
                    s = s[1:]
                else:
                    print(s)
                ret = shell.execute(s, symtable)
                symtable.pop("@")
                symtable.pop("^")
                exit_code = ret['exit_code']
                if exit_code != 0:
                    print("make:", ret["stderr"], file=sys.stderr, end="")
                    print("make: *** [%r] Error %d" % (rule.get_pos(), exit_code))
                    print("make: *** [%r]: %s Error %d" % (recipe.get_pos(), rule.target, exit_code))
                    return exit_code
                print(ret['stdout'],end="")

    return exit_code
    
def usage():
    # options are designed to be 100% compatible with GNU Make
    # please keep this list in alphabetical order (but with identical commands
    # still grouped together)
    print("""Usage: pymake [options] [target] ...")
Options:
    -d          Print extra debugging information.
    -f FILE
    --file FILE
    --makefile FILE
                Read FILE as a makefile.
    -h
    --help
                Print this help message and exit.
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

        # extra arguments on the command line, interpretted either as a target
        # or a GNU Make expression
        self.argslist = []

        self.warn_undefined_variables = False
        self.detailed_error_explain = False

def parse_args():
    print_version ="""PY Make %s. Work in Progress.
Copyright (C) 2014-2023 David Poole davep@mbuf.com, testcluster@gmail.com""" % (Version.vstring(),)

    args = Args()
    optlist, arglist = getopt.gnu_getopt(sys.argv[1:], "hvo:dSf:", 
                            [
                            "debug", 
                            "dotfile=",
                            "explain",
                            "file=", 
                            "makefile=", 
                            "output=", 
                            "version", 
                            "warn-undefined-variables", 
                            ]
                        )
    for opt in optlist:
        if opt[0] in ("-f", "--file", "--makefile"):
            args.filename = opt[1]                    
        elif opt[0] in ('-o', "--output"):
            args.output = opt[1]
        elif opt[0] == '-S':
            args.s_expr = True
        elif opt[0] == '-d':
            args.debug += 1            
        elif opt[0] in ("-v", "--version"):
            print(print_version)
            sys.exit(0)
        elif opt[0] in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt[0] == "--warn-undefined-variables":
            args.warn_undefined_variables = True
        elif opt[0] == "--explain":
            args.detailed_error_explain = True
        elif opt[0] == "--dotfile":
            args.dotfile = opt[1]
        else:
            # wtf?
            assert 0, opt
            
    args.argslist = arglist
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
    sys.exit(exit_code)

