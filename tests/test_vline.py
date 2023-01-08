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
import io

logger = logging.getLogger("pymake.test_vline")

from scanner import ScannerIterator
from vline import get_vline
from source import SourceFile
import hexdump
from vline import is_line_continuation, VirtualLine
from printable import printable_string

# turn on the big global debug flags
import vline
vline._debug = True

# GNU Make Manual section 3.1.1 Splitting Long Lines.
# "Outside of recipe lines, backslash/newlines are converted into a single space character.
# Once that is done, all whitespace around the backslash/newline is condensed into a single
# space: this includes all whitespace preceding the backslash, all whitespace at the beginning
# of the line after the backslash/newline, and any consecutive backslash/newline combina-
# tions."

class DebugVirtualLine(VirtualLine):
    # wrapper around VirtualLine which allows us to feed in strings that don't
    # strictly come from files
    def __init__(self, phys_lines_list):
        super().__init__(phys_lines_list, (0,0), "/dev/null")

def test_line_cont():
    test_list = ( 
        ( "this is a test\n",   False ),
        ( "this is a test\\\n", True ),
        ( "this is a test",     False),

        # Windows, DOS
        ( "this is a test\\\r\n", True ),
        ( "this is a test\\\n\r", True ),

        # short stuff
        ( "", False ),
        ( "\\", False ),
        ( "\\\n", True ),

    )

    for test in test_list : 
        test_string,result = test
        assert is_line_continuation(test_string)==result, (test_string,)

def test_vline():
    # Section 3.1.1  Splitting Long Lines.  
    # "Outside of recipe lines, backslash/newlines are converted into a single space character.
    # Once that is done, all whitespace around the backslash/newline is condensed into a single
    # space: this includes all whitespace preceding the backslash, all whitespace at the beginning
    # of the line after the backslash/newline, and any consecutive backslash/newline combina-
    # tions."  -- GNU Make 4.3 Jan 2020
    
    # use an array of strings as the input, just like python readlines() would return.
    test_list = ( 

    # from the gnu make manual
    ( "var:= one$\\\nword\n", "var:= one$ word\n"),

    ( "space=\\\nbar\n", "space= bar\n" ),

    # leading whitespace preserved
    ( "   foo=\\\nbar\n", "   foo= bar\n"),

    # single line (nothing to do)
    ( "foo : bar ; baz\n", "foo : bar ; baz\n"),

    ( "foo\\\nbar\\\nbaz\n", "foo bar baz\n"),

#    ( "backslash=\ \n", "backslash=\ \n"),

    # backslash then two blank lines w/ backslashes then end-of-string
    ( "space=\\\n\\\n\\\n\n", "space= \n" ),
    ( "space=\\\n    \\\n    \\\n\n", "space= \n" ),
    ( "space=\\\n    \\\n    \\\n   \n", "space= \n" ),

    # backslash joining foo: bar ; baz
    ( "foo\\\n:\\\nbar\\\n;\\\nbaz\n", "foo : bar ; baz\n" ),
    ( "foo\\\n   :\\\n   bar\\\n   ;\\\n   baz\n", "foo : bar ; baz\n" ),

    # from ffmpeg
    ( "SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \\\n" +
      "        HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \\\n" + 
      "        ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \\\n" +
      "        ALTIVEC-OBJS VIS-OBJS                                     \\\n" +
      "        MMX-OBJS YASM-OBJS                                        \\\n" +
      "        MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \\\n" +
      "        OBJS HOSTOBJS TESTOBJS\n",
     "SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS ALTIVEC-OBJS VIS-OBJS MMX-OBJS YASM-OBJS MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS OBJS HOSTOBJS TESTOBJS\n" ),

    (   "more-fun-in-assign\\\n" + 
        "=           \\\n" +
        "    the     \\\n" +
        "    leading \\\n" +
        "    and     \\\n" +
        "    trailing\\\n" +
        "    white   \\\n" +
        "    space   \\\n" +
        "    should  \\\n" +
        "    be      \\\n" +
        "    eliminated\\\n" +
        "    \\\n" +
        "    \\\n" +
        "    \\\n" +
        "    including \\\n" +
        "    \\\n" +
        "    \\\n" +
        "    blank\\\n" +
        "    \\\n" +
        "    \\\n" +
        "    lines\n",
        "more-fun-in-assign = the leading and trailing white space should be eliminated including blank lines\n" ),

    ( "literal-backslash\\=foo\\ \n", "literal-backslash\\=foo\\ \n"),

    ( "foo : # this comment\\\ncontinues on this line\n", "foo : # this comment continues on this line\n" ),

    # end of the tests list
    )

    for test in test_list : 
        # string, validation
        test_src,valid_str = test

        infile = io.StringIO(test_src)
        lines = infile.readlines()
        infile.close()

        vline = DebugVirtualLine( lines )

        test_result = str(vline)
        print("test_src=\n{0}".format(hexdump.dump(test_src,16)),end="")
        print("valid_str=\n{0}".format(hexdump.dump(valid_str,16)),end="")
        print("test_result=\n{0}".format(hexdump.dump(test_result,16)),end="")
        if test_result != valid_str:
            print("failed %r" % (test,))
            breakpoint()
        assert test_result==valid_str


def file_test(infilename):
    # load, print a file. The virtual line will hide the backslash line
    # continuations
    src = SourceFile(infilename)
    src.load()
    scanner = ScannerIterator(src.file_lines, infilename)
    vline_iter = get_vline(infilename, scanner)

    for vline in vline_iter:
        logger.info("@@%r >>%s<<", vline.starting_pos, printable_string(str(vline)))
        vline.validate()

    scanner = ScannerIterator(src.file_lines, infilename)
    vline_iter = get_vline(infilename, scanner)
    for v in vline_iter:
        print(str(v), end="")

def run_tests() : 
    test_line_cont()
    test_vline()
    # need moar tests!

def main():
    for f in sys.argv[1:]:
        file_test(f)

    if len(sys.argv) == 1:
        # run internal tests
        run_tests()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
