#!/usr/bin/env python3

import sys
import logging
import itertools

_debug = True

logger = logging.getLogger("pymake.symbol")

from printable import printable_char, printable_string
from vline import VirtualLine, VChar, VCharString
from version import Version
from error import *
import shell
from flatten import flatten
from todo import TODOMixIn

_debug = True

__all__ = [ "Symbol",
            "Literal",
            "Operator",
            "AssignOp",
            "RuleOp",
            "Expression",
            "VarRef",
            "AssignmentExpression",
            "RuleExpression",
            "PrerequisiteList",
            "Recipe",
            "RecipeList",
            "Directive",
            "ExportDirective",
            "UnExportDirective",
            "IncludeDirective",
            "MinusIncludeDirective",
            "SIncludeDirective",
            "VpathDirective",
            "OverrideDirective",
            "LineBlock",
            "ConditionalBlock",
            "ConditionalDirective",
            "IfdefDirective",
            "IfndefDirective",
            "IfeqDirective",
            "IfneqDirective",
            "DefineDirective",
            "UnDefineDirective",
            "Makefile",
]

#
#  Class Hierarchy for Tokens
#
class Symbol(object):
    # base class of everything we find in the makefile
    def __init__(self, vstring=None):
        # using array of vchar for the symbol now 
        if vstring:
            # do you quack like a VCharString? everything must be VChar so know filename/pos
            try:
                vstring.chars, vstring[0].pos, vstring[0].filename
            except AttributeError:
                if _debug:
                    vstring = VCharString([VChar(c,(0,0),"/dev/null") for c in vstring])
                else:
                    logger.error(type(vstring))
                    raise
            logger.debug("new Symbol vstring=\"%s\"", printable_string(str(vstring)))
            vstring.validate()

        # by default, save the token's VChars
        # (descendent classes could store something different)
        self.string = vstring

    def __str__(self):
        # create a string such as Literal("all")
        # handle embedded " and ' (with backslashes I guess?)
        return "{0}(\"{1}\")".format(self.__class__.__name__, printable_string(str(self.string)))

    def __eq__(self, rhs):
        # lhs is self
        # compare to rhs
        try:
            return self.string == rhs.string
        except AttributeError:
            # rhs can also be python string instead of VCharString
            # e.g., ":=" "::=" 
            return str(self.string) == rhs

    def makefile(self):
        # create a Makefile from this object
        return str(self.string)

    @staticmethod
    def validate(token_list):
        if not _debug:
            return

        for t in token_list : 
            assert isinstance(t, Symbol), (type(t), t)
            if not t.string:
                return
            t.string.validate()

    def eval(self, symbol_table):
        # children should override
        raise NotImplementedError(self.name)

    def get_pos(self):
        return self.string[0].filename, self.string[0].pos

class Literal(Symbol):
    # A literal found in the token stream. Store as a string.

    def __init__(self, vstring):
        # catch bugs where I create empty Literals
        if not len(vstring):
            breakpoint()
        assert len(vstring)

        super().__init__(vstring)
    
    def eval(self, symbol_table):
        # everything returns a single string
        return str(self.string)

class Operator(Symbol):
    pass

class AssignOp(Operator):
    # An assignment symbol, one of { "=" | ":=" | "?=" | "+=" | "!=" | "::=" }
    pass
    
class RuleOp(Operator):
    # A rule symbol, one of { ":" | "::" }
    pass

class Expression(Symbol):
    # An Expression is a list of Symbols. An Expression self.string is None
    # A Symbol will not have a token_list.
    # A Symbol's self.string is the VCharString containing VChar knowing the
    #    filename/pos of everything in the Makefile
    def __init__(self, token_list ):
        # expect a list/array/tuple (test by calling len())
        assert len(token_list)>=0, (type(token_list), token_list)
        self.token_list = token_list
        Symbol.validate(token_list)
        super().__init__()

    def __str__(self):
        # return a ()'d list of our tokens
        s = "{0}([".format(self.__class__.__name__)
        s += ", ".join([str(t) for t in self.token_list])
        s += "])"
        return s

    def __getitem__(self, idx):
        return self.token_list[idx]

    def __eq__(self, rhs):
        # Used in test code.
        #
        # lhs is self
        # rhs better be another expression
        assert isinstance(rhs, Expression), (type(rhs), rhs)

        if len(self.token_list) != len(rhs.token_list):
            logger.error("length mismatch %d != %d", len(self.token_list), len(rhs.token_list))
            return False

        for tokens in zip(self.token_list, rhs.token_list) :
            if tokens[0].__class__ != tokens[1].__class__ : 
                logger.error("class mismatch %s != %s", tokens[0].__class__, tokens[1].__class__)
                return False

            # Recurse into sub-expressions. It's tokens all the way down!
            if not str(tokens[0]) == str(tokens[1]) :
                logger.error("token mismatch %s != %s", tokens[0], tokens[1])
                return False

        return True

    def makefile(self):
        # Build a Makefile string from this rule expression.
        return "".join([t.makefile() for t in self.token_list])
            
    def __len__(self):
        return len(self.token_list)

    def eval(self, symbol_table):
        for e in self.token_list:
            logger.debug("expression e=%s", e)

        step1 = [e.eval(symbol_table) for e in self.token_list]
        return "".join(step1)

    def get_pos(self):
        # Find the position (filename,(row,col)) of this Expression.
        # An Expression contains a token_list.  That token_list also contains
        # tokens.  Find the first symbol that contains the string (vs simply
        # containing another symbol)
        tok = self.token_list[0]
        while tok.string is None:
            tok = tok.token_list[0]

        vchar = tok.string[0]
        return vchar.filename, vchar.pos

class VarRef(Expression):
    # A variable reference found in the token stream. Save as a nested set of
    # tuples representing a tree. 
    # $a            ->  VarRef(a)
    # $(abc)        ->  VarRef(abc,)
    # $(abc$(def))  ->  VarRef(abc,VarRef(def),)
    # $(abc$(def)$(ghi))  ->  VarRef(abc,VarRef(def),VarRef(ghi),)
    # $(abc$(def)$(ghi$(jkl)))  ->  VarRef(abc,VarRef(def),VarRef(ghi,VarRef(jkl)),)
    # $(abc$(def)xyz)           ->  VarRef(abc,VarRef(def),Literal(xyz),)
    # $(info this is a varref)  ->  VarRef(info this is a varref)

    def makefile(self):
        return "$(" + "".join([t.makefile() for t in self.token_list]) + ")"

    def eval(self, symbol_table):
        logger.debug("varref=%r eval start", self)
        key = [t.eval(symbol_table) for t in self.token_list]
        logger.debug("varref=%r key=%r", self, key)
#        key = "".join([t.eval(symbol_table) for t in self.token_list])
        return symbol_table.fetch("".join(key))

class AssignmentExpression(Expression):
    def __init__(self, token_list):
        super().__init__(token_list)
        self.sanity()

    def eval(self, symbol_table):
        self.sanity()
        lhs = self.token_list[0].eval(symbol_table)
        op = self.token_list[1]
        logger.debug("assignment lhs=%s op=%s", lhs, op)

        # FIXME I have a sneaking suspicion the rhs can be token_list[3:]
        # pyfiles := $(wildcard foo*.py) $(wildcard bar*.py) $(wildcard baz*.py)
        assert len(self.token_list) == 3

        # from the gnu make pdf:
        # immediate = deferred
        # immediate ?= deferred
        # immediate := immediate
        # immediate ::= immediate
        # immediate += deferred or immediate
        # immediate != immediate

        # handle different styles of assignment
        if op == ":=" or op == "::=":
            # simply expanded
            rhs = self.token_list[2].eval(symbol_table)
        elif op == "=":
            # recursively expanded
            # store the expression in the symbol table without evaluating
            rhs = self.token_list[2]
        elif op == "!=":
            # != seems to be a > 3.81 feature so add a version check here
            if Version.major < 4:
                raise VersionError("!= not in this version of make")

            # execute RHS as shell
#            s = self.token_list[2].eval(symbol_table)
            rhs = shell.execute_tokens(list(self.token_list[2]), symbol_table )
        else:
            # TODO
            raise Unimplemented("op=%s"%op)

        logger.debug("assignment rhs=%s", rhs)

        # lhs should be an iterable of strings
#        assert isinstance(lhs,list), type(lhs)
#        assert isinstance(lhs[0],str), type(lhs[0])

        key = "".join(lhs)
        symbol_table.add(key, rhs, self.token_list[0].get_pos())
        return ""

    def sanity(self):
        # AssignmentExpression :=  Expression AssignOp Expression
        assert len(self.token_list)==3, len(self.token_list)
        assert isinstance(self.token_list[0], Expression)
        assert isinstance(self.token_list[1], AssignOp)
        assert isinstance(self.token_list[2], Expression), (type(self.token_list[2]),)

class RuleExpression(Expression):
    # Rules are tokenized in multiple steps. First the target + prerequisites
    # are tokenized and put into an instance of this RuleExpression. Then the
    # (optional) recipe list is tokenized, added to an instance of RecipeList,
    # which is passed to the RuleExpression.
    #
    # The two separate steps are necessary because the Makefile's lines need
    # to be separated differently for rules vs recipes (backslashes and
    # comments are handled differently).
    # 
    # Rule ::= Target RuleOperator Prerequisites 
    #      ::= Target Assignment 
    #
    # 

    def __init__(self, token_list):
        # add sanity check in constructor
        Symbol.validate(token_list)

        assert len(token_list)==3 or len(token_list)==4, len(token_list)

        assert isinstance(token_list[0], Expression), (type(token_list[0]),)
        assert isinstance(token_list[1], RuleOp), (type(token_list[1]),)

        if isinstance(token_list[2], PrerequisiteList) : 
            pass
        elif isinstance(token_list[2], AssignmentExpression) :
            pass 
        else:
            assert 0, (type(token_list[2]),)

        # If one not provied, start with a default empty recipe list
        # (so this object will always have a RecipeList instance)
        if len(token_list)==3 : 
            self.recipe_list = RecipeList([]) 
            token_list.append( self.recipe_list )
        elif len(token_list)==4 : 
            assert isinstance(token_list[3], RecipeList), (type(token_list[3]),)

        super().__init__(token_list)

    def makefile(self):
        # rule-targets rule-op prereq-list <CR>
        #     recipes
        assert len(self.token_list)==4, len(self.token_list)

        s = ""

        # Embed the filename+pos of the rule in the output makefile.
        if _debug:
            filename, pos = self.get_pos()
            s += "# %s %s\n" % (filename, pos)

        # davep 03-Dec-2014 ; need spaces between targets, no spaces between
        # prerequisites
        # 
        # first the targets
        s += " ".join( [ t.makefile() for t in self.token_list[0].token_list ] )

        # operator
        s += self.token_list[1].makefile()

        # prerequisite(s)
        s += self.token_list[2].makefile()

        # recipe(s)
        recipe_list = self.token_list[3].makefile()
        if recipe_list : 
            s += "\n"
            s += recipe_list
            assert s[-1]=='\n'
        return s

    def add_recipe_list( self, recipe_list ) : 
        assert isinstance(recipe_list, RecipeList)

        logger.debug("add_recipe_list() rule=%s", str(self))
        logger.debug("add_recipe_list() recipe_list=%s", str(recipe_list))

        # replace my recipe list with this recipe list
        self.token_list[3] = recipe_list
        self.recipe_list = recipe_list

#        logger.debug("add_recipe_list() %s", self.makefile())

    def eval(self, symbol_table):
        # TODO
        logger.error("%s eval not implemented yet", type(self))
#        breakpoint()
        return ""

class PrerequisiteList(Expression):
     # davep 03-Dec-2014 ; FIXME prereq list must be an array of expressions,
     # not an expression itself or wind up with problems with spaces
     #  $()a vs $() a
     # (note the space before 'a')

    def __init__(self, token_list):
        for t in token_list :
            assert isinstance(t, Expression), (type(t,))
        super().__init__(token_list)

    def makefile(self):
        # space separated
        return " ".join( [ t.makefile() for t in self.token_list ] )

class Recipe(Expression):
    # A single line of a recipe

    def __init__(self, token_list):
        super().__init__(token_list)
        self.recipe = None

    def save(self, recipe):
        self.recipe = recipe

class RecipeList( Expression ) : 
    # A collection of Recipe objects
    def __init__(self, recipe_list):
        for r in recipe_list :
            assert isinstance(r, Recipe), (r,)
        
        super().__init__(recipe_list)

    def makefile(self):
        # newline separated, tab prefixed
        s = ""
        if len(self.token_list):
            s = "\t" + "\n\t".join([t.makefile() for t in self.token_list])
            s += "\n"
        return s

class Directive(Symbol):
    name = "should not see this"

    # A Directive instance contains an Expression instance ("has a").
    # A Directive instance is _not_ an Expression instance ("not is-a").

    def __init__(self, expression=None):
        if expression : 
            assert isinstance(expression, Expression) 

        super().__init__()
        self.expression = expression

    def __str__(self):
        if self.expression : 
            return "{0}({1})".format(self.__class__.__name__, str(self.expression))
        else:
            return "{0}()".format(self.__class__.__name__)

    def makefile(self):
        if self.expression : 
            return "{0} {1}".format(self.name, self.expression.makefile() )
        else : 
            return "{0}".format(self.name)

    def save(self, code):
        self.code = code

class ExportDirective(Directive):
    name = "export"

    def __init__(self, expression=None):
        # TODO 
        # make 3.81 "export define" not allowed ("missing separator")
        # make 3.82 works
        # make 4.0  works
        if not(Version.major==3 and Version.minor==81) : 
            raise TODO()

        super().__init__(expression)

class UnExportDirective(ExportDirective):
    name = "unexport"

class IncludeDirective(Directive):
    name = "include"

class MinusIncludeDirective(IncludeDirective):
    # handles -include directives
    name = "-include"

class SIncludeDirective(MinusIncludeDirective):
    # handles sinclude directives (another name for -include)
    name = "sinclude"

class VpathDirective(Directive):
    name = "vpath"

class OverrideDirective(TODOMixIn,Directive):
    name = "override"

    def __init__(self, expression=None ):
        description="Override requires an assignment expression."
        if expression is None :
            # must have an expression (bare override not allowed)
            raise ParseError(description=description)
        if not isinstance(expression, AssignmentExpression):
            # must have an assignment expression            
            raise ParseError(description=description)

        super().__init__(expression)

    def eval(self, symbol_table):
        o = self.expression.eval(symbol_table)
#        breakpoint()
        # TODO I'm unsure how to get this integrated with the symbol table yet


class LineBlock(Symbol):
    # Pile of unparsed code inside a conditional directive or a define
    # multi-line macro. The text is unexamined until the condition is evaluated
    # true (for conditional) or until the macro is $(call)ed (for multi-line
    # macro).
    #
    # ifdef FOO
    #    LineBlock
    # else
    #    LineBlock
    # endif  
    #
    # or
    #
    # define foo
    #   LineBlock
    # endef

    def __init__(self, vline_list):
        if _debug:
            [vline.validate() for vline in vline_list]

        # ha-ha typechecking
        if len(vline_list):
            vline_list[0].filename

        self.vline_list = vline_list
        super().__init__()

    def makefile(self):
        if _debug:
            [vline.validate() for vline in self.vline_list]
        
        s = "".join( [ str(v) for v in self.vline_list ] )
        return s

    def __str__(self):
        # This class contains an array of VirtualLine instances. Need to
        # recreate the appropriate Python code.
        s = ", ".join( [v.python() for v in self.vline_list] )
        return "LineBlock([{0}])".format(s)

    def eval(self, symbol_table, tokenize_fn):
        # FIXME passing tokenize down here is ugly and I hate it and it's ugly.
        # Fix it somehow.
        vline_iter = iter(self.vline_list)

        for vline in vline_iter:
            # XXX temp hack ; pass None for raw line_scanner
            statement = tokenize_fn(vline, vline_iter, None)

            # TODO handle weird stuff like stray function call in expression
            # context (Same as what execute() in pymake.py needs to handle)
            result = statement.eval(symbol_table)
            logger.debug("execute result=\"%s\"", result)

        # XXX what do I do about rules?
        return ''


class ConditionalBlock(Directive):
    name = "<ConditionalBlock>"

    # A ConditionalBlock represents a conditional and all its contents
    # (if/elseif/else/endif). 
    #
    # A ConditionalDirective instance is the conditional expression (ifdef
    # Expression, ifndef Expression, etc).
    #
    # A LineBlock instance represents a blob of unparsed text (will be parsed
    # if the condition evaluates True).
    #
    # if expression
    # elif expression
    # else 
    # endif
    #
    # if abc      <--- cond_expr[0]
    #   foo         <--- cond_blocks[0][0]
    #   bar         <--- cond_blocks[0][1]
    #   baz         <--- cond_blocks[0][2]
    # else if xyz <--- cond_expr[1]
    #   abc         <--- cond_blocks[1][0]
    #   def         <--- cond_blocks[1][1]
    #   ghi         <--- cond_blocks[1][2]
    # else        <--- NOT a member of cond_expr
    #   xyzzy       <--- cond_blocks[2][0]
    # endif
    #
    # len(self_expr) == len(cond_blocks) or\
    # len(self_expr) == len(cond_blocks)-1
    #
    # The stuff inside the cond_blocks[] is {LineBlock|ConditionalBlock}
    # Is an array of unparsed text (LineBlock) intermixed with more nested
    # conditionals (ConditionalBlock).

    def __init__(self, tokenize_fn) :
        super().__init__()
        
        # https://en.wikipedia.org/wiki/Dependency_injection
        self.tokenize_fn = tokenize_fn

        # cond_expr is an array of ConditionalDirective
        #
        # cond_blocks is an array of arrays. Each cond_block[n] array is an
        # array of either LineBlock or ConditionalBlock
        self.cond_exprs = []
        self.cond_blocks = []

        # now process args
        # Args will be an array of tuples.
        # Each tuple will be:
        #   (ConditionalExpression, [LineBlock|ConditionalBlock]*)
        # tuple[0] is the ConditionalExpression
        # tuple[1] is an array of zero or more LineBlock/ConditionalBlocks that
        #          represent the contents of the conditional case.
        # The final else (for which there is no ConditionalExpression) is just
        # a ConditionalExpression following the array.
        
#        if conditional_blocks : 
#            for block_tuple in conditional_blocks : 
#                cond_expr, cond_block_list = block_tuple
#                self.add_conditional( cond_expr )
#                for b in cond_block_list : 
#                    self.add_block( b )

        # were we given an else_block?
        # (an empty [] else block is treated like an empty else condition)
        # ifdef FOO
        #   blah blah blah
        # else <--- still want the else to print
        # endif
#        if not else_blocks is None : 
#            self.start_else()
#            for b in else_blocks: 
#                self.add_block( b )
        
    def add_conditional( self, cond_expr ) :
        assert len(self.cond_exprs) == len(self.cond_blocks)
        assert isinstance(cond_expr, ConditionalDirective), (type(cond_expr), )
        self.cond_exprs.append(cond_expr)
        self.cond_blocks.append( [] )

    def add_block( self, block ):
        assert isinstance(block, (ConditionalBlock, LineBlock)), (type(block), )
        self.cond_blocks[-1].append(block)

    def start_else( self ) : 
        assert len(self.cond_exprs) == len(self.cond_blocks)
        self.cond_blocks.append( [] )
        assert len(self.cond_exprs)+1 == len(self.cond_blocks)

    def makefile(self):
        # sanity check; need at least one conditional
        assert self.cond_exprs

        s = ""
        e = ""
        
        # jump through weird hoop to add tailing \n on ConditionalBlock sub-blocks
        # (my rule is the final \n is caller's responsibility)
        def prn(b):
            if isinstance(b, ConditionalBlock) :
                return b.makefile()+"\n"
            else:
                return b.makefile()

        # if/elseif blocks
        for expr, block in zip(self.cond_exprs, self.cond_blocks):
            s += e + expr.makefile()+"\n"
            s += "".join([prn(b) for b in block])
            e = "else "
        # else block
        if len(self.cond_exprs) != len(self.cond_blocks) :
            assert len(self.cond_exprs)+1 == len(self.cond_blocks)
            s += "else\n"
            s += "".join([prn(b) for b in self.cond_blocks[-1]])
            
        s += "endif"
        return s

    def __str__(self):
        s = "{0}(".format(self.__class__.__name__)
        
        def blocklist_str( blocklist ):
            # connect the (ConditionalBlock|LineBlock) together into an array
            return "[" + \
                       ", ".join([str(b) for b in blocklist]) +\
                   "]"

        # array of tuples
        #   tuple[0] is ConditionalExpression
        #   tuple[1] is array of (LineBlock|ConditionalBlock)
        s += "["
        s += ", ".join( [ "("+str(expr)+", "+blocklist_str(blocklist)+")" for expr, blocklist in zip(self.cond_exprs, self.cond_blocks) ] )
        s += "]"

        # TODO add else case
        if len(self.cond_blocks) > len(self.cond_exprs):
            # have an else
            s += ", " + blocklist_str(self.cond_blocks[-1])

        s += ")"
        return s

    def eval(self, symbol_table):

        # XXX eventually we'll return a Rule if the block contains a rule?
    
        for idx,expr in enumerate(self.cond_exprs):
            breakpoint()
            flag = expr.eval(symbol_table)
            if not flag:
                # try next conditional
                continue

            line_block = self.cond_blocks[idx][0]
            # we found a truthy so we're done
            return line_block.eval(symbol_table, self.tokenize_fn)

        # At this point we have run out of expressions to evaluate.
        # Is there one more cond_block which indicates an unconditional else?
        if len(self.cond_blocks) > len(self.cond_exprs):
            assert len(self.cond_blocks) == len(self.cond_exprs)+1
            line_block = self.cond_blocks[-1][0]
            return line_block.eval(symbol_table, self.tokenize_fn)


class ConditionalDirective(Directive):
    name = "(should not see this)"

class IfdefDirective(ConditionalDirective):
    name = "ifdef"

    def eval(self, symbol_table):
        name = self.expression.eval(symbol_table)

        # don't use .fetch() because we don't want to eval the expression in
        # the symbol table. We just want proof of exist.
        return symbol_table.is_defined(name)


class IfndefDirective(ConditionalDirective):
    name = "ifndef"

    def eval(self, symbol_table):
        name = self.expression.eval(symbol_table)

        # don't use .fetch() because we don't want to eval the expression in
        # the symbol table. We just want proof of exist.
        return not symbol_table.is_defined(name)

class IfeqDirective(ConditionalDirective):
    name = "ifeq"

    # "The ifeq directive begins the conditional, and specifies the condition. It contains two
    # arguments, separated by a comma and surrounded by parentheses. Variable substitution
    # is performed on both arguments and then they are compared. The lines of the makefile
    # following the ifeq are obeyed if the two arguments match; otherwise they are ignored."
    #  GNU Make Manual 7.1 pg 81

    def eval(self, symbol_table):
        breakpoint()

class IfneqDirective(ConditionalDirective):
    name = "ifneq"

class DefineDirective(Directive):
    name = "define"

    def __init__(self, macro_name, line_block=None):
        super().__init__()
        self.string = macro_name
#        assert isinstance(macro_name, str), type(macro_name)

        self.line_block = line_block if line_block else LineBlock([])

    def __str__(self):
        return "{0}(\"{1}\", {2})".format(self.__class__.__name__,
                        str(self.string),
                        str(self.line_block))

    def set_block(self, line_block):
        self.line_block = line_block

    def makefile(self):
        s = str(self.line_block)
        return "define {0}=\n{1}endef".format(
                        str(self.string),
                        self.line_block.makefile() )
        

class UnDefineDirective(Directive):
    name = "undefine"

class Makefile(object) : 
    # A collection of statements, directives, rules.
    # Note this class is separate from the Symbol hierarchy.

    def __init__(self, token_list):
        Symbol.validate(token_list)
        self.token_list = token_list

    def __str__(self):
        return "Makefile([{0}])".format(", \n".join( [ str(block) for block in self.token_list ] ) )
#        return "Makefile([{0}])".format(", \n".join( [ "{0}".format(block) for block in self.token_list ] ) )

    def makefile(self):
        s = "\n".join( [ "{0}".format(token.makefile()) for token in self.token_list ] )
        return s

    def __iter__(self):
        return iter(self.token_list)


