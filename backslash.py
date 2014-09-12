#!/usr/bin/env python3

# How does GNU Make handle \'s ?
# davep 11-Sep-2014

import sys
import subprocess
import pyparsing

# require Python 3.x for best Unicode handling
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

makefile="""
$(info {0})

all: ; @:
"""

def main():
    cmd = "make -f tst.mk".split()

    bad = set("()")
    test_chars = set(pyparsing.printables)-bad

    with open("tst.mk",'w') as outfile:
        for char in test_chars:
            outfile.write("a={0}\n".format('\\'+char))
            outfile.write("$(info {0}=$a)\n".format(char))
        outfile.write("all:;@:\n")

    s = subprocess.check_output(cmd,shell=False)
    # strip \n
    s = s[:-1]
    print("{0}={1}".format(char,s))

if __name__=='__main__':
    main()

