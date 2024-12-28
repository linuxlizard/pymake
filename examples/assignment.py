# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com

# Simple example testing finding assignment statements.
#
# run with:
# PYTHONPATH=. python3 examples/assignment.py
#
# davep 20241116

import sys
import logging

import pymake.source as source
import pymake.vline as vline
from pymake.scanner import ScannerIterator
from pymake import tokenizer
from pymake import parser
from pymake.symtable import SymbolTable

from gnu_make import run_gnu_make, debug_save

logger = logging.getLogger("pymake")

# Note for my future self because I keep tripping over this problem: Do not
# use embedded \n in a line fed to vline. The vline code assumes it
# receives an array of strings already split by newlines. The embedded newlines
# confuse the vline parser.
# DO NOT DO THIS!!!
#    "SRC\\\n=\\\nhello.c\\\n\n",
# do this instead:
#    "SRC\\\n", "=\\\n", "hello.c\\\n", "\n"

# all these are valid assignment statements
test_file = """
SRC = hello.c
 SRC = hello.c
# these four entries are one virtual line
SRC\\
=\\
hello.c\\


SRC=
SRC=hello.c 
SRC:=hello.c 
SRC::=hello.c 
SRC!=hello.c 
 SRC  =   hello.c     
 SRC  :=   hello.c     
 SRC  ::=   hello.c     
# SRC  :::=   hello.c     
 SRC  !=   hello.c     

# yay tabs
\tSRC\t:=\thello.c\t\t\t\t

# note also trailing whitespace after hello.c is preserved
SRC=hello.c   # next line needs SRC set for GNU Make otherwise "empty variable name"
$(SRC) = $(hello)

FOO? = !! # yes, this is legal Make
FOO?FOO = !! 

# weird but legal ; creates var named the LHS, weird char and all
export,CC:=gcc
export!CC:=gcc

# what happens with unicode?
export 🦄:=👻

# export modifier with variable assignment
export CC =  gcc 
  export      CC =  gcc 
export CC=gcc CFLAGS=-Wall  # creates var named 'gcc CFLAGS=-Wall'
unexport CC=gcc
override CC=gcc
private CC=gcc
export export=export  # what does this do?

# re-usingreserved" words
ifdef=IFDEF
ifeq=IFEQ
vpath=VPATH
export=EXPORT
include=INCLUDE

# multiple modifiers are evaluated left to right by gnu make 
export private override unexport export CC=gcc
export export CC=CFLAGS

# multi-line variable def
# 'endef' required so I can parse this test with GNU Make; ignore
# the 'endef' in my tests later
define foo=
endef  

export define foo=
endef

export unexport override private define foo=
endef

define two-lines=
endef

define two-lines
endef

undefine FOO
undefine FOO BAR BAZ

# will undefine a variable named 'FOO:=1'
undefine FOO:=1
"""

def test_errors():
    name = "error-cases"

    # legal GNU Make but not assignment expression
    error_cases = [
        #  GNU Make thinks this is a rule-specific assignment with a missing LHS
        #  but it kinda looks like a rule with prereq "=hello.c"
#        "  SRC  :   =hello.c    \n", 
        "FOO : /dev/null\n",  # a rule
        "FOO:FOO = BAR\n",  # this is a rule with a rule-specific assignment (not a var named "FOO:FOO"
        "export CC CFLAGS LDFLAGS\n",
        "export\n",
        "unexport\n",
    ]

#    debug_save(error_cases)

    run_gnu_make(error_cases)

    line_scanner = ScannerIterator(error_cases, name)
    vline_iter = vline.get_vline(name, line_scanner)
    for virt_line in vline_iter:
        s = str(virt_line).strip()
        expr = tokenizer.tokenize_assignment_statement(iter(virt_line))
        assert expr is None, expr.makefile()

def main():
    name = "assignment-test"

    src = source.SourceString(test_file)
    src.load()

    test_errors()

    debug_save(src.file_lines)

    # verify everything works in GNU Make
    run_gnu_make(src.file_lines)

    # iterator across all actual lines of the makefile
    # (supports pushback)
    line_scanner = ScannerIterator(src.file_lines, name)

    # iterator across "virtual" lines which handles the line continuation
    # (backslash)
    vline_iter = vline.get_vline(name, line_scanner)

    symtable = SymbolTable()

    for virt_line in vline_iter:
        s = str(virt_line).strip()
        print(f"input=\"{s}\"")

        # stmt will be None if not an assignment statement
        stmt = tokenizer.tokenize_assignment_statement(iter(virt_line))

        # handle case of needing 'endef' to close the 'define' so I can run my
        # tests through GNU Make
        if stmt is None and s=="endef":
            continue

        # the test input should always successfully find an assignment statement
        assert stmt, s
        print(stmt)
        m = stmt.makefile()
        print(f"output=\"{m}\"")

        # Whitespace makes verifying the result difficult. I try very hard to
        # preserve all input whitespace but some places I deliberately need to
        # discard it (between assignment operator and RHS) or add it (the \ is
        # replaced by a whitespace char).  
        #
        # As a result, I cannot compare the input to the output. The only valid
        # test is to compare my output to GNU Make output.
        #
        # But I can run a few sanity checks by executing the statement.
        stmt.eval(symtable)

if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
#    logging.getLogger("pymake.vline").setLevel(level=logging.DEBUG)
    logging.getLogger("pymake.tokenize").setLevel(level=logging.DEBUG)
    logging.getLogger("pymake.symbol").setLevel(level=logging.DEBUG)
    main()

