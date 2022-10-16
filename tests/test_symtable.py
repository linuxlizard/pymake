import logging

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from symtable import SymbolTable

def test_add_fetch():
    # TODO
    pass

def test_simple_push_pop():
    symtable = SymbolTable()
    symtable.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symtable.push("target")
    symtable.add("target", ["12345"])
    value = symtable.fetch("target")
    assert value == ["12345"]

    symtable.pop("target")
    value = symtable.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

def test_push_push_pop_pop():
    symtable = SymbolTable()
    symtable.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symtable.push("target")
    symtable.add("target", ["12345"])

    symtable.push("target")
    symtable.add("target", ["67890"])

    value = symtable.fetch("target")
    assert value == ["67890"]

    symtable.pop("target")
    value = symtable.fetch("target")
    assert value == ["12345"]

    symtable.pop("target")
    value = symtable.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

def test_push_pop_undefined():
    # "If var was undefined before the foreach function call, it is undefined after the call."
    symtable = SymbolTable()

    symtable.push("target")
    symtable.add("target", ["12345"])
    value = symtable.fetch("target")
    assert value == ["12345"]

    symtable.pop("target")
    value = symtable.fetch("target")
    assert value==""

def test_push_pop_pop():
    # too many pops
    symtable = SymbolTable()
    symtable.add("target", ["abcdefghijklmnopqrstuvwxyz"])

    symtable.push("target")
    symtable.add("target", ["12345"])
    value = symtable.fetch("target")
    assert value == ["12345"]

    symtable.pop("target")
    value = symtable.fetch("target")
    assert value == ["abcdefghijklmnopqrstuvwxyz"]

    try:
        symtable.pop("target")
    except IndexError:
        pass
    else:
        # expected IndexError
        assert 0
        
def test_pop_unknown():
    # pop unknown name should keyerror
    symtable = SymbolTable()

    try:
        symtable.pop("target")
    except KeyError:
        pass
    else:
        # should have failed with KeyError
        assert 0

def test_env_var():
    # environment variables should not be stored in the symtable itself
    symtable = SymbolTable()

    path = symtable.fetch("PATH")

    symtable.push("PATH")
    symtable.add("PATH", "a:b:c:")
    value = symtable.fetch("PATH")
    assert value == "a:b:c:"

    symtable.pop("PATH")

    assert "PATH" not in symtable.symbols

def test_is_defined():
    # verify we check all the ways a symbol can be defined
    symtable = SymbolTable()

    # env var
    assert symtable.is_defined("PATH")

    # built-in
    assert symtable.is_defined(".VARIABLES")

    # regular symbol
    assert not symtable.is_defined("FOO")

    symtable.add("FOO", "BAR")
    assert symtable.is_defined("FOO")

if __name__ == '__main__':
    breakpoint()
    test_push_push_pop_pop()
