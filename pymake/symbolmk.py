# SPDX-License-Identifier: GPL-2.0

import logging

logger = logging.getLogger("pymake.symbol")
#logger.setLevel(level=logging.DEBUG)

from pymake.constants import whitespace
from pymake.printable import printable_char, printable_string
from pymake.vline import VirtualLine, VChar, VCharString, get_vline
from pymake.version import Version
from pymake.error import *
import pymake.shell as shell
from pymake.scanner import ScannerIterator
import pymake.source as source
from pymake.debug import *

_testing = False

_debug = False

__all__ = [ "Symbol",
            "Literal",
            "Operator",
            "AssignOp",
            "RuleOp",
            "Expression",
            "VarRef",
            "AssignmentExpression",
            "RuleExpression",
            "TargetList",
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
            "DefineBlock",
            "DefineDirective",
            "UnDefineDirective",
            "Makefile",
]

# hack dependency injection
tokenize_statement = None
parse_vline_stream = None

# test/debug fn for debugger
def _view(token_list):
    return "".join([str(t) for t in token_list])

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
                # if seeing an AttributeError then trying to pass in a non-VCharString
                if _testing:
                    # if we're running test code, allow array of VChars to sneak in
                    vstring = VCharString([VChar(c,(0,0),"...testing") for c in vstring])
                else:
                    logger.error(type(vstring))
                    raise
            logger.debug("new Symbol vstring=\"%s\" at %r", printable_string(str(vstring)), vstring.get_pos())
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
        return self.string.get_pos()

    def is_whitespace(self):
        return self.string is not None and self.string[0].char in whitespace

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
        assert len(token_list) >= 0
        logger.debug("new Expression with %d tokens", len(token_list))
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

    def xxx__eq__(self, rhs):
        assert 0, "do I use this anymore?"

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
            logger.debug("expression eval e=%s", e)

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
#        logger.debug("varref=%r eval start", self)
        key = [t.eval(symbol_table) for t in self.token_list]
        logger.debug("varref=%r eval key=%r", self, key)
        return symbol_table.fetch("".join(key), self.get_pos())

class AssignmentExpression(Expression):
    def __init__(self, token_list):
        super().__init__(token_list)
        self.sanity()
            
    @staticmethod
    def assign(lhs, op, rhs, symbol_table):
        # from the gnu make pdf:
        # immediate = deferred
        # immediate ?= deferred
        # immediate := immediate
        # immediate ::= immediate
        # immediate += deferred or immediate
        # immediate != immediate

        logger.debug("assignment lhs=%s op='%s'", lhs, op)
        key = lhs.eval(symbol_table)

        # handle different styles of assignment
        if op == ":=" or op == "::=":
            # simply expanded
            rhs = rhs.eval(symbol_table)
        elif op == "=":
            # recursively expanded
            # store the expression in the symbol table without evaluating
            pass
        elif op == "!=":
            # != seems to be a > 3.81 feature so add a version check here
            if Version.major < 4:
                raise VersionError("!= not in this version of make")

            # execute RHS as shell
            rhs = shell.execute_tokens(rhs, symbol_table )
        elif op == "?=":
            # deferred expand
            # store the expression in the symbol table w/o eval
            pass 
        elif op == "+=":
            # Append is a little tricky because we have to treat recursively vs
            # simply expanded variables differently (making the expression
            # sensitive to what's in the LHS). Pass the Expression to the
            # symbol table to figure out.
            pass
        else:
            # TODO
            raise NotImplementedError("op=%s"%op)

        logger.debug("assignment rhs=%s", rhs)

        pos = lhs.get_pos()
        assert pos is not None

        if op == "?=":
            symbol_table.maybe_add(key, rhs, pos)
        elif op == "+=":
            symbol_table.append(key, rhs, pos)
        else:
            symbol_table.add(key, rhs, pos)
        return ""


    def eval(self, symbol_table):
        self.sanity()

        # FIXME I have a sneaking suspicion the rhs can be token_list[3:]
        # pyfiles := $(wildcard foo*.py) $(wildcard bar*.py) $(wildcard baz*.py)
        assert len(self.token_list) == 3

        lhs = self.token_list[0]
        op = self.token_list[1]
        rhs = self.token_list[2]

        return self.assign(lhs, op, rhs, symbol_table)

    def sanity(self):
        # AssignmentExpression :=  Expression AssignOp Expression
        assert len(self.token_list)==3, len(self.token_list)
        assert isinstance(self.token_list[0], Expression), type(self.token_list[0])
        assert isinstance(self.token_list[1], AssignOp), type(self.token_list[1])
        assert isinstance(self.token_list[2], Expression), type(self.token_list[2])

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

        assert len(token_list)==3, len(token_list)

        assert isinstance(token_list[0], Expression), (type(token_list[0]),)
        assert isinstance(token_list[1], RuleOp), (type(token_list[1]),)

        if isinstance(token_list[2], PrerequisiteList) : 
            pass
        elif isinstance(token_list[2], AssignmentExpression) :
            # target specific variable assignment
            # see: 6.11 Target-specific Variable Values  GNU Make V.4.3 Jan2020
            raise NotImplementedError()
            pass 
        else:
            assert 0, (type(token_list[2]),)

        # Start with a default empty recipe list (so this object will always
        # have a RecipeList instance)
        self.recipe_list = RecipeList([]) 

        super().__init__(token_list)

        self.targets = self.token_list[0]
        self.rule_op = self.token_list[1]
        self.prereqs = self.token_list[2]

    def makefile(self):
        # rule-targets rule-op prereq-list <CR>
        #     recipes
        s = ""

        # Embed the filename+pos of the rule in the output makefile.
        if _debug:
            filename, pos = self.get_pos()
            s += "# %s %s\n" % (filename, pos)

        # need spaces between targets and prerequisites

        # first the targets
        s += " ".join( [ t.makefile() for t in self.targets.token_list ] )

        # operator
        s += self.rule_op.makefile()

        # prerequisite(s)
        s += self.prereqs.makefile()

        s += "\n"

        # recipe(s)
        s += self.recipe_list.makefile()
        return s

    def add_recipe( self, recipe ) : 
        assert isinstance(recipe, Recipe)

        logger.debug("add_recipe() rule=%s", str(self))
        self.recipe_list.append(recipe)

    def eval(self, symbol_table):
        # Return two arrays:
        #   [0] : target(s) (string)
        #   [1] : prerequisite(s) (strings)
        #
        # BIG FAT NOTE: This eval() is different than the other Symbol stack
        # eval() methods which all return a single string.
        # 

        # Must be super careful to eval() the target and prerequisites only
        # once! There may be side effects so must not re-eval() 
        # UNLESS:
        # Make allows the same target in multiple rules. Make will eval each
        # time.

        targets = self.targets.eval(symbol_table).split()
        prereqs = self.prereqs.eval(symbol_table).split()

        # throw away empty strings
        targets = [t for t in targets if t]
        prereqs = [p for p in prereqs if p]

        return targets, prereqs

class RuleList(Expression):
     # RuleList class used for the targets and the prerequisites. Is an array
     # of expressions, not an expression itself or wind up with problems with
     # spaces
     #  $()a vs $() a
     # (note the space before 'a')
     #
     # While an Expression is NULL joined, a RuleList is space joined.
    def makefile(self):
        # space separated
        return " ".join( [ t.makefile() for t in self.token_list ] )

    def eval(self, symbol_table):
        # space separated
        return " ".join([t.eval(symbol_table) for t in self.token_list])

    def __iter__(self):
        return iter(self.token_list)

class TargetList(RuleList):
    def __init__(self, token_list):
        expr_list = []
        new_token_list = []
        
        # make a new token_list by creating an Expression of all whitespace
        # separated tokens
        for t in token_list:
            if t.is_whitespace(): 
                if new_token_list:
                    expr_list.append(Expression(new_token_list))
                    new_token_list = []
            else:
                new_token_list.append(t)
        if new_token_list:
            expr_list.append(Expression(new_token_list))
            new_token_list = []

        super().__init__(expr_list)

class PrerequisiteList(RuleList):
    # prerequisites' scanner already removes whitespace
    pass

class Recipe(Expression):
    # A single line of a recipe

    def __init__(self, token_list):
        super().__init__(token_list)

    def eval(self, symbol_table):
        # this method does NOT execute the shell but simply will run the string
        # through the symbol table.
        s = super().eval(symbol_table)

        # recipes will have $$ as an escape for a single $ that should be
        # passed to the shell
        # e.g., "echo $$PATH" becomes "echo $PATH" sent to the shell
        return s.replace("$$","$")

    
class RecipeList( Expression ) : 
    # A collection of Recipe objects
    def __init__(self, recipe_list):
        for r in recipe_list :
            assert isinstance(r, Recipe), (r,)
        
        super().__init__(recipe_list)

    def append(self, recipe):
        self.token_list.append(recipe)

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

    def __init__(self, keyword, expression):
        # ha ha type checking.  keyword needs to be a VCharString which tells
        # us the file+position of the directive
        assert isinstance(keyword, VCharString), type(keyword)

        super().__init__(keyword)

        # expression may be None
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

    # "If you want all variables to be exported by default, you can use export
    # by itself:
    # export
    # "This tells make that variables which are not explicitly mentioned in an
    # export or unexport directive should be exported. Any variable given in an
    # unexport directive will still not be exported."
    #  GNU make Version 4.3 January 2020

    # /* (un)export by itself causes everything to be (un)exported. */ 
    # src/read.c GNU Make 4.4.1 source

    def __init__(self, keyword, expression=None):
        # TODO 
        # make 3.81 "export define" not allowed ("missing separator")
        # make 3.82 works
        # make 4.0  works
#        if not(Version.major==3 and Version.minor==81) : 
#            raise TODO()

        super().__init__(keyword, expression)

    def eval(self, symbol_table):
        if not self.expression:
            # export everything
            symbol_table.export()
            return ""

        if isinstance(self.expression,AssignmentExpression):
            symbol_table.export_start()
            s = self.expression.eval(symbol_table)
            symbol_table.export_stop()
        else:
            s = self.expression.eval(symbol_table)
            for name in s.split():
                symbol_table.export(name)

        return ""

class UnExportDirective(ExportDirective):
    name = "unexport"

    # "Likewise, you can use unexport by itself to tell make not to export
    # variables by default.  Since this is the default behavior, you would only
    # need to do this if export had been used by itself earlier (in an included
    # makefile, perhaps)."
    #  GNU make Version 4.3 January 2020

    # export by itself exports everything
    # unexport turns that off. Variables explicitly export'd remain export.
    #

    def eval(self, symbol_table):
        if self.expression is None:
            # unexport everything
            symbol_table.unexport()
        else:
            s = self.expression.eval(symbol_table)
            for name in s.split():
                symbol_table.unexport(name)

        return ""

class IncludeDirective(Directive):
    name = "include"

    def __init__(self, keyword, expression):
        self.source = None

        super().__init__(keyword, expression)

    # "If an included makefile cannot be found in any of these directories, a
    # warning message is generated, but it is not an immediately fatal error;
    # processing of the makefile containing the include continues. Once it has
    # finished reading makefiles, make will try to remake any that are out of
    # date or don’t exist. See Section 3.5 [How Makefiles Are Remade], page 15.
    # Only after it has tried to find a way to remake a makefile and failed,
    # will make diagnose the missing makefile as a fatal error." 
    # -- GNU Make Version 4.3 Jan 2020
    # 
    # TODO So I'll need a way of caching the file include failures. Will need
    # to retry between execute() and running the Rules.
    def eval(self, symbol_table):
        s = self.expression.eval(symbol_table)

        # GNU Make ignores an empty include
        if not s:
            return []

        symbol_table.append("MAKEFILE_LIST", s, self.expression.get_pos())

        self.source = source.SourceFile(s)
        self.source.load()
        line_scanner = ScannerIterator(self.source.file_lines, self.source.name)
        vline_iter = get_vline(self.source.name, line_scanner)

        statement_list = [parse_vline_stream(vline, vline_iter) for vline in vline_iter] 
        return statement_list

class MinusIncludeDirective(IncludeDirective):
    # handles -include directives
    name = "-include"

    def eval(self, symbol_table):
        try:
            return super().eval(symbol_table)
        except FileNotFoundError:
            return []

class SIncludeDirective(MinusIncludeDirective):
    # handles sinclude directives (another name for -include)
    name = "sinclude"

class VpathDirective(Directive):
    name = "vpath"

class OverrideDirective(Directive):
    name = "override"

    def __init__(self, expression ):
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

    def get_pos(self):
        vline = self.vline_list[0]
        return vline.get_pos()

    def makefile(self):
        if _debug:
            [vline.validate() for vline in self.vline_list]
        
        s = "".join( [ str(v) for v in self.vline_list ] )
        return s

    def __str__(self):
        # This class contains an array of VirtualLine instances. Need to
        # recreate the appropriate Python code.
        s = ", ".join( [v.python() for v in self.vline_list] )
        return "{0}([{1}])".format( self.__class__.__name__, s)

    def eval(self, symbol_table):
        vline_iter = iter(self.vline_list)

        statement_list = [parse_vline_stream(vline, vline_iter) for vline in vline_iter] 
        return statement_list


class ConditionalBlock(Symbol):
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

    def __init__(self) :
        super().__init__()
        
        # cond_expr is an array of ConditionalDirective
        #
        # cond_blocks is an array of arrays. Each cond_block[n] array is an
        # array of either LineBlock or ConditionalBlock
        self.cond_exprs = []
        self.cond_blocks = []

    def get_pos(self):
        return self.cond_exprs[0].get_pos()

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
        #   tuple[0] is ConditionalDirective
        #   tuple[1] is array of (LineBlock|ConditionalBlock)
        s += "["
        s += ", ".join( [ "("+str(expr)+", "+blocklist_str(blocklist)+")" for expr, blocklist in zip(self.cond_exprs, self.cond_blocks) ] )
        s += "]"

        # add else case
        if len(self.cond_blocks) > len(self.cond_exprs):
            # have an else
            s += ", " + blocklist_str(self.cond_blocks[-1])

        s += ")"
        return s

    def eval(self, symbol_table):
        logger.debug("eval %s", self.name)

        for expr,block_list in zip(self.cond_exprs,self.cond_blocks):
            flag = expr.eval(symbol_table)
            if flag:
                # We found a truthy so execute the block then we're done.
                return block_list

        # At this point we have run out of expressions to evaluate.
        # Is there one more cond_block which indicates an unconditional else?
        if len(self.cond_blocks) > len(self.cond_exprs):
            assert len(self.cond_blocks) == len(self.cond_exprs)+1

            return self.cond_blocks[-1]

        # At this point we found no truthy conditionals and no else condition.
        # So we have nothing to return.
        return []

class ConditionalDirective(Directive):
    name = "(should not see this)"

    def __init__(self, keyword, expression):
        super().__init__(keyword, expression)

        # see partial_init()
        self.vcstring = None

    def partial_init(self, vcstring):
        # used when we have a nested conditional where the expression can't be parsed yet.
        # for example:
        # ifdef FOO
        #   ifdef BAR
        #         ^^^-- don't parse this conditional until we're eval'ing the outer FOO block
        # Need to preserve the raw vcharstring so we can parse it later.
        assert isinstance(vcstring,VCharString)
        logger.debug("%s partial_init of \"%s\" at %r", self.string, 
            printable_string(str(vcstring)), vcstring.get_pos())
        self.vcstring = vcstring

    def get_pos(self):
        return self.string.get_pos()


class IfdefDirective(ConditionalDirective):
    name = "ifdef"

    # 
    # "If the value of that variable has a non-empty value, the text-if-true is
    # effective; otherwise, the text-if-false, if any, is effective. Variables
    # that have never been defined have an empty value."
    #
    # This is different than the C preprocessor which treats even empty
    # variables as ifdef'd => true
    #
    def eval(self, symbol_table):
        # don't use .fetch() because we don't want to eval the expression in
        # the symbol table. We just want proof of exist.
        name = self._eval(symbol_table)
        return symbol_table.ifdef(name)

    def _parse(self):
        # FIXME this ugly and slow and ugly and I'd like to fix it
        # (circular imports are circular)
        from pymake.tokenizer import tokenize_statement
        self.expression = tokenize_statement(ScannerIterator(self.vcstring.chars, None))
        
    def _eval(self, symbol_table):
        logger.debug("eval %s", self.name)
        if self.expression is None:
            # if this fails, partial_init() should have been called
            assert self.vcstring is not None
            self._parse()

#        breakpoint()
        name = self.expression.eval(symbol_table)
        return name

class IfndefDirective(IfdefDirective):
    name = "ifndef"

    def eval(self, symbol_table):
        logger.debug("eval %s at %r", self.name, self.get_pos())
        name = self._eval(symbol_table)

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

    def __init__(self, keyword, expr1, expr2):
        # expr1, expr2 may be None
        self.expr1 = expr1
        self.expr2 = expr2
        super().__init__(keyword, self.expr1)

    def makefile(self):
        if self.expr1 is not None:
            # we have parsed our vcstring (if any)
            return "%s (%s,%s)" % (self.name, self.expr1.makefile(), self.expr2.makefile())
        else:
            return "%s %s" % (self.name, str(self.vcstring))

    def __str__(self):
        return "%s(%s,%s)" % (self.__class__.__name__, self.expr1, self.expr2)

    def _parse(self):
        # We are now parsing a previously read directive nested inside another
        # directive. 
        #
        # FIXME this ugly and slow and ugly and I'd like to fix it
        # (circular imports are circular)
        from pymake.parsermk import parse_ifeq_conditionals
        expr = tokenize_statement(ScannerIterator(self.vcstring.chars, None))
        self.expr1, self.expr2 = parse_ifeq_conditionals(expr, self.name)

    def _exprs_eval(self, symbol_table):
        if self.expr1 is None:
            # if this fails, partial_init() was not called as required
            assert self.vcstring is not None

            self._parse()

        if get_line_number(self) == 150:
            breakpoint()

        s1 = self.expr1.eval(symbol_table)
        s2 = self.expr2.eval(symbol_table)
        return s1, s2

    def eval(self, symbol_table):
        s1,s2 = self._exprs_eval(symbol_table)
        logger.debug("ifeq compare \"%s\"==\"%s\"", s1, s2)
        return s1 == s2

class IfneqDirective(IfeqDirective):
    name = "ifneq"

    def eval(self, symbol_table):
        s1,s2 = self._exprs_eval(symbol_table)
        logger.debug("ifneq compare \"%s\"==\"%s\"", s1, s2)
        return s1 != s2

class DefineBlock(LineBlock):
    # Defining Multi-Line Variables.
    # In a LineBlock the contents are Make statements that will be executed.
    # In a DefineBlock the contents are strings that will only have varref
    # substitutions.
    def __init__(self, vline_list):
        super().__init__(vline_list)

        # eval() will tokenize the contents of this block. We'll cache the
        # tokenized values here.
        self.statement_list = None

    def eval(self, symbol_table):
        if self.statement_list is None:
            self.statement_list = [tokenize_statement(iter(v)) for v in self.vline_list]

        # TODO make this one list comprehension statement 
        s_list = []
        for stmt in self.statement_list:
            s = stmt.eval(symbol_table)
            s_list.append(s)

        # "However, note that using two separate lines means make will invoke
        # the shell twice, running an independent sub-shell for each line. See
        # Section 5.3 [Recipe Execution], page 46." GNU Make 4.2 2020 
        #
        # Join the results together with \n and hope for the best. (See also
        # execute_rule() in pymake.py)
        return "\n".join(s_list)

class DefineDirective(Directive):
    name = "define"

    def __init__(self, keyword, varname, assign_op_str, block):
        # ha ha type checking
        assert isinstance(assign_op_str, str)

        # self.string will be 'define' vcstr
        # self.expression is the varname (lhs)
        super().__init__(keyword, varname)

        self.assign_op_str = assign_op_str
        self.block = block

    def __str__(self):
        return "{0}(\"{1}\", {2})".format(self.name,
                        str(self.expression),
                        str(self.block))

    def makefile(self):
        s = str(self.block)
        return "{0} {1} {2}\n{1}\nendef".format(
                        str(self.string),
                        self.expression.makefile(),
                        self.assign_op_str,
                        self.block.makefile() )

    # "The final newline before the endef is not included in the value; if you
    # want your value to contain a trailing newline you must include a blank
    # line." -- GNU Make 4.3 Jan 2020
    def eval(self, symbol_table):
        # self.expression contains the directive's name
        
        # use AssignmentExpression so all the variable type and assignment type
        # special cases are in one place
        return AssignmentExpression.assign(self.expression, self.assign_op_str, 
                    self.block, symbol_table)


class UnDefineDirective(Directive):
    name = "undefine"

    def eval(self, symbol_table):
        s = self.expression.eval(symbol_table)

        # TODO check for valid varname

        symbol_table.undefine(s)

        return ""

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

    def get_pos(self):
        return self.token_list[0].get_pos()

