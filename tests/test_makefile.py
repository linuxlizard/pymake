#!/usr/bin/env python3

import os
import subprocess

import pymake

def _run_makefile(infilename):
    m = subprocess.run(("make", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def _run_pymake(infilename):
    m = subprocess.run(("python3", "pymake.py", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)
    return m.stdout

def test_all():
    infilename_list = ( "filter.mk", "words.mk", "functions_str.mk")
    for infilename in infilename_list:
        ground_truth = _run_makefile(infilename)
        test_output = _run_pymake(infilename)
        assert ground_truth == test_output, infilename

    print(os.getcwd())
    makefile = pymake.parse_makefile(infilename)
    
    
