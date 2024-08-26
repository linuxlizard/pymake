#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

# utilities to compare test results 

import itertools

def compare_result_stdout(expect, actual):
    # result is an iterable of strings expected in the output
    # actual is a single string of stdout/stderr with '\n' between the lines

    linelist = ( s.strip() for s in actual.split("\n") )

    # use zip_longest() to assure equal length
    fail = [ (a,b) for a,b in itertools.zip_longest(expect,linelist) if a != b ]
    assert not fail, fail

