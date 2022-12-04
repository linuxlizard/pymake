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
import os
#import string

logger = logging.getLogger("pymake")
#logging.basicConfig(level=logging.DEBUG)

# require Python 3.x for best Unicode handling
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from scanner import ScannerIterator
import vline
from symbol import *
from constants import *
from error import *
from tokenizer import tokenize_statement
import parser
import source
from symtable import SymbolTable
import makedb
import rules

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]

# TODO rename this fn
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

    # tokenize character by character across a VirtualLine
    vchar_scanner = iter(virt_line)
    statement = tokenize_statement(vchar_scanner)

    # If we found a rule, we need to change how we're handling the
    # lines. (Recipes have different whitespace and backslash rules.)
    if not isinstance(statement,RuleExpression) : 
        logger.debug("statement=%s", str(statement))

        # we found a bare Expression that needs a second pass
        if isinstance(statement,Expression):
            return parser.parse_expression(statement, virt_line, vline_iter)

        # do we ever get here now? 
        assert 0
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

        recipe_list = parser.parse_recipes(line_scanner, dangling_recipe_vline)
    else :
        recipe_list = parser.parse_recipes(line_scanner)

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

    # XXX temp hack dependency injection
    parser.tokenize = tokenize

    # The vline_iter will read from line_scanner. But line_scanner should be at the
    # proper place at all times. In other words, there are two readers from
    # line_scanner: this function and tokenize_vline()
    # Recipes need to read from line_scanner (different backslash rules).
    # Rest of tokenizer reads from vline_iter.
    statement_list = [tokenize(vline, vline_iter, line_scanner) for vline in vline_iter] 

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

    try : 
        return parse_makefile_from_src(src)
    except ParseError as err:
        err.filename = infilename
        print("ERROR! "+str(err), file=sys.stderr)
        raise

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

def _add_internal_db(symtable):
    # grab gnu make's internal db, add to our own
    # NOTE! this requires my code to be the same license as GNU Make (GPLv3 as of 20221002)
    defaults, automatics = makedb.fetch_database()

    # If I don't run this code, is my code still under GPLv3 ???

    # now have a list of strings containing Make syntax.
    for oneline in defaults:
        # TODO mark these variables 'default'
        vline = vline.VirtualLine([oneline], (0,0), "/dev/null")
        stmt = tokenize_statement(iter(vline))
        stmt.eval(symtable)

def execute(makefile):
    # tinkering with how to evaluate
    logger.info("Starting execute of %s", id(makefile))
    symtable = SymbolTable()

    # XXX temp disabled while debugging
#    _add_internal_db(symtable)

    rulesdb = rules.RuleDB()

    for tok in makefile.token_list:
#        print("tok=",tok)
        if isinstance(tok,RuleExpression):
            rule_expr = tok

            # Must be super careful to eval() the target and prerequisites only
            # once! There may be side effects so must not re-eval() 
            rule_dict = rule_expr.eval(symtable)

            for target_str, prereq_list in rule_dict.items():
                rule = rules.Rule(target_str, prereq_list, rule_expr.recipe_list)
                rulesdb.add(rule)
        else:
            try:
    #            breakpoint()
                s = tok.eval(symtable)
                logger.info("execute result s=\"%s\"", s)
                if s.strip():
                    # TODO need to parse/reinterpret the result of the expression.
                    # Functions such as $(eval) and $(call) can generate new
                    # makefile rules, statements, etc.
                    # GNU Make itself seems to interpret raw text as a rule and
                    # will print a "missing separator" error
                    logger.error("unexpected non-empty eval result=\"%s\" at pos=%r" % (s, tok.get_pos()))
                    sys.exit(1)
            except MakeError:
                # let ParseError propagate
                raise
            except SystemExit:
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

    # XXX temporary tinkering with the rules db
    filename = get_basename(makefile.get_pos()[0])
    rulesdb.graph(filename)

    target = "all"
    rule = rulesdb.get(target)
    
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

