#!/usr/bin/env python3

import logging
import string
import itertools

import pymake.vline as vline
import pymake.scanner as scanner

logger = logging.getLogger("pymake.test_vchar")

def getfile(infilename):
    with open(infilename, "r") as infile:
        return infile.readlines()

def test1():
    vs = vline.VCharString()
    assert not len(vs)
    logging.debug("vs=\"{}\"".format(vs))

def test2():
    # read a file, display vchar by vchar
    infilename = "tests/test_vchar.py"

    lines = getfile(infilename)
    vline_iter = vline.get_vline(infilename, scanner.ScannerIterator(lines, infilename))

    for virt_line in vline_iter:
        for vchar in virt_line:
            assert vchar.filename == infilename, vchar.filename
            logger.info("%s %s ", vchar, vchar.pos)

def test3():
    # test string-like append
    infilename = "/dev/null"
    vs = vline.VCharString()
    counter = itertools.count()

    for char, col in zip(string.ascii_letters, counter):
        vs += vline.VChar(char, (0, col), infilename)
        logger.debug("char=%s col=%d len=%d vs=%s", char, col, len(vs), str(vs))
    

def main():
    test1()
    test2()
    test3()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
