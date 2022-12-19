#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import subprocess

# TODO these fns are copy/paste from test_makefile.py and need to be moved to
# somewhere common between those two files
def _run_makefile(infilename):
    m = subprocess.run(("make", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def _run_pymake(infilename):
    m = subprocess.run(("python3", "pymake.py", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def test1():
    makefile = """
CC=gcc
export CC
all:
	printenv
"""
    with tempfile.NamedTemporaryFile() as outfile:
        outfile.write(makefile)
        outfile.flush()
        test_output = _run_pymake(infilename)

