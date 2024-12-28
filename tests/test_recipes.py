# SPDX-License-Identifier: GPL-2.0

# whitebox test parsing a block of recipes

from pymake import pymake
from pymake.scanner import ScannerIterator
import pymake.parser as parser
import pymake.source as source
import pymake.symbol as symbol
import pymake.symtable as symtable
from pymake.constants import backslash
import pymake.vline as vline

def parse_string(s):
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    vline_iter = vline.get_vline(src.name, line_scanner)
    statement_list = [v for v in pymake.parse_vline(vline_iter)]

    assert not line_scanner.remain()
    return statement_list

def make_recipelist(s):
    # everything in 's' should be a recipe
    statement_list = parse_string(s)
    return symbol.RecipeList(statement_list)

def test_parse_recipes_simple():
    s = """\
	@echo foo
	@echo bar
	@echo baz
"""
    recipe_list = make_recipelist(s)
    assert len(recipe_list)==3

    symbol_table = symtable.SymbolTable()
    for recipe in recipe_list:
        s = recipe.eval(symbol_table)
        assert s.startswith("@echo ")

def test_parse_recipes_comments():
    s = """\
	@echo foo
# this is a makefile comment
	@echo bar
	# this is a shell comment
	@echo baz
"""
    recipe_list = make_recipelist(s)

    # the makefile comment should be discarded but the shell comment is preserved
    assert len(recipe_list)==4

    expect_list = ( "@echo foo", "@echo bar", "# this is a shell comment", "@echo baz" )
    symbol_table = symtable.SymbolTable()
    for (recipe, expect_str) in zip(recipe_list, expect_list):
        s = recipe.eval(symbol_table)
        assert s == expect_str

def test_parse_recipes_backslashes():
    # from the GNU Make manual
    s = """\
	@echo no\\
space
	@echo no\\
	space
	@echo one \\
	space
	@echo one\\
	 space
"""
    recipe_list = make_recipelist(s)

    assert len(recipe_list)==4
    symbol_table = symtable.SymbolTable()
    for recipe in recipe_list:
        s = recipe.eval(symbol_table)
        # backslash is preserved
        p = s.index(backslash)
        assert s.startswith("@echo")
        assert s.endswith("space")

def test_parse_end_of_recipes():
    s = """\
	@echo foo
	@echo bar

$(info this should be end of recipes)
"""
    statement_list = parse_string(s)
    recipe_list = symbol.RecipeList(statement_list[0:2])

    # last statement should be an Expression
    last = statement_list[-1]
    assert isinstance(last, symbol.Expression)
    assert str(last) == 'Expression([Info([Literal("this should be end of recipes")])])'

def test_trailing_recipes():
    # handle rules that have recipes on the same line as the rule 
    s = """\
foo: ; @echo foo
	@echo bar
	@echo baz
"""
    statement_list = parse_string(s)
    assert len(statement_list)==3
    rule = statement_list[0]
    rule.add_recipe(statement_list[1])
    rule.add_recipe(statement_list[2])

    symbol_table = symtable.SymbolTable()
  
    expect_list = ( "@echo foo", "@echo bar", "@echo baz" )
    symbol_table = symtable.SymbolTable()
    for (recipe, expect_str) in zip(rule.recipe_list, expect_list):
        s = recipe.eval(symbol_table)
        assert s == expect_str
        
def test_recipe_ifdef_block():
    s = """\
	@echo foo?
ifdef FOO
	@echo hello from foo!
endif # FOO
	@echo bar
"""
    statement_list = parse_string(s)
    assert isinstance(statement_list[0], symbol.Recipe)
    assert isinstance(statement_list[2], symbol.Recipe)

    # TODO add eval of the ifdef block to peek at the Recipe within
