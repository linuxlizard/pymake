# SPDX-License-Identifier: GPL-2.0

# test parsing a whole rule
#
# XXX work in progress!

import pytest

from pymake.pymake import parse_vline
from pymake.scanner import ScannerIterator
import pymake.source as source
import pymake.symbol as symbol
import pymake.symtable as symtable
import pymake.vline as vline
from pymake.state import ParseState

def parse_rule_string(s):
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    vline_iter = vline.get_vline(src.name, line_scanner)

    state = ParseState()
    statement_list = [parse_vline(vline, vline_iter, state) for vline in vline_iter] 

    assert isinstance(statement_list[0], symbol.RuleExpression)

    for s in statement_list[1:]:
        assert isinstance(s, symbol.Recipe)

    return statement_list[0], statement_list[1:]

def run_rule(s, expect, symbol_table=None):
    if symbol_table is None:
        symbol_table = symtable.SymbolTable()

    rule, statement_list = parse_rule_string(s)
    target_list, prereq_list = rule.eval(symbol_table)
       
    assert len(target_list) == len(expect["targets"])
    assert target_list == expect["targets"]

    assert len(prereq_list) == len(expect["prereqs"])
    assert prereq_list == expect["prereqs"]

    # TODO add checks on expect["recipes"]


def test_simple_rule():
    s = """\
foo:
	@echo foo
"""
    expect = {
        "targets" : ["foo",],
        "prereqs" : [],
        "recipes"   : ["@echo foo"],
    }
    run_rule(s,expect)

def test_simple_rule_with_prereq():
    s = """\
foo: bar
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo",],
        "prereqs" : ["bar"],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_rule_with_multiple_target_multiple_prereq():
    s = """\
foo1 foo2 foo3 : bar1 bar2 bar3
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo1","foo2","foo3"],
        "prereqs" : ["bar1","bar2","bar3"],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_rule_expressions_as_target_and_prereq():
    s = """\
$a $b $c : $d $e $f
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo1","foo2","foo3"],
        "prereqs" : ["bar1","bar2","bar3"],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    symbol_table = symtable.SymbolTable()
    symbol_table.add("a", "foo1")
    symbol_table.add("b", "foo2")
    symbol_table.add("c", "foo3")
    symbol_table.add("d", "bar1")
    symbol_table.add("e", "bar2")
    symbol_table.add("f", "bar3")

    run_rule(s,expect, symbol_table)

def test_rule_empty_expressions():
    s = """\
$a $b $c : $d  $e $f
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo1","foo2","foo3"],
        "prereqs" : [],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    symbol_table = symtable.SymbolTable()
    symbol_table.add("a", "foo1")
    symbol_table.add("b", "foo2")
    symbol_table.add("c", "foo3")

    run_rule(s,expect, symbol_table)

def test_rule_one_expression_as_target_and_prereq():
    s = """\
$a$b$c : $d$e$f
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo"],
        "prereqs" : ["bar"],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    symbol_table = symtable.SymbolTable()
    symbol_table.add("a","f")
    symbol_table.add("b","o")
    symbol_table.add("c","o")
    symbol_table.add("d","b")
    symbol_table.add("e","a")
    symbol_table.add("f","r")

    run_rule(s,expect, symbol_table)

def test_simple_rule_dangling_recipe():
    s = """\
foo: ; @echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo",],
        "prereqs" : [],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_simple_rule_dangling_recipe_whitespace():
    s = """\
   foo	:		;			@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo",],
        "prereqs" : [],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_simple_rule_dangling_recipe_with_prereq():
    s = """\
   foo	:	bar	;			@echo foo
	@echo bar
"""
    expect = {
        "targets" : ["foo",],
        "prereqs" : ["bar",],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_rule_no_targets():
    # "rule without a target" for
    # "compatibility with SunOS 4 make"
    s ="""\
 : bar
	@echo foo
	@echo bar
"""
    expect = {
        "targets" : [],
        "prereqs" : ["bar",],
        "recipes"   : ["@echo foo", "@echo bar"],
    }
    run_rule(s,expect)

def test_recipe_continuation():
    # from the GNU Make manual
    s = """\
subdirs:
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir; \
	done
"""
    expect = {
        "targets" : ["subdirs"],
        "prereqs" : [],
        "recipes"   : ["for dir in foo"],
    }

    symbol_table = symtable.SymbolTable()
    symbol_table.add("SUBDIRS", "foo")
    symbol_table.add("MAKE", "i-am-make")

    run_rule(s, expect, symbol_table)

@pytest.mark.skip(reason="TODO circular dependencies")
def test_circular_dependency():
    s = """\
foo: foo
	@echo foo
"""
    # TODO check for:
    # warning: Circular foo <- foo dependency dropped

