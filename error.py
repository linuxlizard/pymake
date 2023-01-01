#!/usr/bin/env python3

import sys

__all__ = [ "ParseError",
            "MakeError",
            "RecipeCommencesBeforeFirstTarget",
            "MissingSeparator",
            "InvalidFunctionArguments",

            "warning_message",
            "error_message",
          ]

# test/debug flags
# assert() in ParseError() constructor TODO make this a command line arg
assert_on_parse_error = False

class MakeError(Exception):
    # base class of all pymake exceptions
    description = "(No description!)" # useful description of the error

    def __init__(self,*args,**kwargs):
        super().__init__(*args)
        self.code = kwargs.get("code",None)
        self.pos = kwargs.get("pos", ("missing",(-1,-1)))
        self.filename = self.pos[0]
        self.msg = kwargs["msg"]

    def __str__(self):
        return "*** filename=\"{0}\" pos={1}: {2}".format(
                self.filename,self.pos[1],self.msg)
#        return "*** filename=\"{0}\" pos={1} src=\"{2}\": {3}".format(
#                self.filename,self.pos,str(self.code).strip(),self.msg)

class ParseError(MakeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if assert_on_parse_error : 
            # handy for stopping immediately to diagnose a parse error
            # (especially when the parse error is unexpected or wrong)
            assert 0

class RecipeCommencesBeforeFirstTarget(MakeError):
    description = """Usually a parse error. Make has gotten confused by a <tab>
(RECIPEPREFIX) found at the start of line and thinks we've found a Recipe.
TODO add more description here
"""

class MissingSeparator(MakeError):
    description = """Usually a parse error.  Make has found some text that
    doesn't successfully pares into a rule or an expression.
TODO add more description here
"""

class InvalidFunctionArguments(MakeError):
    description = """Arguments to a function are incorrect."""

#class VersionError(MakeError):
#    """Feature not in this version"""
#    pass

def warning_message(pos, msg):
    if pos:
        print("%s %r warning: %s" % (pos[0], pos[1], msg), file=sys.stderr)
    else:
        print("(pos unknown): %s" % (msg,), file=sys.stderr)

def error_message(pos, msg):
    print("%s %r: *** %s" % (pos[0], pos[1], msg), file=sys.stderr)

