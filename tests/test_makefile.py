#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import subprocess
import sys

import pytest
#import pymake

# Find file relative to tests location
test_dir = os.path.dirname(__file__)
example_dir = os.path.abspath(os.path.join(test_dir, '..', "pymake"))


def _run_makefile(infilename):
    if os.name == 'nt':
        pytest.skip("Make on Windows :s")

    filepath = os.path.join(example_dir, infilename)
    assert os.path.exists(filepath)

    m = subprocess.run(("make", "-f", filepath), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def _run_pymake(infilename):
    filepath = os.path.join(example_dir, infilename)
    assert os.path.exists(filepath)

    m = subprocess.run((sys.executable, "-m", "pymake.pymake", "-f", filepath), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout



infilename_list = ( 
    # same order as gnu make manual to make my brain work less

    # string functions
    "subst.mk",
    "patsubst.mk",
    "strip.mk",
    "findstring.mk", 
    "filter.mk", 
    "filter-out.mk",
    "sort.mk",
    "word.mk",
    "wordlist.mk",
    "words.mk",
    "firstword.mk",
    "lastword.mk",
    "functions_str.mk", # test all the things

    # filesystem functions
    "dir.mk",
    "notdir.mk",
    "suffix.mk",
    "basename.mk",
    "addsuffix.mk",
    "addprefix.mk",
    "join.mk",
    "wildcard.mk",
    "realpath.mk",
    "abspath.mk",

    # conditional functions
    "conditional.mk",

    # the Super Special Stuff
    "foreach.mk",
    # "file.mk",
    "call.mk",
#        "value.mk",  # FIXME my .makefile() surrounds single letter varrefs with () even if not in the original
    # "eval.mk",
    # "origin.mk",
    # "flavor.mk",
    # "shell.mk",
    # "variables.mk",
    "filepatsubst.mk",
    "undefine.mk",

    "info.mk",
    "ifeq.mk",
    "ifdef.mk",
    "ifeq-nested.mk",

    "recursive.mk",
)

@pytest.mark.parametrize("infilename", infilename_list)
def test_makefile(infilename):
    ground_truth = _run_makefile(infilename)
    test_output = _run_pymake(infilename)
    assert ground_truth == test_output


    # can I run pymake w/i pytest w/o spawning an additional python?
#    print(os.getcwd())
#    makefile = pymake.parse_makefile(infilename)
    
def test_value():
    # TODO need some way of testing value() function w/o running afoul of my $(P) problem
    # GNU Make: FOO = $PATH
    # I parse and regenerate that expression to:
    # FOO = $(P)ATH
    #
    # I like having my output with explicit varref even for single char names.
    # I just need to create a test that will work around this $(P) problem.
    pass

