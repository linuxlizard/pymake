# SPDX-License-Identifier: GPL-2.0
# Copyright (C) David Poole david.poole@ericsson.com

# Testing simple tokenizing
# davep 20241124

import logging

import pymake.source as source
import pymake.vline as vline
from pymake.scanner import ScannerIterator
from pymake import tokenizer

logger = logging.getLogger("pymake")

from gnu_make import run_gnu_make, debug_save

def main():
    name = "expression-test"

    # A list of lines as if read from a makefile.
    # (must be a valid makefile for this test)
    test_file = """
ifeq (a,b)
endif
a:=b
a := b
ifeq 'a' 'b'
endif

$(info a=$(a))
a:=
$(a)

all: $(SRC)
"""
    src = source.SourceString(test_file)
    src.load()

    debug_save(src.file_lines)

    # run through GNU Make to verify we're valid 
    run_gnu_make(src.file_lines)

    # iterator across all actual lines of the makefile
    # (supports pushback)
    line_scanner = ScannerIterator(src.file_lines, src.name)

    # iterator across "virtual" lines which handles the line continuation
    # (backslash)
    vline_iter = vline.get_vline(name, line_scanner)

    for virt_line in vline_iter:
        s = str(virt_line).strip()
        print(f"input=\"{s}\"")

        vchar_scanner = iter(virt_line)

        # a very simple tokenize pass that simply splits into Literals (whitespace or non-whitespace)
        # and variable ref $()
        # Pretty much anything can be tokenized into a simple token_list
        token_list = tokenizer.tokenize_line(vchar_scanner)
        assert isinstance(token_list,list), type(token_list)
        print(token_list)

if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
#    logging.getLogger("pymake.tokenize").setLevel(level=logging.DEBUG)
#    logging.getLogger("pymake.parser").setLevel(level=logging.DEBUG)
    main()

