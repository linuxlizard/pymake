#!/usr/bin/env python3

# 
#  This module completely 100% utterly ignores Unicode.
#  Shame on me.
#  But it's only used for debugging.
#

def printable_char(c):
    if ord(c) < 32 or ord(c) > 127:
        if c == '\t':
            return "\\t"
        if c == '\n':
            return "\\n"
        if c == '\r':
            return "\\r"
        return "\\x{0:02x}".format(ord(c))

    if c == '\\': 
        return '\\\\'
#    if c == '"': 
#        return '\\"'
    return c

def printable_string(s): 
    # Convert a string with unprintable chars and/or weird printing chars into
    # something that can be printed without side effects.
    # For example, 
    #   <tab> -> "\t"   
    #   <eol> -> "\n"
    #   "     -> \"
    #
    # Want to be able to round trip the output of the Symbol hierarchy back
    # into valid Python code.
    #
    return "".join([printable_char(c) for c in s])

if __name__ == '__main__':
    # showing the difference between '%r' and my fn.
    for i in range(256):
        print("%r" % chr(i), printable_char(chr(i)))

    s = "".join(chr(i) for i in range(256))
    print(printable_string(s))

    s = "".join("%r"%chr(i) for i in range(256))
    print(printable_string(s))

