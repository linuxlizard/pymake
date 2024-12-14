# SPDX-License-Identifier: GPL-2.0

import os
import tempfile

import pytest

import run

# Jump through some strange hoops to write two temporary files.
# GNU make allows multiple arguments to the include directive.
def run_two_files(s):
    with tempfile.NamedTemporaryFile(buffering=0, delete=os.name != 'nt') as outfile1:
        with tempfile.NamedTemporaryFile(buffering=0, delete=os.name != 'nt') as outfile2:
            outfile1.write(b"$(info hello from outfile1)\n")
            outfile2.write(b"$(info hello from outfile2)\n")
            makefile_s = s % (outfile1.name, outfile2.name)

            try:
                gnumake_stdout = run.gnumake_string(makefile_s)
                print("gnu make stdout=\"%s\"" % gnumake_stdout)
                pymake_stdout = run.pymake_string(makefile_s)
                print("pymake stdout=\"%s\"" % pymake_stdout)

                assert gnumake_stdout==pymake_stdout, (gnumake_stdout, pymake_stdout)
            finally:
                if os.name == 'nt':
                    outfile1.close()
                    outfile2.close()
                    os.remove(outfile1.name)
                    os.remove(outfile2.name)
    

def test1():
    s = """
include /dev/null
@:;@:
"""
    run.simple_test(s)    

def test_leading_tab():
    # GNU make will allow a <tab> leading an include statement
    s = """
	include /dev/null
@:;@:
"""
    run.simple_test(s)    

def test_sinclude():
    s = """
sinclude /path/does/not/exist
@:;@:
"""
    run.simple_test(s)    

def test_dash_include():
    s = """
-include /path/does/not/exist
@:;@:
"""
    run.simple_test(s)    

def test_include_assignment():
    s = """
include:=/path/does/not/exist
ifneq ($(include),/path/does/not/exist)
$(error fail)
endif
@:;@:
"""
    run.simple_test(s)    

def test_whitespace():
    s = """
		include /dev/null
@:;@:
"""
    run.simple_test(s)

def test_include_fail():
    s = """
include /path/does/not/exist
@:;@:
"""
    run.gnumake_should_fail(s)
    run.pymake_should_fail(s)

def test_include_two_files():
    s = """
include %s %s
@:;@:
"""
    run_two_files(s)

def test_include_two_files_tab():
    # separate filenames by tab(s)
    s = """
include 	%s		%s
@:;@:
"""
    run_two_files(s)

def test_include_varref():
    s = """
FILENAME:=/dev/null
include ${FILENAME}
@:;@:
"""
    run.simple_test(s)

def test_include_varref():
    s = """
FILENAME:=/dev/null
include ${FILENAME}
@:;@:
"""
    run.simple_test(s)

def test_wildcard():
    s = """
include $(wildcard /dev/null)
@:;@:
"""
    run.simple_test(s)

@pytest.mark.skip(reason="FIXME broken in pymake")
def test_generated_makefile():
    # "Once it has finished reading makefiles, make will try to remake any that are
    # out of date or don’t exist. See Section 3.5 [How Makefiles Are Remade], page
    # 14.  Only after it has tried to find a way to remake a makefile and failed,
    # will make diagnose the missing makefile as a fatal error."  
    s = """
include {0}

{0}:
	touch {0}

@:;@:
"""
    include_name = "tst.mk"
    makefile_s = s.format(include_name)

    with tempfile.TemporaryDirectory() as outdirname:
        filename = os.path.join(outdirname, include_name)
        with open(filename,"wb", buffering=0) as outfile:
            outfile.write("$(info hello from {})".format(include_name).encode("utf8"))

            gnumake_stdout = run.gnumake_string(makefile_s)
            print("gnu make stdout=\"%s\"" % gnumake_stdout)

            pymake_stdout = run.pymake_string(makefile_s)
            print("pymake stdout=\"%s\"" % gnumake_stdout)

