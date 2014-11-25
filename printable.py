#!/usr/bin/env python3

def printable_char(c):
    if ord(c) < 32:
        if c == '\t':
            return "\\t"
        if c == '\n':
            return "\\n"
        return "\\x{0:02x}".format(ord(c))
    if c == '\\': 
        return '\\\\'
    if c == '"': 
        return '\\"'
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
    return "".join( [ printable_char(c) for c in s ] )

