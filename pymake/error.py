#!/usr/bin/env python3

import sys

__all__ = [ "ParseError",
            "MakeError",
            "RecipeCommencesBeforeFirstTarget",
            "MissingSeparator",
            "InvalidFunctionArguments",
            "InvalidSyntaxInConditional",
            "EmptyVariableName",

            "warning_message",
            "error_message",

            "exit_status",
          ]

# from "EXIT STATUS" of make(1)
exit_status = {
    "success" : 0,
    "rebuild-required" : 1,
    "error" : 2,   # "errors were encountered"
}

# test/debug flags
# assert() in ParseError() constructor TODO make this a command line arg
assert_on_parse_error = False

class MakeError(Exception):
    # base class of all pymake exceptions
    description = "(No description!)" # useful description of the error
    default_msg = "(no message)"

    def __init__(self,*args,**kwargs):
        super().__init__(*args)
        self.code = kwargs.get("code",None)
        self.pos = kwargs.get("pos", ("missing",(-1,-1)))
        self.filename = self.pos[0]
        self.msg = kwargs.get("msg") or self.default_msg
        if "moremsg" in kwargs:
            self.msg += "; %s" % kwargs["moremsg"]

    def get_pos(self):
        return self.pos

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

class RecipeCommencesBeforeFirstTarget(ParseError):
    description = """\"Recipe Commmences Before First Target\"
Usually a parse error. Make has gotten confused by a RECIPEPREFIX (by default,
\\t (tab)) found at the start of line and thinks we've found a Recipe.  
TODO add more description here
"""
    default_msg = "recipe commences before first target"

class MissingSeparator(ParseError):
    description = """\"Missing Separator\"
Usually a parse error.  Make has found some text that
doesn't successfully parse into a rule or an expression.
-    Can happen when a Recipe doesn't the proper recipe prefix (default \\t (tab))
-    Can happen when a text transformation function "leaks" text into the parser
     where it should be captured by a variable.

TODO add better+more description here
"""
    default_msg = "missing separator"

class InvalidFunctionArguments(ParseError):
    description = """Arguments to a function are incorrect."""

class InvalidSyntaxInConditional(ParseError):
    default_msg = "invalid syntax in conditional"

class EmptyVariableName(ParseError):
    default_msg = "empty variable name"

#class VersionError(MakeError):
#    """Feature not in this version"""
#    pass

def warning_message(pos, msg):
    if pos:
        print("%s %r warning: %s" % (pos[0], pos[1], msg), file=sys.stderr)
    else:
        print("(pos unknown): %s" % (msg,), file=sys.stderr)

def error_message(pos, msg):
    if pos:
        print("%s %r: *** %s" % (pos[0], pos[1], msg), file=sys.stderr)
    else:
        print("*** %s" % msg, file=sys.stderr)

