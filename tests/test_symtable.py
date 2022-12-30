import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from symbol import *
import symtable

# Verify we've found my symtable module.
# FIXME rename my symtable.py to avoid colliding with Python's built-in
symtable.Entry

# turn on internal behaviors that allow us to create literals without VCharString
import symbol
symbol._testing = True

import run

def test_simply_expanded():
    symbol_table = symtable.SymbolTable()
    # simply expanded
    symbol_table.add("CC", "gcc")
    value = symbol_table.fetch("CC")
    assert value=="gcc", value

def test_recursively_expanded():
    symbol_table = symtable.SymbolTable()

    # recursively expanded
    symbol_table.add("CFLAGS", Expression([Literal("-g -Wall")]))
    value = symbol_table.fetch("CFLAGS")
    assert value=="-g -Wall", value

def test_simple_push_pop():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symbol_table.push("target")
    symbol_table.add("target", ["12345"])
    value = symbol_table.fetch("target")
    assert value == ["12345"]

    symbol_table.pop("target")
    value = symbol_table.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

def test_push_push_pop_pop():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symbol_table.push("target")
    symbol_table.add("target", ["12345"])

    symbol_table.push("target")
    symbol_table.add("target", ["67890"])

    value = symbol_table.fetch("target")
    assert value == ["67890"]

    symbol_table.pop("target")
    value = symbol_table.fetch("target")
    assert value == ["12345"]

    symbol_table.pop("target")
    value = symbol_table.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

def test_push_pop_undefined():
    # "If var was undefined before the foreach function call, it is undefined after the call."
    symbol_table = symtable.SymbolTable()

    symbol_table.push("target")
    symbol_table.add("target", ["12345"])
    value = symbol_table.fetch("target")
    assert value == ["12345"]

    symbol_table.pop("target")
    value = symbol_table.fetch("target")
    assert value==""

def test_push_pop_pop():
    # too many pops
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symbol_table.push("target")
    symbol_table.add("target", ["12345"])
    value = symbol_table.fetch("target")
    assert value == ["12345"]

    symbol_table.pop("target")
    value = symbol_table.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

    try:
        symbol_table.pop("target")
    except IndexError:
        pass
    else:
        # expected IndexError
        assert 0
        
def test_pop_unknown():
    # pop unknown name should keyerror
    symbol_table = symtable.SymbolTable()

    try:
        symbol_table.pop("target")
    except KeyError:
        pass
    else:
        # should have failed with KeyError
        assert 0

def test_env_var():
    # environment variables should act like regular vars
    symbol_table = symtable.SymbolTable()

    save_path = symbol_table.fetch("PATH")
    assert save_path

    symbol_table.push("PATH")
    symbol_table.add("PATH", "a:b:c:")
    value = symbol_table.fetch("PATH")
    assert value == "a:b:c:"

    symbol_table.pop("PATH")

    path = symbol_table.fetch("PATH")
    assert path==save_path

def test_is_defined():
    # verify we check all the ways a symbol can be defined
    symbol_table = symtable.SymbolTable()

    # env var
    assert symbol_table.is_defined("PATH")

    # built-in
    assert symbol_table.is_defined(".VARIABLES")

    # regular symbol
    assert not symbol_table.is_defined("FOO")

    symbol_table.add("FOO", "BAR")
    assert symbol_table.is_defined("FOO")

def test_maybe_add():
    symbol_table = symtable.SymbolTable()

    # test method used by ?= assignment which won't replace a value if it
    # already exists.
    symbol_table.add("CC", "gcc")
    assert symbol_table.is_defined("CC")
    assert symbol_table.fetch("CC")=="gcc"
    symbol_table.maybe_add("CC", "xcc")
    assert symbol_table.fetch("CC")=="gcc"

    assert not symbol_table.is_defined("CFLAGS")
    symbol_table.maybe_add("CFLAGS", "-g -Wall")
    assert symbol_table.is_defined("CFLAGS")
    assert symbol_table.fetch("CFLAGS") == "-g -Wall"

def test_builtin_VARIABLES():
    symbol_table = symtable.SymbolTable()
    value = symbol_table.fetch(".VARIABLES")
    assert value
    assert symbol_table.origin(".VARIABLES")=="default"

    symbol_table.add("CC", "cc")
    value = symbol_table.fetch("CC")
    assert value=="cc"
    value = symbol_table.fetch(".VARIABLES")
    varlist = value.split(" ")
    assert "CC" in varlist

def test_builtin_overwrite():
    # built-in variables have no special meaning so we can change them
    symbol_table = symtable.SymbolTable()
    value = symbol_table.fetch(".VARIABLES")
    assert value
    assert symbol_table.origin(".VARIABLES")=="default"

    symbol_table.add(".VARIABLES", "die-die-die")
    value = symbol_table.fetch(".VARIABLES")
    assert value == "die-die-die"
    assert symbol_table.origin(".VARIABLES")=="file"

def test_builtin_MAKE_VERSION():
    symbol_table = symtable.SymbolTable()
    value = symbol_table.fetch("MAKE_VERSION")
    assert value
    
def test_warn_undefined():
    makefile = """
$(info FOO=$(FOO))
@:;@:
"""
    expect_stdout = "FOO="
    expect_stderr = "warning: undefined variable 'FOO'"
    flags = run.FLAG_OUTPUT_STDERR | run.FLAG_OUTPUT_STDOUT

    output = run.pymake_string(makefile, extra_args=("--warn-undefined-variables",), flags=flags)
    stdout, stderr = output
    # stdout should just be one line
    assert stdout == expect_stdout

    # stderr will contain python logging module message so let's throw those
    # away
    stderr = [s for s in stderr.split("\n") if not s.startswith("INFO")] 
#    breakpoint()
    assert expect_stderr in stderr[0]
    
#    symbol_table = symtable.SymbolTable(warn_undefined_variables=True)
#    value = symbol_table.fetch("CC")

def test_append_simple():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("FOO", "foo")
    symbol_table.append("FOO", Literal("bar"))
    value = symbol_table.fetch("FOO")
    assert value=="foo bar"

def test_append_recursive():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("CFLAGS", Expression([Literal("-g -Wall")]))
    value = symbol_table.fetch("CFLAGS")
    assert value == "-g -Wall"
    symbol_table.append("CFLAGS", Expression([Literal("-Wextra")]))

if __name__ == '__main__':
#    test_push_push_pop_pop()
    test_maybe_add()
