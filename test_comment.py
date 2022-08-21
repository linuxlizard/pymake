#!/usr/bin/env python3

# Test tokenizing (eating) comments.
# davep 27-sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from pymake import *

def run():
    comments_test_list = ( 
        # string to test , the expected value after eating the comment
        ( "#foo\n", "" ),
        ( "#\n", "" ),
        ( "# \nfoo:bar", "foo:bar" ),
        ( r"""# this is\
        a run on comment\
        that is annoying\
        and probably a \
        corner case
        foo:bar""", "        foo:bar" ),
        ( r"# I am a comment \\ with two backslashes", "" ),
        ( r"# I am a comment \ with a backslash", "" ),
    )

    for test in comments_test_list:
        s, expected_remain = test
        print("test={0}".format(printable_string(s)))

        line_scanner = ScannerIterator(s.split("\n"), "/dev/null")
        vline_iter = vline.get_vline("/dev/null", line_scanner)
        breakpoint()
        vl = next(vline_iter)
        print(vl)
        assert 0
        comment(next(vline_iter))
        remain = "".join([vchar.char for vchar in vchar_iter])
        print( "\"{}\" == \"{}\"".format(remain, expected_remain))
        assert remain == expected_remain

if __name__=='__main__':
    run()
