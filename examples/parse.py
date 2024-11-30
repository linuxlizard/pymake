# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com
#
# Demo parsing.
#
# run with:
# PYTHONPATH=. python3 examples/parse.py
#
# davep 20241129

import logging

import pymake.source as source
import pymake.vline as vline
from pymake.pymake import parse_vline
from pymake.scanner import ScannerIterator

from gnu_make import run_gnu_make, debug_save

logger = logging.getLogger("pymake")

# A list of lines as if read from a makefile.
test_file = """
# build hello, world
CC?=gcc
CFLAGS?=-Wall

EXE:=hello
OBJ:=hello.o

ifdef DEBUG
CFLAGS+=-g
endif

all: $(EXE)
	echo successfully built $(EXE)

hello : hello.o
	$(CC) $(CFLAGS) -o $@ $^

hello.o : hello.c
	$(CC) $(CFLAGS) -c -o $@ $^

hello.c:
	echo 'int main(){}' > hello.c
    
clean : ; $(RM) $(OBJ) $(EXE)
"""

def main():
    name = "parser-block-test"

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
        stmt = parse_vline( virt_line, vline_iter )
        assert stmt
        print(stmt)

if __name__ == '__main__':
#    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
#    logging.getLogger("pymake.tokenize").setLevel(level=logging.DEBUG)
#    logging.getLogger("pymake.parser").setLevel(level=logging.DEBUG)
    main()

