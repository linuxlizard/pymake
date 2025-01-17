# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com
#
import logging

import pytest

logger = logging.getLogger("pymake")
logging.basicConfig(level=logging.DEBUG)

from pymake.symbol import *
import pymake.symtable as symtable

# turn on internal behaviors that allow us to create literals without VCharString
import pymake.symbol as symbol
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

def test_simple_layer():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", "abcdefghijklmnopqrstuvwxyz")

    symbol_table.push_layer()
    symbol_table.add("target", "12345")
    value = symbol_table.fetch("target")
    assert value == "12345"

    symbol_table.pop_layer()
    value = symbol_table.fetch("target")
    assert value == "abcdefghijklmnopqrstuvwxyz"

def test_push_push_pop_pop():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", "abcdefghijklmnopqrstuvwxyz")

    symbol_table.push_layer()
    symbol_table.add("target", "12345")

    symbol_table.push_layer()
    symbol_table.add("target", "67890")

    value = symbol_table.fetch("target")
    assert value == "67890"

    symbol_table.pop_layer()
    value = symbol_table.fetch("target")
    assert value == "12345"

    symbol_table.pop_layer()
    value = symbol_table.fetch("target")
    assert value == "abcdefghijklmnopqrstuvwxyz"

def test_push_pop_undefined():
    # "If var was undefined before the foreach function call, it is undefined after the call."
    symbol_table = symtable.SymbolTable()

    symbol_table.push_layer()
    symbol_table.add("target", "12345")
    value = symbol_table.fetch("target")
    assert value == "12345"

    symbol_table.pop_layer()
    value = symbol_table.fetch("target")
    assert value==""

def test_push_pop_pop():
    # too many pops
    symbol_table = symtable.SymbolTable()
    symbol_table.add("target", "abcdefghijklmnopqrstuvwxyz")

    symbol_table.push_layer()
    symbol_table.add("target", "12345")
    value = symbol_table.fetch("target")
    assert value == "12345"

    symbol_table.pop_layer()
    value = symbol_table.fetch("target")
    assert value == "abcdefghijklmnopqrstuvwxyz"

    try:
        symbol_table.pop_layer()
    except IndexError:
        pass
    else:
        # expected IndexError
        assert 0
        
def test_env_var():
    # environment variables should act like regular vars
    symbol_table = symtable.SymbolTable()

    save_path = symbol_table.fetch("PATH")
    # should always find PATH in the env no matter the test environment
    assert save_path
    assert symbol_table.origin("PATH") == "environment"

    symbol_table.push_layer()
    symbol_table.add("PATH", "a:b:c:")
    value = symbol_table.fetch("PATH")
    assert value == "a:b:c:"

    symbol_table.pop_layer()

    path = symbol_table.fetch("PATH")
    assert path==save_path

    symbol_table.add("PATH", Literal("/bin"))
    assert symbol_table.origin("PATH") == "file"

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

    assert not symbol_table.is_defined("DAVE")
    symbol_table.push_layer()
    symbol_table.add("DAVE","dave")
    assert symbol_table.is_defined("DAVE")
    symbol_table.pop_layer()
    assert not symbol_table.is_defined("DAVE")

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
    for s in stderr:
        if expect_stderr in s:
            break
    else:
        assert 0
    
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
    value = symbol_table.fetch("CFLAGS")
    assert value == "-g -Wall -Wextra"

def test_update():
    # I had a bug where I was creating a new entry for every 'add'
    # so let's make sure I'm actually _UPDATING_ the dang thing now.
    symbol_table = symtable.SymbolTable()
    # CFLAGS=-g -Wall
    symbol_table.add("FOO", Literal("foo"))
    entry = symbol_table.find("FOO")
    assert entry._value == "foo"
    id1 = id(entry)

    # update value, verify we're still the same entry
    symbol_table.add("FOO", Literal("oof"))
    entry = symbol_table.find("FOO")
    assert entry._value == "oof"
    assert id1==id(entry)

def test_command_line():
    # variable from command line, for example:
    # make FOO:=foo
    symbol_table = symtable.SymbolTable()
    symbol_table.command_line_start()
    symbol_table.add("FOO", Literal("foo"))
    symbol_table.command_line_stop()
    value = symbol_table.fetch("FOO")
    assert value == "foo"
    assert symbol_table.origin("FOO") == "command line"

    # command line vars are always marked for export
    exports = symbol_table.get_exports()
    assert exports["FOO"] == "foo"
    
    # should not be able to update a command line var
    symbol_table.add("FOO", Literal("oof"))
    value = symbol_table.fetch("FOO")
    assert value == "foo"  # unchanged
    assert symbol_table.origin("FOO") == "command line"

def test_command_line_multiple_var():
    # multiple variable with same name from command line, for example:
    # make FOO:=foo FOO:=bar FOO:=baz
    # These can update the value.
    symbol_table = symtable.SymbolTable()
    symbol_table.command_line_start()
    symbol_table.add("FOO", Literal("foo"))
    symbol_table.add("FOO", Literal("bar"))
    symbol_table.add("FOO", Literal("baz"))
    symbol_table.command_line_stop()
    value = symbol_table.fetch("FOO")
    # last value wins
    assert value == "baz"
    assert symbol_table.origin("FOO") == "command line"
    
def test_layers():
    symbol_table = symtable.SymbolTable()
    symbol_table.add("FOO", Literal("foo"))
    symbol_table.push_layer()
    value = symbol_table.fetch("FOO")
    assert value == "foo"  # unchanged

def test_layers_variables():
    symbol_table = symtable.SymbolTable()

    symbol_table.add("FOO", Literal("foo"))
    varlist = symbol_table.variables(None)
    assert "FOO" in varlist

    symbol_table.push_layer()
    varlist = symbol_table.variables(None)
    assert "FOO" in varlist

@pytest.mark.skip("undefine FIXME")
def test_layers_undefine():
    symbol_table = symtable.SymbolTable()

    symbol_table.add("FOO", Literal("foo"))
    symbol_table.push_layer()
    symbol_table.add("FOO", Literal("bar"))

    symbol_table.undefine("FOO")
    varlist = symbol_table.variables(None)
    assert "FOO" not in varlist
    symbol_table.pop_layer()
    varlist = symbol_table.variables(None)
    assert "FOO" in varlist

@pytest.mark.skip("foo")
def test_layer_append():
    symbol_table = symtable.SymbolTable()

    symbol_table.add("FOO", Literal("foo"))
    symbol_table.push_layer()
    symbol_table.append("FOO", Literal("bar"))
    value = symbol_table.fetch("FOO")
#    assert value=="foobar"
    symbol_table.pop_layer()
    value = symbol_table.fetch("FOO")
#    assert value=="foo"

def test_global_export_layers():
    makefile="""
export

all:FOO:=bar
all:
	printenv FOO
"""
    run.simple_test(makefile)

