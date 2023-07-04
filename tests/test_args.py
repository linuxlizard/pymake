#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

# test pargs.py to make codecov happy

import pytest

from pymake import pargs

def test_usage():
    pargs.usage()

def test_args():
    a = pargs.Args()

@pytest.mark.skip(reason="sys.exit causes pytest to error")
def test_parse_args_help():
    args = pargs.parse_args(('-h',))
    args = pargs.parse_args(('--help',))

def test_parse_args_always_make():
    args = pargs.parse_args(('-B', '-f', '/dev/null'))
    assert args.always_make

    args = pargs.parse_args(('--always-make', '-f', '/dev/null'))
    assert args.always_make

def test_parse_args_file():
    args = pargs.parse_args(('-f', '/dev/null'))
    assert args.filename == "/dev/null"

    args = pargs.parse_args(('--file', '/dev/null'))
    assert args.filename == "/dev/null"

    args = pargs.parse_args(('--makefile', '/dev/null'))
    assert args.filename == "/dev/null"

def test_parse_args_sexpr():
    args = pargs.parse_args(('-S', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.s_expr

def test_no_builtin_rules():
    args = pargs.parse_args(('-r', '-f', '/dev/null'))
    assert args.filename == "/dev/null"

    args = pargs.parse_args(('--no-builtin-rules', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.no_builtin_rules

