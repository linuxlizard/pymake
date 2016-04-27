#!/usr/bin/env python3

import sys
import logging

logger = logging.getLogger("pymake.symbol")

from printable import printable_char, printable_string
from vline import VirtualLine
from version import Version
from error import *
from evaluate import evaluate

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
            "Makefile",
]
#
#  Class Hierarchy for Tokens
#
class Symbol(object):
    # base class of everything we find in the makefile
    def __init__(self, string=None):
        # davep 24-Apr-2016 ; using array of vchar for the symbol now 
        if string:
            # do you quack like a VCharString?
            assert string[0].filename, type(string)
            assert string[0].pos, type(string)
            assert string[0].char, type(string)

        # by default, save the token's VChars
        # (descendent classes could store something different)
        self.string = string

    def __str__(self):
        # create a string such as Literal("all")
        # handle embedded " and ' (with backslashes I guess?)
        return "{0}(\"{1}\")".format(self.__class__.__name__, printable_string(self.string))

    def __eq__(self, rhs):
        # lhs is self
        return self.string==rhs.string

    def makefile(self):
        # create a Makefile from this object
        return self.string

    @staticmethod
    def validate(token_list):
        for t in token_list : 
            assert isinstance(t, Symbol), (type(t), t)

    def eval(self, symbol_table):
        # children should override
        assert 0
        return None

class Literal(Symbol):
    # A literal found in the token stream. Store as a string.
    
    def eval(self, symbol_table):
        return printable_string(self.string)

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
        # expect a list/array/tuple (test by calling len())
        assert len(token_list)>=0, (type(token_list), token_list)

        self.token_list = token_list

        Symbol.validate(token_list)

        Symbol.__init__(self)

    def __str__(self):
        # return a ()'d list of our tokens
        s = "{0}([".format(self.__class__.__name__)
        s += ", ".join([str(t) for t in self.token_list])
        s += "])"
        return s

    def __getitem__(self, idx):
        return self.token_list[idx]

    def __eq__(self, rhs):
        # lhs is self
        # rhs better be another expression
        assert isinstance(rhs, Expression), (type(rhs), rhs)

        if len(self.token_list) != len(rhs.token_list):
            return False

        for tokens in zip(self.token_list, rhs.token_list) :
            if tokens[0].__class__ != tokens[1].__class__ : 
                return False

            # Recurse into sub-expressions. It's tokens all the way down!
            if not tokens[0] == tokens[1] :
                return False

        return True

    def makefile(self):
        # Build a Makefile string from this rule expression.
        return "".join([t.makefile() for t in self.token_list])
            
    def __len__(self):
        return len(self.token_list)

    def eval(self, symbol_table):
        return "".join([e.eval(symbol_table) for e in self.token_list])

class VarRef(Expression):
    # A variable reference found in the token stream. Save as a nested set of
    # tuples representing a tree. 
    # $a            ->  VarExp(a)
    # $(abc)        ->  VarExp(abc,)
    # $(abc$(def))  ->  VarExp(abc,VarExp(def),)
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

    def eval(self, symbol_table):
        s = ""
        for sym in self.token_list:
            s += symbol_table.fetch(sym.eval(symbol_table))
        return s

class AssignmentExpression(Expression):
    def __init__(self, token_list):
        Expression.__init__(self, token_list)
        self.sanity()

    def eval(self, symbol_table):
        self.sanity()
        lhs = self.token_list[0].eval(symbol_table)
        logger.debug("assignment lhs=%s", lhs)
        rhs = self.token_list[2].eval(symbol_table)
        logger.debug("assignment rhs=%s", rhs)
        # TODO handle different styles of assignment
        symbol_table.add(lhs, rhs)
        return None

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

        Expression.__init__(self, token_list)

    def makefile(self):
        # rule-targets rule-op prereq-list <CR>
        #     recipes
        assert len(self.token_list)==4, len(self.token_list)

        # davep 03-Dec-2014 ; need spaces between targets, no spaces between
        # prerequisites
        # 
        # first the targets
        s = " ".join( [ t.makefile() for t in self.token_list[0].token_list ] )

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

        logger.debug("add_recipe_list() rule=%s", self.makefile())
        logger.debug("add_recipe_list() recipe_list=%s", str(recipe_list))

        # replace my recipe list with this recipe list
        self.token_list[3] = recipe_list
        self.recipe_list = recipe_list

#        logger.debug("add_recipe_list() %s", self.makefile())

    def eval(self, symbol_table):
        # TODO
        logger.error("%s eval not implemented yet", type(self))

class PrerequisiteList(Expression):
     # davep 03-Dec-2014 ; FIXME prereq list must be an array of expressions,
     # not an expression itself or wind up with problems with spaces
     #  $()a vs $() a
     # (note the space before 'a')

    def __init__(self, token_list):
        for t in token_list :
            assert isinstance(t, Expression), (type(t,))

        self.token_list = token_list
        
    def makefile(self):
        # space separated
        s = " ".join( [ t.makefile() for t in self.token_list ] )

        return s

class Recipe(Expression):
    # A single line of a recipe
    pass

class RecipeList( Expression ) : 
    # A collection of Recipe objects
    def __init__(self, recipe_list):
        for r in recipe_list :
            assert isinstance(r, Recipe), (r,)
        
        Expression.__init__(self, recipe_list)

    def makefile(self):
        # newline separated, tab prefixed
        s = ""
        if len(self.token_list):
            s = "\t"+"\n\t".join( [ t.makefile() for t in self.token_list ] )
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

class OverrideDirective(Directive):
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
        VirtualLine.validate(vline_list)
        self.vline_list = vline_list
        super().__init__()

    def makefile(self):
        VirtualLine.validate(self.vline_list)
        
        s = "".join( [ str(v) for v in self.vline_list ] )
        return s

    def __str__(self):
        # This class contains an array of VirtualLine instances. Need to
        # recreate the appropriate Python code.
        s = ", ".join( [v.python() for v in self.vline_list] )
        return "LineBlock([{0}])".format(s)

class ConditionalBlock(Directive):
    name = "(should not see this)"

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

    def __init__(self, conditional_blocks=None, else_blocks=None ) :
        super().__init__()

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
        
        if conditional_blocks : 
            for block_tuple in conditional_blocks : 
                cond_expr, cond_block_list = block_tuple
                self.add_conditional( cond_expr )
                for b in cond_block_list : 
                    self.add_block( b )

        # were we given an else_block?
        # (an empty [] else block is treated like an empty else condition)
        # ifdef FOO
        #   blah blah blah
        # else <--- still want the else to print
        # endif
        if not else_blocks is None : 
            self.start_else()
            for b in else_blocks: 
                self.add_block( b )
        
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

class ConditionalDirective(Directive):
    name = "(should not see this)"
    
class IfdefDirective(ConditionalDirective):
    name = "ifdef"

class IfndefDirective(ConditionalDirective):
    name = "ifndef"

class IfeqDirective(ConditionalDirective):
    name = "ifeq"

class IfneqDirective(ConditionalDirective):
    name = "ifneq"

class DefineDirective(Directive):
    name = "define"

    def __init__(self, macro_name, line_block=None):
        super().__init__()
        self.string = macro_name
        assert isinstance(macro_name, str), type(macro_name)

        self.line_block = line_block if line_block else LineBlock([])

    def __str__(self):
        return "{0}(\"{1}\", {2})".format(self.__class__.__name__,
                        self.string,
                        str(self.line_block))

    def set_block(self, line_block):
        self.line_block = line_block

    def makefile(self):
        return "define {0}\n{1}endef".format(
                        self.string,
                        self.line_block.makefile() )
        

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


