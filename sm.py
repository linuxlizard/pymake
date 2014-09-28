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

# eventually will need to port this thing to Windows' CR+LF
platform_eol = "\n"

recipe_prefix = "\t"

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
        # TODO handle embedded " and ' (with backslashes I guess?)
        return "{0}(\"{1}\")".format(self.__class__.__name__,self.string)
#        return "{0}({1})".format(self.__class__.__name__,self.string)

    def __eq__(self,rhs):
        # lhs is self
        return self.string==rhs.string

    def makefile(self):
        # create a Makefile from this object
        return self.string

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
#            print("t={0}".format( t ) )
            assert isinstance(t,Symbol), (type(t),t)

    def __str__(self):
        # return a ()'d list of our tokens
        s = "{0}( [".format(self.__class__.__name__)
        if 0:
            for t in self.token_list :
                s += str(t)
        else:
            s += ",".join( [ str(t) for t in self.token_list ] )
        s += "])"
        return s

    def __getitem__(self,idx):
        return self.token_list[idx]

    def __eq__(self,rhs):
        # lhs is self
        # rhs better be another expression
        assert isinstance(rhs,Expression),(type(rhs),rhs)

        if len(self.token_list) != len(rhs.token_list):
            return False

        for tokens in zip(self.token_list,rhs.token_list) :
            if tokens[0].__class__ != tokens[1].__class__ : 
                return False

            # Recurse into sub-expressions. It's tokens all the way down!
            if not tokens[0] == tokens[1] :
                return False

        return True

    def makefile(self):
        # Build a Makefile string from this rule expression.
        s = ""
        for t in self.token_list : 
            s += t.makefile()
        return s
            

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

    def makefile(self):
        s = "$("
        for t in self.token_list : 
            s += t.makefile()

        s += ")"
        return s

class AssignmentExpression(Expression):
    def __init__(self,token_list):
        # AssignmentExpression :=  Expression AssignOp Expression
        assert len(token_list)==3,len(token_list)
        assert isinstance(token_list[0],Expression)
        assert isinstance(token_list[1],AssignOp)
        assert isinstance(token_list[2],Expression),(type(token_list[2]),)

        Expression.__init__(self,token_list)

class RuleExpression(Expression):
    # add sanity check in constructor
    def __init__(self, token_list):
        assert len(token_list)==4,len(token_list)

        assert isinstance(token_list[0],Expression)
        assert isinstance(token_list[1],RuleOp)
        assert isinstance(token_list[2],PrerequisiteList)
        assert isinstance(token_list[3],RecipeList)

        Expression.__init__(self,token_list)

    def makefile(self):
        # rule-targes rule-op prereq-list <CR>
        #     recipes
        assert len(self.token_list)==4,len(self.token_list)
        s = "".join( [ self.token_list[i].makefile() for i in range(0,3) ] )
        recipe_list = self.token_list[3].makefile()
        if recipe_list : 
            s += "\n"
            s += recipe_list
        return s

class PrerequisiteList(Expression):
    def makefile(self):
        # space separated
        s = " ".join( [ t.makefile() for t in self.token_list ] )
        return s

class Recipe(Expression):
    # A single line of a recipe

#    def makefile(self):
#        s = "".join( [ t.makefile() for t in self.token_list ] )
#        return s
    pass

class RecipeList( Expression ) : 
    # A collection of Recipe objects

    def makefile(self):
        # newline separated, tab prefixed
        s = ""
        print(self.token_list)
        if len(self.token_list):
            s = "\t"+"\n\t".join( [ t.makefile() for t in self.token_list ] )
        return s

class Makefile(Expression) : 
    # a collection of statements, directives, rules

    def makefile(self):
        # newline separated
        s = "\n".join( [ t.makefile() for t in self.token_list ] )
        return s

def comment(string):
    state_start = 1
    state_eat_comment = 2
    state_backslash = 3

    state = state_start

    # this could definitely be faster (method in ScannerIterator to eat until EOL?)
    for c in string : 
        print("c c={0} state={1}".format(filter_char(c),state))
        if state==state_start:
            if c=='#':
                state = state_eat_comment
            else:
                # shouldn't be here unless we're eating a comment
                raise ParseError()

        elif state==state_eat_comment:
            # comments finish at end of line
            if c in eol :
                return
            elif c == '\\':
                state = state_backslash
            # otherwise char is eaten

        elif state==state_backslash:
            state = state_eat_comment

        else:
            assert 0, state

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
    # Only difference between a rule LHS and an assignment LHS is the
    # whitespace. In a rule, the whitespace is ignored. In an assignment, the
    # whitespace is preserved.

    # save current position in the token stream
    string.push_state()
    lhs = tokenize_statement_LHS(string)
    
    assert type(lhs)==type(()), (type(lhs),)
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
        # rule RHS  ::= assignment
        #           ::= prerequisite_list
        #           ::= <empty>
        statement = list(lhs)
        statement.append( tokenize_rule_prereq_or_assign(string) )

        # tokenize the recipe list (could be empty)
        statement.append( tokenize_recipe_list( string ) )

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
#    backslashable = set("%:,")

    for c in string : 
        print("s c={0} state={1} idx={2} ".format(
                filter_char(c),state,string.idx,token))
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
                # cheat and peekahead
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
            if c in eol : 
                # line continuation
                pass
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
    print(string.string)
    assert 0, (state,string.remain(),)

@depth_checker
def tokenize_rule_prereq_or_assign(string):
    # We are on the RHS of a rule's : or ::
    # We may have a set of prerequisites
    # or we may have a target specific assignment.
    # or we may have nothing at all!
    #
    # End of the rule's RHS is ';' or EOL.  The ';' may be followed by a
    # recipe.

    # save current position in the token stream
    string.push_state()
    rhs = tokenize_rule_RHS(string)

    # Not a prereq. We found ourselves an assignment statement.
    if rhs is None : 
        string.pop_state()

        # We have target-specifc assignment. For example:
        # foo : CC=intel-cc
        # retokenize as an assignment statement
        lhs = tokenize_statement_LHS(string)
        statement = list(lhs)

        assert lhs[-1].string in assignment_operators

        statement.append( tokenize_assign_RHS(string) )
        rhs = AssignmentExpression( statement )
    else : 
        assert isinstance(rhs,PrerequisiteList)

    # stupid human check
    for token in rhs : 
        assert isinstance(token,Symbol),(type(token),token)

    return rhs

@depth_checker
def tokenize_rule_RHS(string):

    # RHS ::=                       -->  empty perfectly valid
    #     ::= symbols               -->  simple rule's prerequisites
    #     ::= symbols : symbols     -->  implicit pattern rule
    #     ::= symbols | symbols     -->  order only prerequisite
    #     ::= assignment            -->  target specific assignment 
    #
    # RHS terminated by comment, EOL, ';'
    state_start = 1
    state_word = 2
    state_colon = 3
    state_double_colon = 4
    state_dollar = 5
    state_whitespace = 6
    state_backslash = 7

    state = state_start
    token = ""
    token_list = []

    for c in string :
        print("p c={0} state={1} idx={2}".format(filter_char(c),state,string.idx))

        if state==state_start :
            if c==';':
                # End of prerequisites; start of recipe.  Note we don't
                # preserve token because it will be empty at this point.
                # bye!
                # XXX pushback ';' ? I think I need to for the recipe
                # tokenizer.
                string.pushback()
                return PrerequisiteList(token_list)
            elif c in whitespace :
                # eat whitespace until we find something interesting
                state = state_whitespace
            else :
                string.pushback()
                state = state_word

        elif state==state_whitespace :
            # eat whitespaces between symbols (a symbol is a prerequisite or a
            # field in an assignment)
            if not c in whitespace : 
                string.pushback()
                state = state_start

        elif state==state_word:
            if c in whitespace :
                # save token so far 
                token_list.append(Literal(token))
                # restart the current token
                token = ""
                # start eating whitespace
                state = state_whitespace

            elif c=='\\':
                state = state_backslash

            elif c==':':
                state = state_colon
                # assignment? 
                # implicit pattern rule?

            elif c=='|':
                # We have hit token indicating order-only prerequisite.
                # TODO
                assert 0

            elif c in set("?+!"):
                # maybe assignment ?= += !=
                # cheat and peekahead
                if string.lookahead()=='=':
                    # definitely an assign; bail out and we'll retokenize as assign
                    return None
                else:
                    token += c

            elif c=='=':
                # definitely an assign; bail out and we'll retokenize as assign
                return None

            elif c=='#':
                # eat comment 
                string.pushback()
                comment(string)
                # save the token we've captured
                token_list.append(Literal(token))
                # start seeking next boundary
                state = state_start

            elif c=='$':
                state = state_dollar

            elif c==';' :
                # recipe tokenizer expects to start with a ';' or a <tab>
                token.pushback()
                # end of prerequisites; start of recipe
                token_list.append(Literal(token))
                return PrerequisiteList(token_list)
            
            elif c in eol :
                # end of prerequisites; start of recipe
                token_list.append(Literal(token))
                return PrerequisiteList(token_list)

            else:
                token += c
            
        elif state==state_dollar :
            if c=='$':
                # literal $
                token += "$"
            else:
                # save token so far 
                token_list.append(Literal(token))
                # restart token
                token = ""

                # jump to variable_ref tokenizer
                # restore "$" + "(" in the string
                string.pushback()
                string.pushback()

                # jump to var_ref tokenizer
                token_list.append( tokenize_variable_ref(string) )

            state = state_word

        elif state==state_colon : 
            if c==':':
                # maybe ::= 
                state = state_double_colon
            elif c=='=':
                # found := so definitely a rule specific  assignment; bail out
                # and we'll retokenize as assignment
                return None
            else:
                # implicit pattern rule
                # TODO
                assert 0

        elif state==state_double_colon : 
            # at this point, we found ::
            if c=='=':
                # definitely assign
                # bail out and retokenize as assign
                return None
            else:
                # is this an implicit pattern rule?
                # or a parse error?
                # TODO
                assert 0

        elif state==state_backslash : 
            if not c in eol : 
                # literal backslash
                token += '\\'
                state = state_word
            else:
                # The prerequisites (or whatever) are continued on the next
                # line. We treat the EOL as a boundary between symbols
                state = state_start
                
        else : 
            # wtf?
            assert 0, state

    if state==state_word:
        # save the token we've seen so far
        token_list.append(Literal(token.rstrip()))
    elif state in (state_whitespace, state_start) :
        pass
    else:
        # premature end of file?
        raise ParseError()

    return PrerequisiteList(token_list)

@depth_checker
def tokenize_assign_RHS(string):

    state_start = 1
    state_dollar = 2
    state_literal = 3
    state_backslash = 4
    state_whitespace = 5
    state_save_white = 6
    state_ugly_hack = 7

    state = state_start
    token = ""
    white_token = ""
    token_list = []

    for c in string :
        print("a c={0} state={1} idx={2}".format(
                filter_char(c),state,string.idx, string.remain()))
        if state==state_start :
            if c in whitespace :
                state = state_whitespace
            # gnu make treats \ before start a little strangely
            # foo\
            # =\
            # bar  
            # is "foo=bar" not "foo= bar"
            # (according to the rules for backslash that \ should become a space
#            elif c=='\\' : 
#                string.pushback()
#                state = state_ugly_hack
            else :
                string.pushback()
                state = state_literal

#        elif state==state_ugly_hack :
#            if c in eol : 
#                state = state_start
#            else:
##                string.pushback()
#                string.pushback()
#                state= state_literal

        elif state==state_whitespace :
            if not c in whitespace : 
                string.pushback()
                state = state_literal

        elif state==state_literal:
            if c=='$' :
                state = state_dollar
            elif c=='#':
                # save the token we've seen so far
                string.pushback()
                # eat comment 
                comment(string)
                # stay in same state
            elif c in eol :
                # assignment terminates at end of line
                # end of string
                # save what we've seen so far
                token_list.append(Literal(token))
                return Expression(token_list)

            elif c=='\\':
                state = state_backslash
            elif c in whitespace : 
                # backslash rules make whitespace handling tricky
                white_token = c
                state = state_save_white
            else:
                token += c

        elif state==state_save_white : 
            # backslash rules make whitespace handling tricky

            # this could be a literal backslash so peek ahead to find eol
            if c=='\\' and string.lookahead() in eol :
                state = state_backslash
            elif c in whitespace : 
                # save the whitespace in case we need it
                white_token += c
            else:
                # this whitespace chunk is part of the RHS so save
                token += white_token

                # go back to tokenizing a (maybe) literal
                string.pushback()
                state = state_literal

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

        elif state==state_backslash : 
            # eat the EOL  (backslash+eol == line continuation)
            # "Outside of recipe lines, backslash/newlines are converted into a
            # single space character"
            if c in eol : 
                token += " "
                # eat leading white on next line
                state = state_whitespace
            else:
                # literal backslash + char
                token += '\\'
                token += c
                state = state_literal

        else:
            assert 0, state

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

        else:
            assert 0, state

    raise ParseError()

def filter_char(c):
    # make printable char
    if ord(c) < ord(' '):
        return hex(ord(c))
    return c

@depth_checker
def tokenize_recipe_list(string):
    # Collect characters together into a token. 
    # At token boundary, store token as a Literal. Add to token_list. Reset token.
    # A variable ref is a token boundary, and EOL is a token boundary.
    # At recipe boundary, create a Recipe from the token_list. 
    #   Also store Recipe in recipe_list. Reset token_list.
    # At rule boundary, create a RecipeList from the recipe_list.

    state_start = 1
    state_lhs_white = 2
    state_seeking_next_recipe = 3
    state_recipe = 4
    state_space = 5
    state_dollar = 6
    state_backslash = 7
    
    state = state_start
    token = ""
    token_list = []
    recipe_list = []

    sanity_count = 0

    for c in string :
        print("r c={0} state={1} idx={2} ".format(
                filter_char(c),state,string.idx,token))

        sanity_count += 1
#        assert sanity_count < 50

        if state==state_start : 
            # Must arrive here right after the end of the prerequisite list.
            # Should find either a ; or an EOL
            # example:
            #
            # foo : <eol>
            # <tab>@echo bar
            #
            # foo : ; @echo bar
            #
            if c in eol:
                state = state_seeking_next_recipe 
            elif c==';':
                state = state_lhs_white
            else:
                string.pushback()
                state = state_seeking_next_recipe 
#                raise ParseError("c={0}".format(filter_char(c)))
                
        elif state==state_lhs_white :
            # Whitespace after the <tab> (or .RECIPEPREFIX) until the first
            # shell-able command is eaten.
            if not c in whitespace : 
                string.pushback()
                state = state_recipe
            else:
                # eat the whitespace
                pass

        elif state==state_recipe :
            if c in eol : 
                # save what we've seen so far
                token_list.append( Literal(token) )
                recipe_list.append( Recipe( token_list ) )
                # reset our collecting
                token = ""
                token_list = []
                # TODO handle \r \r\n \n\r \n
                state = state_seeking_next_recipe
            elif c=='$':
                state = state_dollar
            elif c=='\\':
                state = state_backslash
            else:
                token += c

        elif state==state_seeking_next_recipe : 
            if c=='#':
                # eat the comment 
                string.pushback()
                comment(string)
                # continue seeking next recipe
            elif c==recipe_prefix :
                # jump back to start to eat any more leading whitespace
                # (leading whitespace is stripped, trailing whitespace is
                # preserved)
                state = state_lhs_white
            elif c in whitespace: 
                state = state_space
            elif c in eol : 
                # ignore EOL, continue seeking
                pass
            else:
                # Found some other character therefore no next recipe
                # therefore end of recipe list. Bye!
                string.pushback()
                return RecipeList(recipe_list)

        elif state==state_space : 
            # eat spaces until EOL or !spaces
            # TODO what happens if .RECIPEPREFIX != <tab>? Is <tab> now
            # whitespace?
            if c in eol : 
                state = state_seeking_next_recipe
            elif c=='#' :
                # eat the comment 
                string.pushback()
                comment(string)
                state = state_seeking_next_recipe
            elif not c in whitespace :
                # buh-bye!
                string.pushback()
                return RecipeList(recipe_list)

        elif state==state_dollar : 
            if c=='$':
                # literal $
                token += "$"
                state = state_recipe
            else:
                # definitely a variable ref of some sort
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

            state=state_recipe

        elif state==state_backslash : 
            if not c in eol :
                # literal \ followed by some char
                token += '\\'
                token += c
            else :
                # save backslash+newline
                token += '\\' 
                token += platform_eol
            state = state_recipe

        else:
            assert 0,state

    print("end of string state={0}".format(state))

    # end of string
    # save what we've seen so far
    if state==state_recipe : 
        token_list.append( Literal(token) )
        recipe_list.append( Recipe(token_list) )
    elif state==state_seeking_next_recipe:
        pass
    else:
        assert 0,state

    return RecipeList( recipe_list )

def tokenize_makefile(string): 

    state_start = 1
    state_statement = 2

    state = state_start
    token_list = []

    for c in string : 
        print("m c={0} state={1} idx={2}".format(filter_char(c),state,string.idx))
        if state==state_start :
            if c in whitespace or c in eol : 
                # ignore whitespace, blank lines
                pass
            elif c=='#':
                string.pushback()
                # eat comment
                comment(string)
            else :
                string.pushback()
                state = state_statement

        elif state==state_statement : 
            # statement := directive
            #           := assignment
            #           := rule
            #
            # TODO directive
            string.pushback()
            token_list.append( tokenize_assignment_or_rule( string ) )
            state = state_start

        else:
            # wtf?
            assert 0,state

    return Makefile( token_list )

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
            return None
#        print("lookahead={0}".format(self.string[self.idx]))
        return self.string[self.idx]

    def pushback(self):
        if self.idx <= 0 :
            raise StopIteration
        self.idx -= 1

    def push_state(self):
        self.state_stack.append(self.idx)
        print( "push stack=", self.state_stack )

    def pop_state(self):
        print( "pop stack=", self.state_stack )
        self.idx = self.state_stack.pop()

    def remain(self):
        # Test/debug method. Return what remains of the string.
        return self.string[self.idx:]

def parse_file(infilename):
    infile = open(infilename)
    all_lines = infile.readlines()
    infile.close()

    s = "".join(all_lines)
    
    my_iter = ScannerIterator(s)
    
    tokens = tokenize_makefile(my_iter)

    print( "tokens={0}".format(str(tokens)) )
    print( tokens.makefile() )
    print("\n")

if __name__=='__main__':
    for infilename in sys.argv[1:]:
        parse_file(infilename)

