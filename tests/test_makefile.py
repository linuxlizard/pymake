#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import subprocess

#import pymake

def _run_makefile(infilename):
    m = subprocess.run(("make", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def _run_pymake(infilename):
    m = subprocess.run(("python3", "pymake.py", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def test_all():
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
        "filepatsubst.mk",
        "undefine.mk",

        "info.mk",
        "ifeq.mk",
        "ifdef.mk",
        "ifeq-nested.mk",
    )

    for infilename in infilename_list:
        ground_truth = _run_makefile(infilename)
        test_output = _run_pymake(infilename)
        assert ground_truth == test_output, infilename


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

