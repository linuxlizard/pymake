import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from symbol import *
from parser import parse_ifeq_directive
from vline import VirtualLine
from pymake import tokenize_statement

def test1():
    s = "ifeq '$a' '$b'"
    vline = VirtualLine([s], (0,0), "/dev/null")
    stmt = tokenize_statement(iter(vline))

if __name__ == '__main__':
    test1()

