# SPDX-License-Identifier: GPL-2.0
from pymake.vline import VirtualLine, RecipeVirtualLine
from pymake.scanner import ScannerIterator
import pymake.tokenizer as tokenizer
import pymake.symtablemk as symtablemk
import pymake.source as source
from pymake.constants import backslash, eol
import pymake.shell as shell

def make_viter(s):
    # note: only use this fn for recipes that don't have backslashes
    # (recipes have different backslash rules than regular make code)
    vline = VirtualLine([s], (0,0), "/dev/null")
    viter = iter(vline)
    return viter

def tokenize_recipe_str(s):
    # can't use .split() because need to carefully preserve eol
#    lines_list = s.split("\n")

    src = source.SourceString(s)
    src.load()

    vline = RecipeVirtualLine(src.file_lines, (0,0), "/dev/null")
    viter = iter(vline)
    r = tokenizer.tokenize_recipe(viter)
    assert not viter.remain()
    return r

def test_comment():
    s = "# this is a test\n"
    viter = make_viter(s)
    tokenizer.comment(viter)
    assert not viter.remain()

def test_assign_plus_comment():
    s = "foo := bar # this is a test\n"
    viter = make_viter(s)
    stmt = tokenizer.tokenize_assignment_statement(viter)
    assert stmt.assign_op.makefile() == ":="
    assert not viter.remain()

    symbol_table = symtablemk.SymbolTable()
    assert len(stmt.lhs)==2, len(lhs)
    assert stmt.lhs[0].eval(symbol_table)=="foo"
    assert stmt.lhs[1].eval(symbol_table)==" "
    # note trailing whitespace!
    assert stmt.rhs.eval(symbol_table)=="bar "

def test_tokenize_assign():
    s = "foo := bar # this is a test\n"
    viter = make_viter(s)
    expr = tokenizer.tokenize_assignment_statement(viter)

    symbol_table = symtablemk.SymbolTable()
    s = expr.eval(symbol_table)
    assert not s

    # note trailing whitespace!
    assert symbol_table.fetch("foo")=="bar "

def test_tokenize_assign_recursive():
    s = "foo = bar # this is a test\n"
    viter = make_viter(s)
    expr = tokenizer.tokenize_assignment_statement(viter)

    symbol_table = symtablemk.SymbolTable()
    s = expr.eval(symbol_table)
    assert not s

    # note trailing whitespace!
    assert symbol_table.fetch("foo")=="bar "

def test_backslash_expression():
    a = ["foo\\\n","=\\\n","bar\n"]
    vline = VirtualLine(a, (0,0), "/dev/null")
    assert str(vline)=="foo = bar\n"
    viter = iter(vline)
    stmt = tokenizer.tokenize_assignment_statement(viter)
    assert stmt.assign_op.makefile() == "="
    assert not viter.remain()

def test_tokenize_simple_recipe():
    s = "	@echo foo\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)
    assert r.makefile() == "@echo foo"

def test_tokenize_simple_whitespace_recipe():
    s = "			@echo foo\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)
    assert r.makefile() == "@echo foo"

def test_tokenize_varref_recipe():
    s = "	@echo $(foo)\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)

    symbol_table = symtablemk.SymbolTable()
    symbol_table.add("foo", "bar")
    s = r.eval(symbol_table)

    assert r.makefile() == "@echo $(foo)"
    assert s == "@echo bar"

def test_tokenize_single_letter_varref_recipe():
    # make sure I can handle varref w/o ()s
    s = "	@echo $f\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)

    symbol_table = symtablemk.SymbolTable()
    symbol_table.add("f", "bar")
    s = r.eval(symbol_table)

    # my round trip code will always add () around varrefs
    assert r.makefile() == "@echo $(f)"
    assert s == "@echo bar"

def test_recipe_with_backslash():
    s = '	@print "%s\\n%s\\n" $$PWD $$PWD'

    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)

    symbol_table = symtablemk.SymbolTable()
    s = r.eval(symbol_table)
    assert s == '@print "%s\\n%s\\n" $PWD $PWD'

def test_tokenize_bash_var_recipe():
    # double $ which will be replaced with single $
    s = "	@echo $$PATH\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)

    symbol_table = symtablemk.SymbolTable()
    s = r.eval(symbol_table)

    assert r.makefile() == "@echo $$PATH"
    assert s == "@echo $PATH"

def test_tokenize_double_dollar_recipe():
    # In bash, the pid of the process is $$
    # % echo pid=$$
    # In order to get $$ to the shell, we have to escape both $ thus $$$$
    s = "	@echo pid=$$$$\n"
    viter = make_viter(s)
    r = tokenizer.tokenize_recipe(viter)

    symbol_table = symtablemk.SymbolTable()
    s = r.eval(symbol_table)

    assert r.makefile() == "@echo pid=$$$$"
    assert s == "@echo pid=$$"

# 5.1.1 Splitting Recipe Lines
#
# "... backslash/newline pairs are not removed from the recipe. Both the
# backslash and the newline characters are preserved and passed to the shell."
#
# If the first character of the next line after the backslash/newline is the
# recipe prefix character (a tab by default [...]) then that character (and
# only that character) is removed. Whitespace is never added to the recipe."
#
# -- GNU Make 4.3 Jan 2020
#
def test_rules_backslash_nospace():
    # from the GNU Make manual
    s = """\
	echo no\\
space
"""
    r = tokenize_recipe_str(s)
    symbol_table = symtablemk.SymbolTable()
    recipe_str = r.eval(symbol_table)
    print("recipe=\n%r" % recipe_str)
    p = shell.execute(recipe_str, symbol_table)
    assert p.exit_code==0
    assert p.stdout == "nospace\n"

def test_rules_backslash_one_space_1():
    # from the GNU Make manual
    s = """\
	echo one \\
	space
"""
    r = tokenize_recipe_str(s)
    symbol_table = symtablemk.SymbolTable()
    recipe_str = r.eval(symbol_table)
    print("recipe=\n%r" % recipe_str)
    p = shell.execute(recipe_str, symbol_table)
    assert p.exit_code==0
    assert p.stdout == "one space\n"

def test_rules_backslash_one_space_2():
    # from the GNU Make manual
    s = """\
	echo one\\
	 space
"""
    r = tokenize_recipe_str(s)
    symbol_table = symtablemk.SymbolTable()
    recipe_str = r.eval(symbol_table)
    print("recipe=\n%r" % recipe_str)
    p = shell.execute(recipe_str, symbol_table)
    assert p.exit_code==0
    assert p.stdout == "one space\n"

def test_rules_backslashes_linux_kernel_makefile():
    # from the linux kernel makefile, a nice complicated recipe with backslashes
    # include/config/auto.conf:
    s = """\
	@test -e include/generated/autoconf.h -a -e $@ || (		\\
	echo >&2;							\\
	echo >&2 "  ERROR: Kernel configuration is invalid.";		\\
	echo >&2 "         include/generated/autoconf.h or $@ are missing.";\\
	echo >&2 "         Run 'make oldconfig && make prepare' on kernel src to fix it.";	\\
	echo >&2 ;							\\
	/bin/false)
"""
    r = tokenize_recipe_str(s)

    target = "include/config/auto.conf"
    symbol_table = symtablemk.SymbolTable()
    symbol_table.add("@", target)

    recipe_str = r.eval(symbol_table)
    print("recipe=\n%r" % recipe_str)

    # quick sanity checks
    assert recipe_str[0] == '@'
    p = recipe_str.index(backslash) # backslashes are preserved
    assert recipe_str[p+1] in eol  # newlines are preserved

    # leading recipeprefix after backslash/newline is removed
    assert recipe_str[p+2] == 'e'  # 2nd line, starts with 'echo '

    expect_list = ( "@test", "echo", "echo", "echo", "echo", "echo", "/bin/false)" )
    lines_list = recipe_str.split("\n")
    for line_str, expect_str in zip(lines_list, expect_list):
        assert line_str.startswith(expect_str)
        if expect_str != "/bin/false)":
            assert line_str[-1] == backslash

