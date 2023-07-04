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
    assert args.no_builtin_rules

    args = pargs.parse_args(('--no-builtin-rules', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.no_builtin_rules

def test_warn_undefined():
    args = pargs.parse_args(('--warn-undefined-variables', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.warn_undefined_variables

def test_dotfile():
    args = pargs.parse_args(('--dotfile', 'makefile.dot', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.dotfile == 'makefile.dot'

def test_html():
    args = pargs.parse_args(('--html', 'makefile.html', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert args.htmlfile == 'makefile.html'

def test_directory():
    args = pargs.parse_args(('-C', 'build', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert len(args.directory)==1
    assert args.directory[0] == 'build'

    args = pargs.parse_args(('--directory', 'build', '-f', '/dev/null'))
    assert args.filename == "/dev/null"
    assert len(args.directory)==1
    assert args.directory[0] == 'build'

def test_multiple_directory():
    args = pargs.parse_args(('-C', 'build', '-C', 'docs' ))
    assert len(args.directory)==2
    assert args.directory[0] == 'build'
    assert args.directory[1] == 'docs'

    args = pargs.parse_args(('--directory', 'build', '--directory', 'docs' ))
    assert len(args.directory)==2
    assert args.directory[0] == 'build'
    assert args.directory[1] == 'docs'
