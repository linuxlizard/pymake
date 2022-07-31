#!/usr/bin/env python3

import logging
import string
import itertools

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
    # read a file, display vchar by vchar
    infilename = "test_vchar.py"

    lines = getfile(infilename)
    vline_iter = vline.get_vline(infilename, scanner.ScannerIterator(lines))

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

def test4():
    # rstrip
    infilename = "/dev/null"
    vs = vline.VCharString()
    counter = itertools.count()

    for char, col in zip("hello, world    ", counter):
        vs += vline.VChar(char, (0, col), infilename)
        logger.debug("char=%s col=%d len=%d vs=%s", char, col, len(vs), str(vs))

    vs.rstrip()
    assert str(vs)=="hello, world", "\"%s\""%str(vs)
    
def test5():
    # make a VCharString from a plain array of VChar
    # (act like str())
    infilename = "/dev/null"
    counter = itertools.count()

    vchar_list = [vline.VChar(char, (0,col), infilename) for char, col in zip("hello, world    ", counter)]
    logger.info(vchar_list)

    vs = vline.VCharString(vchar_list)
    logger.info("vs=\"%s\"", vs)

    vs.rstrip()
    assert str(vs)=="hello, world", "\"%s\""%str(vs)

def main():
#    test1()
#    test2()
    test3()
    test4()
    test5()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
