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

import hexdump
from scanner import ScannerIterator
import vline

#whitespace = set( ' \t\r\n' )
whitespace = set(' \t')

assignment_operators = {"=", "?=", ":=", "::=", "+=", "!="}
rule_operators = {":", "::"}
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


def filter_char(c):
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

def happy_string(s): 
    # Convert a string with unprintable chars and/or weird printing chars into
    # something that can be printed without side effects.
    # For example, 
    #   <tab> -> "\t"   
    #   <eol> -> "\n"
    #   "     -> \"
    #
    # Want to be able to round trip the output of the Symbol hierarchy back
    # into valid Python code.
    return "".join( [ filter_char(c) for c in s ] )

#
#  Class Hierarchy for Tokens
#
class Symbol(object):
    # base class of everything we find in the makefile
    def __init__(self,string=None):
        # by default, save the token's string 
        # (descendent classes could store something different)
        self.string = string

        # a VirtualLine that holds the code that is compiled to this symbol
        self.code = None

    def __str__(self):
        # create a string such as Literal("all")
        # handle embedded " and ' (with backslashes I guess?)
        return "{0}(\"{1}\")".format(self.__class__.__name__,happy_string(self.string))

    def __eq__(self,rhs):
        # lhs is self
        return self.string==rhs.string

    def makefile(self):
        # create a Makefile from this object
        return self.string

    def set_code(self,vline):
        # the VirtualLine instance holding the block of text for this symbol
        assert hasattr(vline,"phys_lines")
        assert hasattr(vline,"virt_lines")

        print("set_code() start={0} end={1}".format(
                vline.virt_lines[0][0]["pos"],
                vline.virt_lines[-1][-1]["pos"]) )

        self.code = vline

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

        Symbol.__init__(self)

    def __str__(self):
        # return a ()'d list of our tokens
        s = "{0}([".format(self.__class__.__name__)
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
            
    def __len__(self):
        return len(self.token_list)

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
    # Rules are tokenized in multiple steps. First the target + prerequisites
    # are tokenized and put into an instance of this RuleExpression. Then the
    # (optional) recipe list is tokenized, added to an instance of RecipeList,
    # which is passed to the RuleExpression.
    #
    # The two separate steps are necessary because the Makefile's lines  needs
    # to be separated differently for rules vs recipes (backslashes and
    # comments are handled differently).
    # 
    # Rule ::= Target RuleOperator Prerequisites 
    #      ::= Target Assignment 
    #
    # 

    def __init__(self, token_list):
        # add sanity check in constructor

        assert len(token_list)==3 or len(token_list)==4, len(token_list)

        assert isinstance(token_list[0],Expression),(type(token_list[0]),)
        assert isinstance(token_list[1],RuleOp),(type(token_list[1]),)

        if isinstance(token_list[2],PrerequisiteList) : 
            pass
        elif isinstance(token_list[2],AssignmentExpression) :
            pass 
        else:
            assert 0,(type(token_list[2]),)

        # If one not provied, start with a default empty recipe list
        # (so this object will always have a RecipeList instance)
        if len(token_list)==3 : 
            self.recipe_list = RecipeList([]) 
            token_list.append( self.recipe_list )
        elif len(token_list)==4 : 
            assert isinstance(token_list[3],RecipeList),(type(token_list[3]),)

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

    def add_recipe_list( self, recipe_list ) : 
        assert isinstance(recipe_list,RecipeList)

        print("add_recipe_list() rule={0}".format(self.makefile()))
        print("add_recipe_list() recipe_list={0}".format(str(recipe_list)))

        # replace my recipe list with this recipe list
        self.token_list[3] = recipe_list
        self.recipe_list = recipe_list

        print("add_recipe_list()",self.makefile())
        print("add_recipe_list()",self.recipe_list.code)

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
    def __init__(self,recipe_list):
        for r in recipe_list :
            assert isinstance(r,Recipe),(r,)
        
        Expression.__init__(self,recipe_list)

    def makefile(self):
        # newline separated, tab prefixed
        s = ""
        if len(self.token_list):
            s = "\t"+"\n\t".join( [ t.makefile() for t in self.token_list ] )
        return s

#class Makefile(Expression) : 
#    # a collection of statements, directives, rules
#
#    def makefile(self):
#        # newline separated
#        s = "\n".join( [ t.makefile() for t in self.token_list ] )
#        return s

def comment(string):
    state_start = 1
    state_eat_comment = 2

    state = state_start

    # this could definitely be faster (method in ScannerIterator to eat until EOL?)
    for vchar in string : 
        c = vchar["char"]
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
            # otherwise char is eaten

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
def tokenize_statement(string):
    # at start of scanning, we don't know if this is a rule or an assignment
    # this is a test : foo   -> (this,is,a,test,:,)
    # this is a test = foo   -> (this is a test,=,)
    #
    # I first tokenize assuming it's an assignment statement. If the final
    # token is a rule token, then I re-tokenize as a rule.
    #
    # Only difference between a rule LHS and an assignment LHS is the
    # whitespace. In a rule, the whitespace is ignored. In an assignment, the
    # whitespace is preserved.

    # get the starting position of this string (for error reporting)
    starting_pos = string.lookahead()["pos"]

    # save current position in the token stream
    string.push_state()
    lhs = tokenize_statement_LHS(string)
    
    assert type(lhs)==type(()), (type(lhs),)
    for token in lhs : 
        assert isinstance(token,Symbol),(type(token),token)

    # decode what kind of statement do we have based on where
    # tokenize_statement_LHS() stopped.
    last_symbol = lhs[-1]

    print(lhs[-1],len(lhs))

    if isinstance(last_symbol,RuleOp): 
        statement_type = "rule"

        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type))
        print("re-run as rule")

        # jump back to starting position
        string.pop_state()
        # re-tokenize as a rule (backtrack)
        lhs = tokenize_statement_LHS(string,whitespace)
    
        # add rule RHS
        # rule RHS  ::= assignment
        #           ::= prerequisite_list
        #           ::= <empty>
        statement = list(lhs)
        statement.append( tokenize_rule_prereq_or_assign(string) )

        # don't look for recipe(s) yet

        return RuleExpression( statement ) 
    elif isinstance(last_symbol,AssignOp): 
        statement_type = "assignment"

        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type))

        # The statement is an assignment. Tokenize rest of line as an assignment.
        statement = list(lhs)
        statement.append(tokenize_assign_RHS( string ))
        return AssignmentExpression( statement )

    elif isinstance(last_symbol,Expression) :
        statement_type="expression"
        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type))

        assert len(last_symbol),(str(last_symbol),starting_pos)

        # The statement is a directive or function call.
        assert len(string.remain())==0, (len(string.remain(),starting_pos))
        
        return Expression(lhs)

    else:
        statement_type="????"
        print( "last_token={0} ∴ statement is {1}".format(last_symbol,statement_type))

        assert 0,last_symbol

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
    # Statement ::= Assignment | Rule | Directive | Expression
    # Assignment ::= LHS AssignmentOperator RHS
    # Rule       ::= LHS RuleOperator RHS
    # Directive  ::= TODO
    # Expression ::= TODO
    #
    # Directive is stuff like ifdef export vpath define. Directives get
    # slightly complicated because
    #   ifdef :  <--- not legal
    #   ifdef:   <--- legal (verified 3.81, 3.82, 4.0)
    #   ifdef =  <--- legal
    #   ifdef=   <--- legal
    # 
    # Expression is single function like $(info) $(warning). Not all functions
    # are valid in statement context. TODO finish directive.mk to discover
    # which directives are legal in statement context.
    # A lone expression in GNU make usually triggers the "missing separator"
    # error.
    #

    # get the starting position of this string (for error reporting)
    starting_pos = string.lookahead()["pos"]
    print("starting_pos=",starting_pos)

    for vchar in string : 
        c = vchar["char"]
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
                if string.lookahead()["char"]=='=':
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

            elif c in eol : 
                # end of line; bail out
                break
                
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
                # davep 04-Oct-2014 ; XXX   should not see anymore
                print("string={0} data={1}".format(type(string),type(string.data)))
                print(string.data)
                assert 0, (string, vchar)
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
        assert len(token_list),starting_pos
        return Expression(token_list), RuleOp(":") 
    elif state==state_colon_colon:
        # "::"
        assert len(token_list),starting_pos
        return Expression(token_list), RuleOp("::") 
    elif state==state_in_word :
        # likely a lone word (Parse Error) or a $() call
        # TODO handle parse error (How?)
        assert len(token_list),starting_pos
        return Expression(token_list), 

    assert 0, (state,starting_pos)

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

    for vchar in string :
        c = vchar["char"]
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
                if string.lookahead()["char"]=='=':
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
                string.pushback()
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
                assert 0, vchar

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
    state_whitespace = 4

    state = state_start
    token = ""
    token_list = []

    for vchar in string :
        c = vchar["char"]
        print("a c={0} state={1} idx={2}".format(
                filter_char(c),state,string.idx, string.remain()))
        if state==state_start :
            if c in whitespace :
                state = state_whitespace
            else :
                string.pushback()
                state = state_literal

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
            else:
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

    for vchar in string : 
        c = vchar["char"]
        print("v c={0} state={1} idx={2}".format(filter_char(c),state,string.idx))
        if state==state_start:
            if c=='$':
                state=state_dollar
            else :
                raise ParseError(vchar["pos"])
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
                if string.lookahead()["char"]=='$':
                    token += "$"
                    # skip the extra $
                    c = next(string)
                    state = state_in_var_ref
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

    raise ParseError(vchar["pos"])

@depth_checker
def tokenize_recipe(string):
    # Collect characters together into a token. 
    # At token boundary, store token as a Literal. Add to token_list. Reset token.
    # A variable ref is a token boundary, and EOL is a token boundary.
    # At recipe boundary, create a Recipe from the token_list. 

    print("tokenize_recipe()")

    state_start = 1
    state_lhs_white = 2
    state_recipe = 3
    state_space = 4
    state_dollar = 5
    state_backslash = 6
    
    state = state_start
    token = ""
    token_list = []

    sanity_count = 0

    for vchar in string :
        c = vchar["char"]
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
            if c==';' or c==recipe_prefix :
                state = state_lhs_white
                
        elif state==state_lhs_white :
            # Whitespace after the <tab> (or .RECIPEPREFIX) until the first
            # shell-able command is eaten.
            if not c in whitespace : 
                string.pushback()
                state = state_recipe
            # otherwise eat the whitespace

        elif state==state_recipe :
            if c in eol : 
                # save what we've seen so far
                token_list.append( Literal(token) )
                # bye!
                return Recipe( token_list ) 
            elif c=='$':
                state = state_dollar
            elif c=='\\':
                state = state_backslash
            else:
                token += c

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
            # literal \ followed by some char
            token += '\\'
            token += c
            state = state_recipe

        else:
            assert 0,state

    print("end of string state={0}".format(state))

    # end of string
    # save what we've seen so far
    if state==state_recipe : 
        token_list.append( Literal(token) )
    else:
        assert 0,(state,string.starting_file_line)

    return Recipe( token_list )

def parse_recipes( file_lines, semicolon_vline=None ) : 

    print("parse_recipes()")
    print( file_lines.remain() )

    state_start = 1
    state_comment_backslash = 2
    state_recipe_backslash = 3

    state = state_start

    # array of Recipe
    recipe_list = []

    # array of text lines (recipes with \)
    lines_list = []

    if semicolon_vline : 
        # we have something that trails a ; on the rule
        recipe = tokenize_recipe(iter(semicolon_vline))
        print("recipe={0}".format(recipe.makefile()))
        recipe.set_code( semicolon_vline )
        recipe_list.append(recipe)

    for line in file_lines : 
#        print("")
        print( "l state={0}".format(state))
        print( hexdump.dump(line,16), end="" )

        if state==state_start : 
            if line.startswith(recipe_prefix):
                # TODO handle DOS line ending
                if line.endswith('\\\n'):
                    lines_list = [ line ] 
                    state = state_recipe_backslash
                else :
                    # single line
                    recipe_vline = vline.RecipeVirtualLine([line],file_lines.idx)
                    recipe = tokenize_recipe(iter(recipe_vline))
#                    recipe = tokenize_recipe(ScannerIterator(line))
                    print("recipe={0}".format(recipe.makefile()))
                    recipe.set_code(recipe_vline)
                    recipe_list.append(recipe)
            else : 
                line_stripped = line.strip()
                if len(line_stripped)==0:
                    # ignore blank lines
                    pass
                elif line_stripped.startswith("#"):
                    # ignore makefile comments
                    # TODO handle DOS line ending
                    print("recipe comment",line_stripped)
                    if line.endswith('\\\n'):
                        lines_list = [ line ] 
                        state = state_comment_backslash
                else:
                    # found a line that doesn't belong to the recipe;
                    # done with recipe list
                    file_lines.pushback()
                    break

        elif state==state_comment_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # end of the makefile comment (is ignored)
                state = state_start

        elif state==state_recipe_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # now have an array of lines that need to be one line for the
                # recipes tokenizer
                recipe_vline = vline.RecipeVirtualLine(lines_list,file_lines.idx)
                recipe = tokenize_recipe(iter(recipe_vline))
                recipe.set_code(recipe_vline)
                recipe_list.append(recipe)

                # go back and look for more
                state = state_start

        else : 
            # wtf?
            assert 0,state

    print("bottom of parse_recipes()")

    return RecipeList(recipe_list)

def parse_a_line(line_iter,virt_line): 
    # pull apart a single line into token/symbol(s)
    #
    # line_iter - the iterator across the entire file 
    #             (a Rule includes the RecipeList so need to get the entire file)
    # virt_line - the current line we need to tokenize (a VirtualLine)

    assert isinstance(line_iter,ScannerIterator),(type(line_iter),)
    assert isinstance(virt_line,vline.VirtualLine),(type(virt_line),)

    statement_iter = iter(virt_line)
    token = tokenize_statement(statement_iter)

    # If we found a rule, we need to change how we're handling the
    # lines. (Recipes have different whitespace and backslash rules.)
    if isinstance(token,RuleExpression) : 
        # rule line can contain a recipe following a ; 
        # for example:
        # foo : bar ; @echo baz
        #
        # The rule parser should stop at the semicolon. Will leave the
        # semicolon as the first char of iterator
        # 
        print("rule={0}".format(str(token)))

        # truncate the virtual line that precedes the recipe (cut off
        # at a ";" that might be lurking)
        #
        # foo : bar ; @echo baz
        #          ^--- truncate here
        #
        # I have to parse the full like as a rule to know where the
        # rule ends and the recipe(s) begin. The backslash makes me
        # crazy.
        #
        # foo : bar ; @echo baz\
        # I am more recipe hur hur hur
        #
        # The recipe is "@echo baz\\\nI am more recipe hur hur hur\n"
        # and that's what needs to exec'd.
        remaining_vchars = statement_iter.remain()
        if len(remaining_vchars)>0:
            # truncate at position of first char of whatever is
            # leftover from the rule
            truncate_pos = remaining_vchars[0]["pos"]

            recipe_str_list = virt_line.truncate(truncate_pos)

            # make a new virtual line from the semicolon trailing
            # recipe (using a virtual line because backslashes)
            dangling_recipe = vline.RecipeVirtualLine(recipe_str_list,truncate_pos[vline.VCHAR_ROW])
            print("dangling={0}".format(dangling_recipe))
            print("dangling={0}".format(dangling_recipe.virt_lines))
            print("dangling={0}".format(dangling_recipe.phys_lines))

            recipe_list = parse_recipes( line_iter, dangling_recipe )
        else :
            recipe_list = parse_recipes( line_iter )

        assert isinstance(recipe_list,RecipeList)

        print("recipe_list={0}".format(str(recipe_list)))

        # attach the recipe(s) to the rule
        token.add_recipe_list(recipe_list)

    token.set_code(virt_line)

    return token

def parse_lines(file_lines): 
    # File_lines is an array of strings.
    # Each string should be terminated by an EOL.
    # Handle cases where line is continued after the EOL by a \+EOL
    # (backslash).

    # I put stuff like this in here because I lose track of what I'm doing
    assert type(file_lines)==type([])
    assert type(file_lines[0])==type("")

    state_start = 1
    state_backslash = 2
    state_tokenize = 3
    
    state = state_start 

    # array of Symbols we have parsed in the file
    code_block_list = []

    # we need an iterator across our lines that supports pushback
    line_iter = ScannerIterator(file_lines)

    # can't use enumerate() because the line_iter will also be used inside
    # parse_recipes(). 
    for line in line_iter :
        # line_iter.idx is the *next* line number counting from zero 
        line_number = line_iter.idx-1
        print("line_num={0} state={1}".format(line_number,state))
        print("{0}".format(hexdump.dump(line),end=""))

        if state==state_start : 
            start_line_stripped = line.strip()

            # ignore blank lines
            if len(start_line_stripped)==0:
                continue

            line_list = [ line ] 

            starting_line_number = line_number
            if vline.is_line_continuation(line):
                # We found a line with trailing \+eol
                # We will start collecting the next lines until we see a line
                # that doesn't end with \+eol
                state = state_backslash
            else :
                # We found a single line of makefile. Tokenize!
                state = state_tokenize

        elif state==state_backslash : 
            line_list.append( line )
            if not vline.is_line_continuation(line):
                # This is the last line of our continuation block. Create a
                # virtual block for this array of lines.
                state = state_tokenize

        else:
            # wtf?
            assert 0, state

        if state==state_tokenize: 
            # is this a line comment?
            if start_line_stripped.startswith("#") :
                # ignore
                state = state_start
                continue

            # make a virtual line (joins together backslashed lines into one
            # line visible through an iterator)
            virt_line = vline.VirtualLine(line_list,starting_line_number)
            del line_list # detach the ref (VirtualLine keeps the array)

            # now take apart the line into symbol/tokens
            token = parse_a_line(line_iter,virt_line)

            # save the parsed symbol with its code 
            code_block_list.append( token ) 

            # back around the horn
            state = state_start

    return code_block_list 

def parse_makefile_strlist(file_lines):
    # file_lines should be an array of strings

    block_list = parse_lines(file_lines)

    # the following is just test code to printf the results. 
    #
    # TODO need to carefully syntax verify the block list.
    # As of this writing I'm succesfully (mostly) tokenizing makefiles but not
    # syntax verifying.

    for block in block_list : 
        assert isinstance(block,Symbol),(type(block),)
        assert hasattr(block,"code")
        print("block={0}".format(block.code),end="")
        if isinstance(block,RuleExpression):
            for recipe in block.recipe_list : 
                print("recipe={0}".format(recipe.code))
    print("makefile=",",\\\n".join( [ "{0}".format(block) for block in block_list ] ) )
    print("# start makefile")
    print("\n".join( [ "{0}".format(block.makefile()) for block in block_list ] ) )
    print("# end makefile")

def parse_makefile(infilename) : 
    with open(infilename,'r') as infile :
        file_lines = infile.readlines()

    parse_makefile_strlist(file_lines)

def usage():
    # TODO
    print("usage: TODO")

if __name__=='__main__':
    if len(sys.argv) < 2 : 
        usage()
        sys.exit(1)

    infilename = sys.argv[1]
    parse_makefile(infilename)

