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
import hexdump
from vline import is_line_continuation, VirtualLine

# turn on the big global debug flags
import vline
vline._debug = True

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
    test_list = ( 
    # single line
    ( "foo : bar ; baz\n", "foo : bar ; baz\n"),
    ( "backslash=\ \n", "backslash=\ \n"),

    # backslash then blank line then end-of-string
    ( r"""space=\

""", "space= \n" ),

    # backslash joining rule + recipe
    ( r"""foo\
:\
bar\
;\
baz
""", "foo : bar ; baz\n" ),

    # another way to write the previous test
    ( "foo2\\\n:\\\nbar\\\n;\\\nbaz\n", "foo2 : bar ; baz\n" ),

    # from ffmpeg
    ( r"""SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \
               HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \
               ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \
               ALTIVEC-OBJS VIS-OBJS                                     \
               MMX-OBJS YASM-OBJS                                        \
               MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \
               OBJS HOSTOBJS TESTOBJS
""", "SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS ALTIVEC-OBJS VIS-OBJS MMX-OBJS YASM-OBJS MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS OBJS HOSTOBJS TESTOBJS\n" ),

    # stupid DOS \r\n 0x0d0a <cr><lf>
#    ( """supid-dos:\\\r\nis\\\r\nstupid\r\n""", () ),

    ( r"""more-fun-in-assign\
=           \
    the     \
    leading \
    and     \
    trailing\
    white   \
    space   \
    should  \
    be      \
    eliminated\
    \
    \
    \
    including \
    \
    \
    blank\
    \
    \
    lines
""", "more-fun-in-assign = the leading and trailing white space should be eliminated including blank lines\n" ),

    # This is a weird one. Why doesn't GNU Make give me two \\ here? I only get
    # one. Disable the test for now. Need to dig into make
#    ( r"""literal-backslash-2 = \\\
#        q
#""", "literal-backslash-2 = \\ q\n" ),
#
    ( "foo : # this comment\\\ncontinues on this line\n", 
      "foo : # this comment continues on this line\n" ),

    # end of the tests list
    )

    for test in test_list : 
        # string, validation
        s,v = test
#        print(s,end="")
#        print("s={0}".format(hexdump.dump(s,16)),end="")

        # VirtualLine needs an array of lines from a file.  The EOLs must be
        # preserved. But I want a nice easy way to make test strings (one
        # single string). 
        #
        # The incoming string will be one single string with embedded \n's
        # (rather than trying to create an array of strings by hand).
        # Split the test string by \n into an array. Then restore \n on each line.
        # The [:-1] skips the empty string after the final \n
        file_lines = s.split("\n")[:-1]
        lines = [ line+"\n" for line in file_lines ]
        
#        print( "split={0}".format(s.split("\n")))
#        print( "lines={0} len={1}".format(lines,len(lines)),end="")

        vline = VirtualLine( lines, 0 )
        for line in vline.virt_lines : 
            print(line)
        print(vline)

        s = str(vline)
        print("s={0}".format(hexdump.dump(s,16)))
        print("v={0}".format(hexdump.dump(v,16)))
        assert s==v


def file_test(infilename):
    # load, print a file. The virtual line will hide the backslash line
    # continuations
    src = SourceFile(infilename)
    src.load()
    scanner = ScannerIterator(src.file_lines)
    vline_iter = get_vline(infilename, scanner)

    for vline in vline_iter:
        logger.info("@@%d >>%s<<", vline.starting_file_line, vline)
        vline.validate()

def run_tests() : 
    test_line_cont()
    test_vline()
    # need moar tests!

def main():

    # run internal tests
#    run_tests()

    for f in sys.argv[1:]:
        file_test(f)

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
