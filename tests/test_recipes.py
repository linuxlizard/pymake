# SPDX-License-Identifier: GPL-2.0

# whitebox test parsing a block of recipes

from scanner import ScannerIterator
import parsermk
import source
import symtablemk
from constants import backslash
import vline

def make_recipelist(s):
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    recipe_list = parsermk.parse_recipes(line_scanner)
    assert not line_scanner.remain()
    return recipe_list

def test_parse_recipes_simple():
    s = """\
	@echo foo
	@echo bar
	@echo baz
"""
    recipe_list = make_recipelist(s)
    assert len(recipe_list)==3

    symbol_table = symtablemk.SymbolTable()
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
    symbol_table = symtablemk.SymbolTable()
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
    symbol_table = symtablemk.SymbolTable()
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
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    recipe_list = parsermk.parse_recipes(line_scanner)

    # should be one line remaining
    remaining_lines_list = line_scanner.remain()
    assert len(remaining_lines_list)==1
    assert remaining_lines_list[0] == "$(info this should be end of recipes)\n"

def test_trailing_recipes():
    # handle rules that have recipes on the same line as the rule 
    # e.g., foo: ; @echo bar
    dangling = "; @echo baz\n"
    s = """\
	@echo foo
	@echo bar
"""
    # dangling recipe must be VChars
    dangling_recipe_vline = vline.RecipeVirtualLine([dangling], (0,0), "/dev/null")
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)

    recipe_list = parsermk.parse_recipes(line_scanner, dangling_recipe_vline)

    assert not line_scanner.remain()
    assert len(recipe_list)==3
    symbol_table = symtablemk.SymbolTable()
  
    expect_list = ( "@echo baz", "@echo foo", "@echo bar" )
    symbol_table = symtablemk.SymbolTable()
    for (recipe, expect_str) in zip(recipe_list, expect_list):
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
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    recipe_list = parsermk.parse_recipes(line_scanner)

#    breakpoint()

