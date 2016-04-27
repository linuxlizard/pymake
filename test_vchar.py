#!/usr/bin/env python3

import logging

import vline
import scanner

logger = logging.getLogger("pymake.test_vchar")

def getfile(infilename):
    with open(infilename, "r") as infile:
        return infile.readlines()

def test1():
    vs = vline.VCharString()
    assert not len(vs)
    logging.debug("vs=\"{}\"".format(vs))

def test2():
    infilename = "test_vchar.py"

    lines = getfile(infilename)
    vline_iter = vline.get_vline(infilename, scanner.ScannerIterator(lines))

    for virt_line in vline_iter:
        for vchar in virt_line:
            assert vchar.filename == infilename, vchar.filename
            logger.info("%s %s ", vchar, vchar.pos)

def main():
    test1()
    test2()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
