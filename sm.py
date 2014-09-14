#!/usr/bin/env python3

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

import sys

# require Python 3.x for best Unicode handling
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

whitespace = set( ' \t\r\n' )

assignment = {"=","?=",":=","::=","+=","!="}

# 4.8 Special Built-In Target Names
built_in_targets = {
        ".PHONY",
        ".SUFFIXES",
        ".DEFAULT",
        ".PRECIOUS",
        ".INTERMEDIATE",
        ".SECONDARY",
        ".SECONDEXPANSION",
        ".DELETE_ON_ERROR",
        ".IGNORE",
        ".LOW_RESOLUTION_TIME",
        ".SILENT",
        ".EXPORT_ALL_VARIABLES",
        ".NOTPARALLEL",
        ".ONESHELL",
        ".POSIX",
    }

# Stuff from Appendix A.
directive = { 
              "define", "enddef", "undefine",
              "ifdef", "ifndef", "else", "endif", 
              "include", "-include", "sinclude",
              "override", "export", "unexport",
              "private",
              "vpath", 
            }
functions = { 
                "subst",
                "patsubst",
                "strip",
                "findstring",
                "filter",
                "filter-out",
                "sort",
                "word",
                "words",
                "wordlist",
                "firstword",
                "lastword",
                "dir",
                "notdir",
                "suffix",
                "basename",
                "addsuffix",
                "addprefix",
                "join",
                "wildcard",
                "realpath",
                "absname",
                "error",
                "warning",
                "shell",
                "origin",
                "flavor",
                "foreach",
                "if",
                "or",
                "and",
                "call",
                "eval",
                "file",
                "value",
            }
automatic_variables = {
                "@",
                "%",
                "<",
                "?",
                "^",
                "+",
                "*",
                "@D",
                "@F",
                "*D",
                "*F",
                "%D",
                "%F",
                "<D",
                "<F",
                "^D",
                "^F",
                "+D",
                "+F",
                "?D",
                "?F",
            }
builtin_variables = {
                "MAKEFILES",
                "VPATH",
                "SHELL",
                "MAKESHELL",
                "MAKE",
                "MAKE_VERSION",
                "MAKE_HOST",
                "MAKELEVEL",
                "MAKEFLAGS",
                "GNUMAKEFLAGS",
                "MAKECMDGOALS",
                "CURDIR",
                "SUFFIXES",
                ".LIBPATTEREN",
            }

class ParseError(Exception):
    pass

# tinkering with a class for tokens
#def Token(s): return s

class Token(object):
    def __init__(self,s):
        self.string = s

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string

def comment(string):
    state_start = 1
    state_eat_comment = 2

    state = state_start

    # this could definitely be faster (method in ScannerIterator to eat until EOL?)
    for c in string : 
#        print("c={0} state={1}".format(c,state))
        if state==state_start:
            if c=='#':
                state = state_eat_comment
            else:
                # shouldn't be here unless comment
                raise ParseError()
        elif state==state_eat_comment:
            # comments finish at end of line
            # FIXME handle \r\n,\n\r,\r and other weird line endings
            if c=='\n' :
                return
            # otherwise char is eaten
        else:
            assert 0, state

def eatwhite(string):
    # eat all whitespace (testing characters + sets)
    for c in string:
        if not c in whitespace:
            yield c

def tokenize_rule(string):
    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4

    state = state_start
    token = ""

    # a \x of these chars replaced by literal x
    backslashable = set("% :,")

    for c in string : 
        print("r c={0} state={1} token=\"{2}\"".format(c,state,token))
        if state==state_start:
            if c in whitespace : 
                # eat whitespace
                pass
            elif c==':':
                yield Token(":") 
                return
            else :
                # whatever it is, push it back so can tokenize it
                string.pushback()
                state = state_in_word

        elif state==state_in_word:
            if c=='\\':
                state = state_backslash

            elif c in whitespace :
                # end of word
                yield Token(token)
                # restart token
                token = ""
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # eat the comment 
                for t in comments(string):
                    yield t

            elif c==':':
                # end of target(s)
                
                # strip trailing whitespace
                yield Token(token.rstrip())

                yield Token(":")

                # just return for now
                # TODO tokenize prerequisites
                return

            else :
                token += c

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # return token so far
                yield Token(token)
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                for t in tokenize_variable_ref(string):
                    yield t
            state=state_in_word

        elif state==state_backslash :
            if c in backslashable : 
                token += c
            else :
                # literal '\' + somechar
                token += '\\'
                token += c
            state = state_in_word

        else:
            assert 0,state

    # don't raise error; just return assuming rest of string is happy 

def tokenize_variable_ref(string):
    
    state_start = 1
    state_dollar = 2
    state_in_var_ref = 3

    state = state_start
    token = ""

#    print( "state={0}".format(state))

    for c in string : 
        print("v c={0} state={1}".format(c,state))
        if state==state_start:
            if c=='$':
                state=state_dollar
            else :
                raise ParseError()
        elif state==state_dollar:
            # looking for '(' or '$' or some char
            if c=='(' or c=='{':
                opener = c
                state = state_in_var_ref
                yield Token("$"+c)
            elif c=='$':
                # literal "$$"
                yield Token("$$")
            elif not c in whitespace :
                # single letter variable, e.g., $@ $x $_ etc.
                token += c
                yield Token("$")
                yield Token(token)
                return 
        elif state==state_in_var_ref:
            if c==')' or c=='}':
                # TODO make sure to match the open/close chars
                yield Token(token)
                yield Token(c)
                return 
            elif c=='$':
                # nested expression!  :-O
                # if lone $$ token, preserve the $$ in the current token string
                # otherwise, recurse into parsing a $() expression
                if string.lookahead()=='$':
                    token += "$$"
                    string.next()
                else:
                    # return token so far
                    yield Token(token)
                    # restart token
                    token = ""
                    # push the '$' back onto the scanner
                    string.pushback()
                    # recurse into this scanner again
                    for t in tokenize_variable_ref(string):
                        yield t
                    # python 3.3 and above
                    #yield from tokenize_variable_ref(string)
            else:
                token += c

    raise ParseError()

class ScannerIterator(object):
    # string iterator that allows look ahead and push back
    def __init__(self,string):
        self.string = string
        self.idx = 0
        self.max_idx = len(self.string)

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.idx >= self.max_idx:
            raise StopIteration
        self.idx += 1
        return self.string[self.idx-1]

    def lookahead(self):
        if self.idx >= self.max_idx:
            raise StopIteration
#        print("lookahead={0}".format(self.string[self.idx]))
        return self.string[self.idx]

    def pushback(self):
        if self.idx <= 0 :
            raise StopIteration
        self.idx -= 1

def parse(infilename):
    infile = open(infilename)
    all_lines = infile.readlines()
    infile.close()

    s = "".join(all_lines)
    
    my_iter = ScannerIterator(s)

    new_makefile = "".join( [ c for c in eatwhite(comment(my_iter)) ] )
    print(new_makefile)

#    for c in comment(s):
#        print(c,end="")

def run_tests_list(tests_list,tokenizer):
    for test in tests_list :
        print("test={0}".format(test))
        s,result = test
        print("s={0}".format(s))
        my_iter = ScannerIterator(s)
        tokens = [ t for t in tokenizer(my_iter)] 
        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

        for v in zip(tokens,result):
#            print("\"{0}\" \"{1}\"".format(v[0].string,v[1]))
            assert  v[0].string==v[1], v

def variable_ref_test():

    tests_list = ( 
        # string    result
        ("$($$)",      ("$(","$$",")",)),
        ("$($$$$$$)",      ("$(","$$$$$$",")",)),
        ("$(CC)",   ("$(","CC",")")),
        ("$( )",   ("$("," ",")")),
        ("$(    )",   ("$(","    ",")")),
        ("$( CC )", ("$("," CC ", ")")),
        ("$(CC$$)",   ("$(","CC$$", ")")),
        ("$(CC$(LD))",   ("$(","CC","$(","LD",")","",")")),
        ("${CC}",   ("${","CC","}")),
        ("$@",      ("$", "@",)),
        ("$<",      ("$", "<",)),
        ("$F",      ("$","F",)),
#        ("$Ff",      ("$","F","f",)),
#        ("$F$f",      ("$","F","$","f",)),
#        ("$F$f$",      ("$$","$","F","$","f","$$",)),
        ("$($($(FOO)))",    ("$(","","$(","","$(","FOO",")","",")","",")")),
        ("$($($(FOO)a)b)c", ("$(","","$(","","$(","FOO",")","a",")","b",")")),
        ("$(a$(b$(FOO)a)b)c", ("$(","a","$(","b","$(","FOO",")","a",")","b",")")),
        ("$($($F)))",       ("$(","","$(","","$","F","",")","",")","",")")),
        ("$($($Fqq)))",     ("$(","","$(","","$","F","qq",")","",")","",")")),
        ("$(foo   )",       ("$(","foo   ",")")),
        ("$(info this is an info message)",     ("$(","info this is an info message",")")),
        ("$(error this is an error message)",   ("$(","error this is an error message",")")),
        ("$(findstring a,a b c)",               ("$(","findstring a,a b c",")")),
        ("$(patsubst %.c,%.o,x.c.c bar.c)",     ("$(","patsubst %.c,%.o,x.c.c bar.c",")")),
        ("$(filter %.c %.s,$(sources))",        ("$(",
                                                    "filter %.c %.s,",
                                                    "$(",
                                                    "sources",
                                                    ")",
                                                    "",
                                                    ")",
                                                )),
        ("$(objects:.o=.c)",        ("$(","objects:.o=.c",")",)),
        ("$(filter-out $(mains),$(objects))",   ("$(","filter-out ","$(","mains",")",",","$(","objects",")","",")","",")")),
        ("$(subst :, ,$(VPATH))",   ("$(","subst :, ,","$(","VPATH",")","",")")), # spaces are significant!
#        ("$(foo)$(\#)bar=thisisanother\#testtesttest", ("$(","k
        ("$(info = # foo#foo foo#foo foo#foo ###=# foo#foo foo#foo foo#foo ###)",
          ("$(","info = # foo#foo foo#foo foo#foo ###=# foo#foo foo#foo foo#foo ###",")")),
    )
    for test in tests_list :
        print("test={0}".format(test))
        s,result = test
        print("s={0}".format(s))
        my_iter = ScannerIterator(s)
        tokens = [ t for t in tokenize_variable_ref(my_iter)] 
        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

        for v in zip(tokens,result):
#            assert  v[0]==v[1], v
            assert  v[0].string==v[1], v

    # this should fail
#    print( "var={0}".format(tokenize_variable_ref(ScannerIterator("$(CC"))) )

def rules_test():
    rules_tests = ( 
        ( "all:",       ("all",":") ),
        ( "all:foo",    ("all",":","foo")),
        ( "   all :   foo    ", ("all",":","foo")),
        ( "the quick brown fox jumped over lazy dogs : ; ", ("the", "quick", "brown", "fox","jumped","over","lazy","dogs",":", ";", )),
        ( '"foo" : ; ',     ('"foo"',":",";")),
        ('"foo qqq baz" : ;',   ('"foo',"qqq",'baz"',":",";")),
        (r'\foo : ; ',  (r'\foo', ':', ';')),
        (r'foo\  : ; ', (r'foo ',':', ';',)),
        ('@:;@:',       ('@',':',';','@:',)),
        ('I\ have\ spaces : ; @echo $@',    ('I have spaces',':',';','@echo $@',)),
        ('I\ \ \ have\ \ \ three\ \ \ spaces : ; @echo $@', ('I   have   three   spaces',':', ';', '@echo $@' )),
        ('I$(CC)have$(LD)embedded$(OBJ)varref : ; @echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',
            ( 'I', '$(', 'CC', ')', 'have', '$(', 'LD',')','embedded','$(','OBJ',')','varref',':',';','@echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',)),
        ('$(filter %.o,$(files)): %.o: %.c',    
                    ( '', '$(','filter %.o,',
                            '$(','files',')','',
                       ')','',
                          ':','%.o',':','%.c',)),
    )
    run_tests_list( rules_tests, tokenize_rule )
#    for test in rules_tests : 
#        print("test={0}".format(test))
#        s = test
#        my_iter = ScannerIterator(s)
#
#        tokens = [ t for t in tokenize_rule(my_iter) ]
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

def test():
#    variable_ref_test()
    rules_test()
    pass

def main():
    import sys
    for infilename in sys.argv[1:]:
        parse(infilename)
    test()

if __name__=='__main__':
    main()

