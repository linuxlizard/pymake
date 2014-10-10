#!/usr/bin/env python3

# A few times I've accidentally fed my python scripts to my makefile parser
# Yes, it's a silly test but as of this writing my parser will successfully
# accept this file (!).
# davep 08-Oct-2014

import sys

import itertools

import hexdump
from sm import *

eol = set("\r\n")
whitespace = set( ' \t' )

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

