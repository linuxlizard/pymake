#!/usr/bin/env python3

# Test tokenizing (eating) comments.

import pytest

from pymake.scanner import ScannerIterator
from pymake.printable import printable_string
from pymake.vline import get_vline
from pymake.source import SourceFile, SourceString

comments_test_list = ( 
    # string to test , the expected value after eating the comment
    ( "#foo\n", None ),
    ( "#\n",  None ),
    ( "# \nfoo:bar", "foo:bar" ),
    ( r"""# this is\
    a run on comment\
    that is annoying\
    and probably a \
    corner case
foo:bar""", "foo:bar" ),
    ( r"# I am a comment \\ with two backslashes", None ),
    ( r"# I am a comment \ with a backslash", None ),
)

@pytest.mark.parametrize("test_tuple", comments_test_list)
def test1(test_tuple):
    test_string, expected_result = test_tuple
#    print("test={0}".format(printable_string(test_string)))

    src = SourceString( test_string )
    src.load()
    scanner = ScannerIterator(src.file_lines, src.name)
    vline_iter = get_vline(src.name, scanner)

    try:
        oneline = next(vline_iter)
    except StopIteration:
        oneline = None

    if oneline is None:
        assert expected_result is None
    else:
        assert str(oneline) == expected_result, (str(oneline), expected_result)


