#!/usr/bin/env python3

# Test tokenizing (eating) comments.
# davep 27-sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from sm import *
from run_tests import run_tests_list

def run():
    comments_test_list = ( 
        ( "#foo", "" ),
        ( "#", "" ),
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
        s,remain = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)
        comment( my_iter )
        print( "remain={0}".format(my_iter.remain()))
        assert my_iter.remain()==remain

if __name__=='__main__':
    run()
