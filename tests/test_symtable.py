import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

import symtable

# Verify we've found my symtable module.
# FIXME rename my symtable.py to avoid colliding with Python's built-in
symtable.FLAG_NONE

def test_add_fetch():
    # TODO
    pass

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
    # environment variables should not be stored in the symbol_table itself
    symbol_table = symtable.SymbolTable()

    path = symbol_table.fetch("PATH")

    symbol_table.push("PATH")
    symbol_table.add("PATH", "a:b:c:")
    value = symbol_table.fetch("PATH")
    assert value == "a:b:c:"

    symbol_table.pop("PATH")

    assert "PATH" not in symbol_table.symbols

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

if __name__ == '__main__':
#    test_push_push_pop_pop()
    test_maybe_add()
