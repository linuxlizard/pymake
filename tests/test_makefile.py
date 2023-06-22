#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import subprocess
import sys
import re

import pytest
#import pymake

# Find file relative to tests location
test_dir = os.path.dirname(__file__)
example_dir = os.path.abspath(os.path.join(test_dir, '..', "tests"))


def _run_makefile(infilename):
    if os.name == 'nt':
        pytest.skip("Make on Windows :s")

    filepath = os.path.join(example_dir, infilename)
    assert os.path.exists(filepath)

    m = subprocess.run(("make", "-f", filepath), 
                        shell=False, 
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
#    print(m.stdout)
    return m.stdout

def _run_pymake(infilename):
    filepath = os.path.join(example_dir, infilename)
    assert os.path.exists(filepath)

    m = subprocess.run((sys.executable, "-m", "pymake.pymake", "-f", filepath), 
                        shell=False, 
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
#    print(m.stdout)
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
    # "define.mk",
    "undefine.mk",

    "info.mk",
    "ifeq.mk",
    "ifdef.mk",
    "ifeq-nested.mk",

    "recursive.mk",  # FIXME this is a bad filename (does not test recursive make)
    "assign.mk",
    "multiline.mk",
    "ignoreandsilent.mk",
    # "automatic.mk",
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

def test_submake():
    # My sub-make output doesn't exactly match GNU-Make's output so need to run
    # the sub-make test separately.
    infilename = "submake.mk"
    ground_truth = _run_makefile(infilename)
#    print("output=",ground_truth)
    # 20230621 as of this writing, I don't announce the depth or directory
    truth_strlist = [s for s in ground_truth.decode('utf8').split("\n") if not s.startswith("make[1]")]

    test_output = _run_pymake(infilename)
#    print("output=",test_output)
    test_strlist = test_output.decode('utf8').split("\n")

    # clean up some of the variable parts 
    pid_re = re.compile("pid=[0-9]+")

    def clean(s):
        s = re.sub(pid_re,"pid=",s)
        s = s.replace("py-submake","make")
        return s

    for result in zip(truth_strlist,test_strlist):
        print("%r" % (result,))
        truth,test = [clean(s) for s in result]
#        print(truth,test)
        assert truth==test
        

