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

assignment_operators = {"=","?=",":=","::=","+=","!="}
rule_operators = { ":", "::" }

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

class NestedTooDeep(Exception):
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

class Symbol(object):
    pass

class Literal(Symbol):
    # A literal found in the token stream. Store as a string.
    def __init__(self,string):
        self.string = string

    def __str__(self):
        return "Literal({0})".format(self.string)

class Expression(Symbol):
    pass

class VarRef(Expression):
    # A variable reference found in the token stream. Save as a nested set of
    # tuples representing a tree. 
    # $a            ->  VarExp(a)
    # $(abc)        ->  VarExp(abc,)
    # $(abc$(def))  ->  VarExp(abc,VarExp(def),)
    # $(abc$(def)$(ghi))  ->  VarExp(abc,VarExp(def),)
    # $(abc$(def)$(ghi))  ->  VarExp(abc,VarExp(def),VarExp(ghi),)
    # $(abc$(def)$(ghi$(jkl)))  ->  VarExp(abc,VarExp(def),VarExp(ghi,VarExp(jkl)),)
    # $(abc$(def)xyz)           ->  VarExp(abc,VarRef(def),Literal(xyz),)
    # $(info this is a varref)  ->  VarExp(info this is a varref)
    def __init__(self, token_list ):
        self.token_list = token_list

        # sanity check
#        print("token_list={0}".format(self.token_list))
        for t in self.token_list :
#            print("t={0} {1}".format(str(t),type(t)) )
            assert isinstance(t,Symbol), (type(t),t)

    def __str__(self):
        s = "VarRef("
        for t in self.token_list :
            s += str(t)
        s += ")"

        return s
        

class Assign(Expression):
    pass

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

def tokenize_assignment_or_rule(string):

    string.push_state()
    tokens = [ t for t in tokenize_statement_LHS(string) ]

    statement_type = "rule" if tokens[-1].string in rule_operators else "assign" 

    print( "last_token={0} ∴ statement is a {1}".format(tokens[-1],statement_type))
    if tokens[-1].string in rule_operators :
        print("re-run as rule")
        string.pop_state()
        # re-tokenize as a rule (backtrack)
        tokens = [ t for t in tokenize_statement_LHS(string,whitespace) ]

    return tokens

def tokenize_statement_LHS(string,separators=""):
    # formerly tokenize_rule()

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4
    state_colon = 5
    state_colon_colon = 6

    state = state_start
    token = ""

    # Before can disambiguate assignment vs rule, must parse forward enough to
    # find the operator. Otherwise, the LHS between assignment and rule are
    # identical.
    #
    # assignment ::= LHS assignment_operator RHS
    # rule       ::= LHS rule_operator RHS
    #

    # a \x of these chars replaced by literal x
    # XXX in both rule and assignment LHS? O_o
    backslashable = set("% :,")

    for c in string : 
        print("r c={0} state={1} token=\"{2}\"".format(c,state,token))
        if state==state_start:
            # always eat whitespace while in the starting state
            if c in whitespace : 
                # eat whitespace
                pass
            elif c==':':
                state = state_colon
            else :
                # whatever it is, push it back so can tokenize it
                string.pushback()
                state = state_in_word

        elif state==state_in_word:
            if c=='\\':
                state = state_backslash

            # whitespace in LHS of assignment is significant
            # whitespace in LHS of rule is ignored
            elif c in separators :
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
                # end of LHS (don't know if rule or assignment yet)
                # strip trailing whitespace
                yield Token(token.rstrip())
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peakahead
                if string.lookahead()=='=':
                    string.next()
                    yield Token(token.rstrip())
                    yield Token(c+'=')
                    return
                else:
                    token += c

            elif c=='=':
                # definitely an assignment 
                # strip trailing whitespace
                yield Token(token.rstrip())
                yield Token("=")
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
                # restore "$" + "(" in the string
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

        elif state==state_colon :
            # assignment end of LHS is := or ::= 
            # rule's end of target(s) is either a single ':' or double colon '::'
            if c==':':
                # double colon
                state = state_colon_colon
            elif c=='=':
                # :=
                yield Token(":=")
                # end of RHS
                return
            else:
                # Single ':' followed by something. Whatever it was, put it back!
                string.pushback()
                yield Token(":")
                # successfully found LHS 
                return
        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                yield Token("::=")
            else:
                string.pushback()
                yield Token("::")
            # successfully found LHS 
            return
        else:
            assert 0,state

    print("end of string! state={0}".format(state))

    # hit end of string; what was our final state?
    if state==state_colon:
        # ":"
        yield Token(":")
    elif state==state_colon_colon:
        # "::"
        yield Token("::")

    # don't raise error; just return assuming rest of string is happy 

depth = 0
def depth_reset():
    # reset the depth (used when testing the depth checker)
    global depth
    depth = 0

def depth_checker(func):
    def check_depth(*args):
        global depth
        depth += 1
        if depth > 10 : 
            raise NestedTooDeep(depth)
        ret = func(*args)
        depth -= 1

        # shouldn't happen!
        assert depth >= 0, depth 

        return ret

    return check_depth

@depth_checker
def tokenize_variable_ref(string):
    
    state_start = 1
    state_dollar = 2
    state_in_var_ref = 3

    state = state_start
    token = ""
    token_list = []

    sanity = 0

    for c in string : 
        sanity += 1
        assert sanity < 100, (sanity,depth)

#        print("v c={0} state={1} idx={2}".format(c,state,string.idx))
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
            elif c=='$':
                # literal "$$"
                token += "$"
            elif not c in whitespace :
                # single letter variable, e.g., $@ $x $_ etc.
                token_list.append( Literal(c) )
                return VarRef(token_list)
                # done tokenizing the var ref

        elif state==state_in_var_ref:
            if c==')' or c=='}':
                # end of var ref
                # TODO make sure to match the open/close chars

                # save what we've read so far
                token_list.append( Literal(token) )
                return VarRef(token_list)
                # done tokenizing the var ref

            elif c=='$':
                # nested expression!  :-O
                # if lone $$ token, preserve the $$ in the current token string
                # otherwise, recurse into parsing a $() expression
                if string.lookahead()=='$':
                    token += "$$"
                    string.next()
                else:
                    # save token so far
                    token_list.append( Literal(token) )
                    # restart token
                    token = ""
                    # push the '$' back onto the scanner
                    string.pushback()
                    # recurse into this scanner again
                    token_list.append( tokenize_variable_ref(string) )
            else:
                token += c

    raise ParseError()

class ScannerIterator(object):
    # string iterator that allows look ahead and push back
    def __init__(self,string):
        self.string = string
        self.idx = 0
        self.max_idx = len(self.string)
        self.state_stack = []

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

    def push_state(self):
        self.state_stack.append(self.idx)

    def pop_state(self):
        self.idx = self.state_stack.pop()

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

        assert len(tokens)==len(result), (len(tokens),len(result))

        for v in zip(tokens,result):
            print("\"{0}\" \"{1}\"".format(v[0].string,v[1]))
            assert  v[0].string==v[1], v

def variable_ref_test():

    variable_ref_tests = ( 
        # string    result
        ("$(CC)",   ("$(","CC",")")),
        ("$a",   ("$","a",)),
        ("$($$)",      ("$(","$$",")",)),
        ("$($$$$$$)",      ("$(","$$$$$$",")",)),
        ("$( )",   ("$("," ",")")),
        ("$(    )",   ("$(","    ",")")),
        ("$( CC )", ("$("," CC ", ")")),
        ("$(CC$$)",   ("$(","CC$$", ")")),
        ("$($$CC$$)",   ("$(","$$CC$$", ")")),
        ("$($(CC)$$)",   ("$(","$(","CC", "$$",")",")")),
        ("$($$$(CC)$$)",   ("$(","$$","$(","CC",")","$$", ")")),
        ("$(CC$(LD))",   ("$(","CC","$(","LD",")","",")")),
        ("${CC}",   ("${","CC","}")),
        ("$@",      ("$", "@",)),
        ("$<",      ("$", "<",)),
        ("$F",      ("$","F",)),
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

#    run_tests_list( variable_ref_tests, tokenize_variable_ref )
    
    for test in variable_ref_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_variable_ref(my_iter)
        print( "tokens={0}".format(str(tokens)) )
        print("\n")

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
            ( 'I', '$(', 'CC', ')', 'have', '$(', 'LD',')','embedded','$(','OBJ',')','varref',':',';',
              '@echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',)
        ),
        ('$(filter %.o,$(files)): %.o: %.c',    
                    ( '', '$(','filter %.o,',
                            '$(','files',')','',
                       ')','',
                          ':','%.o',':','%.c',)),
        ('aa$(filter %.o,bb$(files)cc)dd: %.o: %.c',    
                    ( 'aa', '$(','filter %.o,bb',
                            '$(','files',')','cc',
                       ')','dd',
                          ':','%.o',':','%.c',)),
        ("double-colon1 :: colon2", ("double-colon1","::","colon2")),
        ( "%.tab.c %.tab.h: %.y", ("%.tab.c","%.tab.h",":","%.y")),
        ("foo2:   # hello there; is this comment ignored?",("foo2",":")),
        ("$(shell echo target $$$$) : $(shell echo prereq $$$$)",
            ("","$(","shell echo target $$$$",")","",":","$(shell echo prereq $$$$)",),)
    )
    run_tests_list( rules_tests, tokenize_rule )
#    for test in rules_tests : 
#        print("test={0}".format(test))
#        s = test
#        my_iter = ScannerIterator(s)
#
#        tokens = [ t for t in tokenize_rule(my_iter) ]
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

def statement_test():
    rules_tests = ( 
        # rule LHS
        ( "all:",    ("all",":")),
        ( "all::",    ("all","::",)),
        # assignment LHS
        ( "all=foo",    ("all","=",)),
        ( "    all  =",    ("all","=")),
        ( "all:=",    ("all",":=",)),
        ( "all::=foo",    ("all","::=",)),
        ( "all?=foo",    ("all","?=",)),
        ( "all+=foo",    ("all","+=",)),
        ( "$(all)+=foo",    ("","$(","all",")","","+=",)),
        ( "qq$(all)+=foo",    ("qq","$(","all",")","","+=",)),
        ( "qq$(all)qq+=foo",    ("qq","$(","all",")","qq","+=",)),

        # kind of ambiguous
        ( "this is a test = ",           ("this is a test","=",) ),
        ( "  this   is   a   test   = ", ("this   is   a   test","=",) ),
        ( "this$(is) $a $test = ",      ("this ","$(","is",")"," ","$","a"," ","$","t","est","=",) ),
        ( "this $(  is  ) $a $test = ",  ("this ","$(","  is  ",")"," ","$","a"," ","$","t","est","=",) ),
        ( "this$(is)$a$(test) : ",       ("this","$(","is",")","","$","a","","$(","test",")","",":",) ),
        ( "this is a test : ",           ("this","is","a","test",":",) ),
        ( "  this   is   a   test   : ", ("this", "is","a","test",":",) ),
        ( "this $(is) $a $test : ",      ("this","$(","is",")","","$","a","","$","t","est","=",) ),

        # yadda yadda yadda
        ( "override all=foo",    ("override","all","=","foo")),
    )

#    for test in rules_tests : 
#        s,result = test
#        my_iter = ScannerIterator(s)
#        tokens = tokenize_assignment_or_rule(my_iter)
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

    run_tests_list( rules_tests, tokenize_assignment_or_rule)

@depth_checker
def recurse(foo,bar,baz):
    recurse(foo+1,bar+1,baz+1)

def test():
    assert isinstance(VarRef([]),Symbol)

    # $($(qq))
    v = VarRef( [VarRef([Literal("qq")]),] )
    print("v={0}".format(str(v)))

    try : 
        recurse(10,20,30)
    except NestedTooDeep:
        depth_reset()
    else:
        assert 0
    assert depth==0

    variable_ref_test()
#    rules_test()
#    statement_test()

def main():
    import sys
    for infilename in sys.argv[1:]:
        parse(infilename)
    test()

if __name__=='__main__':
    main()

