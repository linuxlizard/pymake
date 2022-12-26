#!/usr/bin/env python3

import sys

__all__ = [ "ParseError",
            "MakeError",
#            "NestedTooDeep",
#            "Unimplemented",
#            "VersionError",
#            "EvalError",
            "warning_message",
            "error_message",
          ]

# test/debug flags
# assert() in ParseError() constructor TODO make this a command line arg
assert_on_parse_error = False

class MakeError(Exception):
    # base class of all pymake exceptions
    filename = None   # filename containing the error
    pos = (-1, -1)  # row/col of position, zero based
    code = None  # code line that caused the error (a VirtualLine)
    description = "(No description!)" # useful description of the error

    def __init__(self,*args,**kwargs):
        super().__init__(*args)
        self.code = kwargs.get("code",None)
        self.pos = kwargs.get("pos", ("missing",(-1,-1)))
        self.filename = self.pos[0]
        self.description = kwargs.get("description", "(missing description)")

    def __str__(self):
        return "*** filename=\"{0}\" pos={1}: {2}".format(
                self.filename,self.pos[1],self.description)
#        return "*** filename=\"{0}\" pos={1} src=\"{2}\": {3}".format(
#                self.filename,self.pos,str(self.code).strip(),self.description)

class ParseError(MakeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if assert_on_parse_error : 
            # handy for stopping immediately to diagnose a parse error
            # (especially when the parse error is unexpected or wrong)
            assert 0

#class NestedTooDeep(MakeError):
#    pass

class Unimplemented(MakeError):
    """Feature not yet implemented"""
    pass

#class VersionError(MakeError):
#    """Feature not in this version"""
#    pass

#class EvalError(MakeError):
#    """execution error e.g., bad function call"""
#    pass

def warning_message(pos, msg):
    if pos:
        print("%s %r warning: %s" % (pos[0], pos[1], msg), file=sys.stderr)
    else:
        print("(pos unknown): %s" % (msg,), file=sys.stderr)

def error_message(pos, msg):
    print("%s %r: %s" % (pos[0], pos[1], msg), file=sys.stderr)

