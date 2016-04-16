#!/usr/bin/env python3

#  The whole Virtual Line thing provides character by character iterator across
#  a block of text from a Makefile. The "virtual line" bit hides the backslash
#  rules from the scanner/parser.
#
#  VirtualLine also will eventually be the cornerstone in the debugger itself.
#  Soooooon.
#
# davep 20160416

import sys
import logging

logger = logging.getLogger("pymake.test_vline")

from scanner import ScannerIterator
from vline import get_vline
from source import SourceFile

def test1(infilename):
    # load, print a file. The virtual line will hide the backslash line
    # continuations
    src = SourceFile(infilename)
    src.load()
    scanner = ScannerIterator(src.file_lines)
    vline_iter = get_vline(scanner)

    for vline in vline_iter:
        logger.info("@@%d >>%s<<", vline.starting_file_line, vline)

def main():
    for f in sys.argv[1:]
        test1(f)

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
