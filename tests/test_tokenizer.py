from vline import VirtualLine
from scanner import ScannerIterator
import tokenizer
import symtablemk

def make_viter(s):
    vline = VirtualLine([s], (0,0), "/dev/null")
    viter = iter(vline)
    return viter

def test_comment():
    s = "# this is a test\n"
    viter = make_viter(s)
    tokenizer.comment(viter)
    assert not viter.remain()

def test_assign_plus_comment():
    s = "foo := bar # this is a test\n"
    viter = make_viter(s)
    lhs, assignop = tokenizer.tokenize_statement_LHS(viter)
    assert str(assignop.string) == ":="
    rhs = tokenizer.tokenize_assign_RHS(viter)
    assert not viter.remain()

    symbol_table = symtablemk.SymbolTable()
    assert lhs.eval(symbol_table)=="foo"
    # note trailing whitespace!
    assert rhs.eval(symbol_table)=="bar "

def test_tokenize_assign():
    s = "foo := bar # this is a test\n"
    viter = make_viter(s)
    expr = tokenizer.tokenize_statement(viter)

    symbol_table = symtablemk.SymbolTable()
    s = expr.eval(symbol_table)
    assert not s

    # note trailing whitespace!
    assert symbol_table.fetch("foo")=="bar "

def test_tokenize_assign_recursive():
    s = "foo = bar # this is a test\n"
    viter = make_viter(s)
    expr = tokenizer.tokenize_statement(viter)

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
    lhs, assignop = tokenizer.tokenize_statement_LHS(viter)
    assert str(assignop.string) == "="
    rhs = tokenizer.tokenize_assign_RHS(viter)
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

