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

#whitespace = set( ' \t\r\n' )
whitespace = set( ' \t' )

assignment_operators = {"=","?=",":=","::=","+=","!="}
rule_operators = { ":", "::" }
eol = set("\r\n")

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

#
#  Class Hierarchy for Tokens
#
class Symbol(object):
    # base class of everything we find in the makefile
    def __init__(self,string):
        # by default, save the token's string 
        # (descendent classes could store something differnet)
        self.string = string

    def __str__(self):
        # create a string such as "Literal(all)"
        return "{0}({1})".format(self.__class__.__name__,self.string)

class Literal(Symbol):
    # A literal found in the token stream. Store as a string.
    pass

class Operator(Symbol):
    pass

class AssignOp(Operator):
    # An assignment symbol, one of { = , := , ?= , += , != , ::= }
    pass
    
class RuleOp(Operator):
    # A rule sumbol, one of { : , :: }
    pass
    
class Expression(Symbol):
    # An expression is a list of symbols.
    def __init__(self, token_list ):
        self.token_list = token_list

        # sanity check
        for t in self.token_list :
            assert isinstance(t,Symbol), (type(t),t)

    def __str__(self):
        # return a ()'d list of our tokens
        s = "{0}(".format(self.__class__.__name__)
        for t in self.token_list :
            s += str(t)
        s += ")"
        return s

    def __getitem__(self,idx):
        return self.token_list[idx]

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

    pass

class AssignmentExpression(Expression):
    def __init__(self,token_list):
        Expression.__init__(self,token_list)

        # AssignmentExpression :=  Expression AssignOp Expression
        assert len(self.token_list)==3,len(self.token_list)
        assert isinstance(self.token_list[0],Expression)
        assert isinstance(self.token_list[1],AssignOp)
        assert isinstance(self.token_list[2],Expression),(type(self.token_list[2]),)

class RuleExpression(Expression):
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

depth = 0
def depth_reset():
    # reset the depth (used when testing the depth checker)
    global depth
    depth = 0

def depth_checker(func):
    # Avoid very deep recurssion into tokenizers.
    # Note this uses a global so is NOT thread safe.
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
def tokenize_assignment_or_rule(string):
    # at start of scanning, we don't know if this is a rule or an assignment
    # this is a test : foo   -> (this,is,a,test,:,)
    # this is a test = foo   -> (this is a test,=,)
    #
    # I tokenize assuming it's an assignment statement. If the final token is a
    # rule token, then I re-tokenize as a rule.
    #

    # save current position in the token stream
    string.push_state()
    lhs = tokenize_statement_LHS(string)
    
    assert type(lhs)==type(())
    for token in lhs : 
        assert isinstance(token,Symbol),(type(token),token)

    statement_type = "rule" if lhs[-1].string in rule_operators else "assignment" 

    print( "last_token={0} ∴ statement is {1}".format(lhs[-1],statement_type))
    if lhs[-1].string in rule_operators :
        print("re-run as rule")
        string.pop_state()
        # re-tokenize as a rule (backtrack)
        lhs = tokenize_statement_LHS(string,whitespace)
    
        # add rule RHS
        statement = list(lhs)
        statement.append( tokenize_rule_RHS(string) )

        return RuleExpression( statement ) 

    # The statement is an assignment. Tokenize rest of line as an assignment.
    statement = list(lhs)
    statement.append(tokenize_assign_RHS( string ))
    return AssignmentExpression( statement )

@depth_checker
def tokenize_statement_LHS(string,separators=""):
    # Tokenize the LHS of a rule or an assignment statement. A rule uses
    # whitespace as a separator. An assignment statement preserves internal
    # whitespace but leading/trailing whitespace is stripped.

    state_start = 1
    state_in_word = 2
    state_dollar = 3
    state_backslash = 4
    state_colon = 5
    state_colon_colon = 6

    state = state_start
    token = ""

    token_list = []

    # Before can disambiguate assignment vs rule, must parse forward enough to
    # find the operator. Otherwise, the LHS between assignment and rule are
    # identical.
    #
    # BNF is sorta
    # assignment ::= LHS assignment_operator RHS
    # rule       ::= LHS rule_operator RHS
    #

    # a \x of these chars replaced by literal x
    # XXX in both rule and assignment LHS? O_o
    backslashable = set("% :,")

    for c in string : 
#        print("r c={0} state={1} token=\"{2}\"".format(c,state,token))
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
                token_list.append( Literal(token) )

                # restart token
                token = ""

                # jump back to start searching for next symbol
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c=='#':
                # eat the comment 
                string.pushback()
                comment(string)

            elif c==':':
                # end of LHS (don't know if rule or assignment yet)
                # strip trailing whitespace
                token_list.append( Literal(token.rstrip()) )
                state = state_colon

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peakahead
                if string.lookahead()=='=':
                    string.next()
                    token_list.append(Literal(token.rstrip()))
                    return Expression(token_list),AssignOp(c+'=')
                else:
                    token += c

            elif c=='=':
                # definitely an assignment 
                # strip trailing whitespace
                token_list.append(Literal(token.rstrip()))
                return Expression(token_list),AssignOp("=")
                
            else :
                token += c

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token so far; note no rstrip()!
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

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
                # end of RHS
                return Expression(token_list), AssignOp(":=") 
            else:
                # Single ':' followed by something. Whatever it was, put it back!
                string.pushback()
                # successfully found LHS 
                return Expression(token_list),RuleOp(":")
        elif state==state_colon_colon :
            # preceeding chars are "::"
            if c=='=':
                # ::= 
                return Expression(token_list), AssignOp("::=") 
            string.pushback()
            # successfully found LHS 
            return Expression(token_list), RuleOp("::") 
        else:
            assert 0,state

    # hit end of string; what was our final state?
    if state==state_colon:
        # ":"
        return Expression(token_list), RuleOp(":") 
    elif state==state_colon_colon:
        # "::"
        return Expression(token_list), RuleOp("::") 

    # don't raise error; just return assuming rest of string is happy 

@depth_checker
def tokenize_assign_RHS(string):
    pass

@depth_checker
def tokenize_assign_RHS(string):

    state_start = 1
    state_dollar = 2
    state_literal = 3
    state_eol = 4

    state = state_start
    token = ""
    token_list = []

    for c in string :
        print("a c={0} state={1} idx={2}".format(c,state,string.idx))
        if state==state_start :
            if c=='$':
                state = state_dollar
            elif c=='#':
                string.pushback()
                # eat comment until end of line
                comment(string)
                # bye!
                return Expression(token_list)
            elif not c in whitespace :
                string.pushback()
                state = state_literal

            # default will eat leading whitespace
            # once we leave the state state, we will never return
            # (all whitespace after leading whitespace is preserved)

        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token so far; note no rstrip()!
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state = state_literal

        elif state==state_literal:
            if c=='$' :
                state = state_dollar
            elif c=='#':
                string.pushback()
                # eat comment until end of line
                comment(string)
                # bye!
                token_list.append(Literal(token))
                return Expression(token_list)
            elif c in eol :
                state = state_eol
            else:
                token += c

        elif state==state_eol :
            if not c in eol :
                string.pushback()
                token_list.append(Literal(token))
                return Expression(token_list)

    # end of string
    # save what we've seen so far
    token_list.append(Literal(token))
    return Expression(token_list)

@depth_checker
def tokenize_variable_ref(string):
    # Tokenize a variable reference e.g., $(expression) or $c 
    # Handles nested expressions e.g., $( $(foo) )
    # Returns a VarExp object.

    state_start = 1
    state_dollar = 2
    state_in_var_ref = 3

    state = state_start
    token = ""
    token_list = []

    for c in string : 
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
                    token += "$"
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

def parse_file(infilename):
    infile = open(infilename)
    all_lines = infile.readlines()
    infile.close()

    s = "".join(all_lines)
    
    my_iter = ScannerIterator(s)

    # TODO
    assert 0

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
        ("$Ff",      ("$","F","f",)),
        ("$F$f",      ("$","F","$","f",)),
        ("$F$f$",      ("$$","$","F","$","f","$$",)),
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

        ( "all:",       ("all",":") ),
        ( "all:foo",    ("all",":","foo")),
        ( "   all :   foo    ", ("all",":","foo")),
        ( "the quick brown fox jumped over lazy dogs : ; ", 
            ("the", "quick", "brown", "fox","jumped","over","lazy","dogs",":", ";", )),
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
#    for test in rules_tests : 
#        s,result = test
#        my_iter = ScannerIterator(s)
#        tokens = tokenize_assignment_or_rule(my_iter)
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

    for test in rules_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )
        print("\n")
#    run_tests_list( rules_tests, tokenize_assignment_or_rule)

def assignment_test():

    assignment_tests = ( 
        ("foo=baz",""),
        ("foo=$(baz)",""),
        ("foo=$(baz3) $(baz3) $(baz3)",""),

        # leading spaces discarded, trailing spaces preserved
        ("foo=     $(baz3) $(baz3) $(baz3)",""),
        ("foo= this is a test # this is a comment",""),
        ("foo= this is a test # this is a comment\nbar=baz",""),

        # empty is fine, too
        ( "foo=", ""),
        ( " foo =     ", "" ),

        # assignment done at eol
        ( "foo=$(CC)\nfoo bar baz=$(LD)\n", "" ), 

        ( "today != $(shell date)", "" ),
        ( "this is a test = this is a test", "" ),
    )

    for test in assignment_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )

        # AssignmentExpression :=  Expression AssignOp Expression
        assert isinstance(tokens,AssignmentExpression)
        assert isinstance(tokens[0],Expression)
        assert isinstance(tokens[1],AssignOp)
        assert isinstance(tokens[2],Expression),(type(tokens[2]),)

#        print( "string={0}".format(my_iter))
        print("\n")

@depth_checker
def recurse_test(foo,bar,baz):
    recurse_test(foo+1,bar+1,baz+1)

def internal_tests():
    assert isinstance(VarRef([]),Symbol)

    # $($(qq))
    v = VarRef( [VarRef([Literal("qq")]),] )
    print("v={0}".format(str(v)))

    try : 
        recurse_test(10,20,30)
    except NestedTooDeep:
        depth_reset()
    else:
        assert 0
    assert depth==0

def test():
#    internal_tests()
#    variable_ref_test()
#    statement_test()
    assignment_test()

def main():
    import sys
    for infilename in sys.argv[1:]:
        parse_file(infilename)
    test()

if __name__=='__main__':
    main()

