# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com

# Demo finding conditional blocks.
#
# run with:
# PYTHONPATH=. python3 examples/conditional.py
#
# davep 20241116

import logging

import pymake.source as source
import pymake.vline as vline
from pymake.scanner import ScannerIterator
from pymake import tokenizer
from pymake.constants import *
from pymake.tokenizer import seek_directive
from pymake.parser import parse_directive

from gnu_make import run_gnu_make, debug_save

logger = logging.getLogger("pymake")

def main():
    name = "conditional-block-test"

    # A list of lines as if read from a makefile.
    test_file = """
ifdef SRC
foo
endif

ifdef SRC
foo
else ifdef OBJ
bar
endif

ifdef SRC
foo
else 
ifdef OBJ
bar
endif
endif

ifeq (a,b)
endif

ifneq 'a' 'b'
endif

# conditional with invalid block
ifdef SRC
this line cannot be parsed by make
endif

# nested conditional with an invalid conditional within
ifdef SRC
ifeq xyz   # invalid but should not fail
endif
endif

ifeq 'abc' "xyz"
hello, world this is an error in your makefile
endif
"""
    src = source.SourceString(test_file)
    src.load()

    debug_save(src.file_lines)

    # verify everything works in GNU Make
    run_gnu_make(src.file_lines)

    # iterator across all actual lines of the makefile
    # (supports pushback)
    line_scanner = ScannerIterator(src.file_lines, src.name)

    # iterator across "virtual" lines which handles the line continuation
    # (backslash)
    vline_iter = vline.get_vline(name, line_scanner)

    for virt_line in vline_iter:
        s = str(virt_line).strip()
        print(f"input=>>>{s}<<<")

        vchar_scanner = iter(virt_line)
        # ha ha type checking
        _ = vchar_scanner.pushback
        _ = vchar_scanner.get_pos

        # 
        # closely follow GNU Make's behavior eval() src/read.c
        #
        # 1. assignments
        # 2. conditional blocks
        # 3... coming soon
        #
        expr = tokenizer.tokenize_assignment_statement(vchar_scanner)
        if expr:
            # Is an assignment statement not a conditional.
            # So ignore.
            continue

        # make sure tokenize_assignment_statement() restored vchar_scanner to
        # its starting state
        #
        # pos[0] = filename
        # pos[1] = (row,col)
        pos = vchar_scanner.get_pos()
        assert vchar_scanner.get_pos()[1][1] == 0, pos

        # mimic what GNU Make conditional_line() does
        # by looking for a directive in this line
        vstr = seek_directive(vchar_scanner, conditional_open)

        # for this test, we should always find a directive
        assert vstr, vstr

        d = parse_directive( vstr, vchar_scanner, vline_iter)
        print(d)
        print(f'makefile="""\n{d.makefile()}\n"""')



if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
#    logging.getLogger("pymake.tokenize").setLevel(level=logging.DEBUG)
#    logging.getLogger("pymake.parser").setLevel(level=logging.DEBUG)
    main()

