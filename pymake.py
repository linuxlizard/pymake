#!/usr/bin/env python3

# Parse GNU Makefiles with 100% Python.
#
# Because I'm sick of trying to debug Makefiles with only GNU Make
#
# Notes:
#   Whitespace is very significant in variable assignments.
#
#   LIST =      a b c d e f   $(WAT)  g    <- extra trailing whitespace on string
#   $(info **$(LIST)**)
#
#   result:  **a b c d e f   1+1  g    **
#   Leading whitespace is trimmed. Trailing whitespace is preserved.
#
#
# davep 02-Sep-2014

import pyparsing
from pyparsing import Word, alphas, alphanums, nums, Optional, ZeroOrMore,\
                      Literal, Group, And, LineEnd, Or, ParseException,\
                      Optional,White,restOfLine, Suppress, printables,\
                      OneOrMore

#reserved_words = ( "ifdef", "ifndef", "endif", "else", "ifeq", "ifneq" )

# "A variable name may be any sequence of characters not containing ‘:’, ‘#’, ‘=’,
# or white- space. "

# FIXME - added '$(){}' to the exclude list but GNU Make accepts them.
exclude_chars=":#=$(){}"+White().DEFAULT_WHITE_CHARS
identifier = Word(printables,excludeChars=exclude_chars)("identifier")

valid_identifier_char = "".join( [ c for c in printables if c not in exclude_chars ] ) 
print(valid_identifier_char)

# Rules
colon = Literal(":")("literal")
double_colon = Literal("::")("literal")

# Variable Assignment
equal = Literal("=")("literal")
question_equal = Literal("?=")("literal")
colon_equal = Literal(":=")("literal")
colon_colon_equal = Literal("::=")("literal")
plus_equal = Literal("+=")("literal")
bang_equal = Literal("!=")("literal")

# TODO
# Add support for $[a-zA-Z] and other single char variable expressions
# e.g., $x $@ $< etc.   Make PDF 6.1
#
# Support $$

single_char_var = "$" + One

variable_ref = Or( ("$(" + identifier + ")", "${" + identifier + "}", "$"+valid_identifier_char) )

# discard any leading whitespace, preserve all trailing whitespace
assignment_rhs = Suppress(ZeroOrMore(White())) + restOfLine + LineEnd()
assignment = identifier + ( equal | question_equal | colon_equal \
                            | colon_colon_equal | plus_equal | bang_equal ) +\
                            Optional( assignment_rhs )

target = OneOrMore( identifier | variable_ref )

prerequsites = ZeroOrMore( identifier("prerequisite") ).setResultsName("prerequisite_list")

rule = target("target") + colon + prerequsites + LineEnd()

makefile = ZeroOrMore( assignment | rule )

makefile.ignore( pyparsing.pythonStyleComment )


def parse(infilename):
#    with open(infilename,"r") as infile:
#        lines = infile.readlines()
#
#    line = "".join(lines)
#    print(line)
#    tokens = makefile.parseString(line)
#    print( tokens )
#    return

    infile = open(infilename,"r") 
    if not infile : 
        print( "failed to open {0}".format(infilename))
        return

    while 1 : 
        line = infile.readline()
        # TODO check for '\' continuation lines
        if len(line)<=0:
            break
        line = line.strip()

        print( "line=\"{0}\"".format(line) )
#            tokens = makefile.ignore(pyparsing.pythonStyleComment).parseString(line)
        tokens = makefile.parseString(line)
        print( tokens )

    infile.close()

class ParseTest(object):
    def __init__(self,parser):
        self.parser = parser

    def report(self):
        print( "tokens={0}".format(self.tokens))

    def run(self,test_str):
        self.tokens = self.parser.parseString(test_str)
        self.report()
        return self.tokens

    def __call__(self,test_str):
        return self.run(test_str)

class ParseFailTest(ParseTest):
    # a parse that should fail
    def run(self,test_str):
        try : 
            tokens = self.parser.parseString(test_str)
        except ParseException:
            # expected to fail
            print("parse of \"{0}\" failed : OK".format(test_str))
            return None
        else:
            # this should have failed!
            raise Exception("Error: parse of \"{0}\" should have failed".format(test_str))

class RuleParseTest(ParseTest):
    # parse a rule; report extra info
    def report(self):
        print( "tokens={0} rule={1} target={2} prereqs={3}".format(
                self.tokens,self.tokens.rule,self.tokens.target,self.tokens.prerequisite_list) )

class IdentifierParseTest(ParseTest):
    def report(self):
        print( "tokens={0} identifier={1}".format(self.tokens,self.tokens.identifier))

def test():
    ########## 
    print("test comment")

    tokens = makefile.parseString("# this is a comment")
    print(tokens)

    ########## 
    print( "test identifier")

    test_identifier = IdentifierParseTest(identifier)
    test_identifier("foo")
    test_identifier("foo-bar")
    test_identifier("foo&bar")
    test_identifier("foo*bar")
    test_identifier("foo_bar")
    test_identifier("@")
    test_identifier("@")
    test_identifier("_")
    # the following are LEGAL but can't parse yet
    # yeah, these are going to be tough
#    test_identifier("$$")   
#    test_identifier("_()")

    ########## 
    print( "test variable refereneces")
    test_variable_ref = ParseTest(variable_ref)
    test_variable_ref("$(CC)")
    test_variable_ref("${CC}")  
    test_variable_ref("${ CC }")  
    test_variable_ref("$x")
    # these should fail
    fail_test_variable_ref = ParseFailTest(variable_ref)
    fail_test_variable_ref("$(patsubst %.c,%.o,x.c.c bar.c)")  
    fail_test_variable_ref("$(var :pattern =replacement )")

    ########## 
    print("test assignment")

    test_assign = ParseTest(assignment)
    test_assign("FOO=foo1")
    # empty rhs is valid
    test_assign("FOO=") 
    # rhs is pretty much a free-form string
    test_assign("WAT=1+1")
    test_assign("   WAT     = 1 + 1   ")
    test_assign("FOO2=foo1 foo2 foo3 foo4")
    # GNU make: leading whitespace is discarded; trailing whitespace is preserved
    # sample:
    # LIST =      a b c d e f g    
    # $(info **$(LIST)**)
    # result:
    # **a b c d e f g    **
    test_assign("LIST =      a b c d e f g    ")
    test_assign("LIST =      a b c d e f   $(CC)  g    ")

    test_assign("BAR:=bar2")
    test_assign("BAR::=bar2")
    test_assign("BAR?=bar2")
    test_assign("BAR+=bar3")
    test_assign("BAR!=bar3")
    test_assign("BAR=$(CC)")
    test_assign("BAR=$(strip a b c )")
    test_assign("BAR=$($(FOO))")
    test_assign("BAR=$($($(FOO)))")
    test_assign(" host-type := $(shell arch)")
#    return

    ########## 
    print("test rule")

    test_rule = RuleParseTest(rule)
    test_rule("all:foo")
    test_rule("foo:bar baz")
    test_rule("clean:")
    test_rule("a:b c d e f g h i j k l m n o p q r s t u v w x y z")
    test_rule("a42 : b_43")
    test_rule("a42 : b_43")
    test_rule("$(objects) : defs.h")
    test_rule("kbd.o command.o files.o : command.h")


    tst="""
        FOO=1
        all : foo
        clean : 
    """
    
    print("test makefile")
    for s in tst.split("\n"):
        tokens = makefile.parseString(s)
        print( "tokens={0} {1}".format(tokens,type(tokens)) )
#        print( "tokens={0}".format(tokens.asXML()) )

def main() : 
    import sys

    test()
    return

    if len(sys.argv):
        parse(sys.argv[1])

if __name__=='__main__':
    main()

