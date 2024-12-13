#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

import os
import shutil
import itertools

import run
import verify

_debug = True

def test_ignore_environment():
    makefile="""
$(info SHELL=$(SHELL))
@:;@:
"""
    p = run.gnumake_string(makefile,extra_env={"SHELL":"/bin/bash"})
    assert "SHELL=/bin/sh" in p, p

    p = run.pymake_string(makefile,extra_env={"SHELL":"/bin/bash"})
    assert "SHELL=/bin/sh" in p, p

def test_default_variables():
    makefile="""
$(info SHELL=$(SHELL))
$(info .SHELLFLAGS=$(.SHELLFLAGS))
@:;@:
"""
    expect = (
        "SHELL=/bin/sh",
        ".SHELLFLAGS=-c",
    )
    p = run.gnumake_string(makefile)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    verify.compare_result_stdout(expect, p)

def test_empty_shell():
    ls = shutil.which('ls')
    makefile="""
SHELL:=
.SHELLFLAGS:=
$(info $(shell %s))
@:;@:
""" % ls

    # will launch e.g., /usr/bin/ls as argv[0]
    # which should happily succeed
    p = run.gnumake_string(makefile)
    # make sure we get something back
    assert p.strip(), p
    print("p=",p)

    p = run.pymake_string(makefile)

def test_empty_shell_with_args():
    ls = shutil.which('ls')
    makefile="""
SHELL:=
.SHELLFLAGS:=
$(info $(shell %s *.mk))
@:;@:
""" % ls

    error = ("No such file or directory", "Command not found")
    # will launch .e.g, '/usr/bin/ls *.mk' as the complete command
    # argv[0] == '/usr/bin/ls *.mk'
    # which should error with 'No such file or directory'
    p = run.gnumake_string(makefile, flags=run.FLAG_OUTPUT_STDERR)
#    print("p=",p)
    assert "ls *.mk" in p, p
    assert any([e in p for e in error])

    p = run.pymake_string(makefile, flags=run.FLAG_OUTPUT_STDERR)
    assert "ls *.mk" in p, p
    assert any([e in p for e in error])

def test_permission_denied():
    # this makefile will try to literally exec /dev/zero which will fail with a
    # permission denied
    makefile="""
SHELL:=
.SHELLFLAGS:=
$(info $(shell /dev/zero))
@:;@:
"""
    p = run.gnumake_string(makefile, flags=run.FLAG_OUTPUT_STDERR)
    print("p=",p)
    assert "/dev/zero" in p, p
    assert "Permission denied" in p, p

    p = run.pymake_string(makefile, flags=run.FLAG_OUTPUT_STDERR)
    print("p=",p)

def test_shell_wildcards():
    # GNU make will launch /usr/bin/cat directly
    makefile="""
$(info $(sort $(shell cat /etc/passwd)))
@:;@:
"""
    # GNU make will launch /bin/sh to call cat
    makefile="""
$(info $(sort $(shell cat /etc/pass??)))
@:;@:
"""
    # pymake will always use the shell.

    # TODO

def test_shell_trailing_whitespace():
    # spaces should be trimmed
    # the SHELL line below has leading and trailing whitespace
    makefile="""
SHELL:=   /bin/sh    
$(info SHELL=$(SHELL))
$(info $(shell ls))
@:;@:
"""
    p = run.gnumake_string(makefile)
    print("p=",p)

    p = run.pymake_string(makefile)
    print("p=",p)

def test_perl():
    makefile="""
SHELL:=perl
.SHELLFLAGS:=-e
$(info $(shell print('hello, $$(shell) perl')))
# let perl run recipes
all:
	@print('hello, recipe perl')
"""
    expect = ( "hello, $(shell) perl",
        "hello, recipe perl")

    p = run.gnumake_string(makefile)
    print("p=",p)
    verify.compare_result_stdout(expect, p)

    p = run.pymake_string(makefile)
    print("p=",p)
    verify.compare_result_stdout(expect, p)

def test_multiword():
    makefile="""
# "SHELL may be a multi-word command" says a comment in src/job.c
SHELL:=perl -e
.SHELLFLAGS:=
$(info $(shell print('hello again, perl')))
@:;@:
    """
    p = run.gnumake_string(makefile)
    print("p=",p)

#    p = run.pymake_string(makefile)
#    print("p=",p)

def test_empty_shell():
    makefile = """
foo=$(shell )
@:;@:
"""
    p = run.gnumake_string(makefile)
    print("p=",p)

    p = run.pymake_string(makefile)
    print("p=",p)

def test_shell_python():
    makefile="""
"""
    # TODO
