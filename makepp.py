#!/usr/bin/env python3

# Make Pre Processor!
#
# Run an entire Makefile through the vline pre-processor.
# Joins backslashed lines into one logical line (whilc preserving physical
# lines). Removes comments.
#
# davep 14-Nov-2014

import sys
from pymake import get_vline
from scanner import ScannerIterator

def makefile_pp_from_strlist(file_lines):
    # we need an iterator across our lines that supports pushback
    line_iter = ScannerIterator(file_lines)
    vline_iter = get_vline(line_iter)

    return list(vline_iter)

def makefile_pp(infilename):
    with open(infilename,'r') as infile :
        file_lines = infile.readlines()

    return makefile_pp_from_strlist(file_lines)

if __name__=='__main__':
    infilename = sys.argv[1]
    makefile_strlist = makefile_pp(infilename)
    print("{0}".format("".join( [ str(s) for s in makefile_strlist ] )),end="")

