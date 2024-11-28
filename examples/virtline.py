# SPDX-License-Identifier: GPL-2.0
# Copyright (C) David Poole david.poole@ericsson.com

# simple example showing the virtual line iterator which handles backslashes
# and maintains a file+row+col for every character
#
# run with:
# PYTHONPATH=. python3 examples/virtline.py
#
# davep 20241116

import sys
import logging

logger = logging.getLogger("pymake")

import pymake.source as source
import pymake.vline as vline
from pymake.scanner import ScannerIterator
from pymake import tokenizer

def main(infilename):
    src = source.SourceFile(infilename)
    src.load()

    # iterator across all actual lines of the makefile
    line_scanner = ScannerIterator(src.file_lines, src.name)

    # iterator across "virtual" lines which handles the line continuation
    # (backslash)
    vline_iter = vline.get_vline(src.name, line_scanner)

    # iterate over a file showing single lines joined by backslash
    for virt_line in vline_iter:
        pos = virt_line.get_pos()
        s = str(virt_line)
        print(f"{pos} {s}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    for infilename in sys.argv[1:]:
        main(infilename)
    else:
        print("usage: %s makefile1 [makefile2 [makefile3...]]", file=sys.stderr)


