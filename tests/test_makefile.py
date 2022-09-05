#!/usr/bin/env python3

import subprocess

def _run_makefile(infilename):
    m = subprocess.run(("make", "-f", infilename), shell=False, check=True, capture_output=True)
    print(m.stdout)


def test_all():
    infilename = "filter.mk"
    _run_makefile(infilename)
    
    
