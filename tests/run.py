# SPDX-License-Identifier: GPL-2.0

import os
import sys
import tempfile
import subprocess
import shutil

import pytest

_debug = True

# on failure, copy the makefile under test to this filename
fail_filename = os.path.join(os.path.dirname(__file__), "..", "log", "fail.mk")


MAKE='make'
#MAKE='/home/dpoole/src/make-4.3/make'

def verify(output_str, expect):
    all_lines = output_str.split("\n")
    for line,expect_line in zip(all_lines,expect):
        if _debug:
            print("\"%s\" == \"%s\"" % (line, expect_line))
        assert line==expect_line, (line,expect_line)

def _real_run(args, extra_args=None, extra_env=None):
    if extra_args:
        assert isinstance(args,tuple), type(args)
        all_args = args + extra_args
    else:
        all_args = args

    # make a copy
    env = dict(os.environ)
    if extra_env:
        assert isinstance(extra_env,dict), type(extra_env)
        env.update(extra_env)

    p = subprocess.run(all_args, shell=False, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

#    if _debug:
#        print("stdout=",p.stdout)
#        print("stderr=",p.stderr)

    return p

def run_makefile(infilename, extra_args=None, extra_env=None):
    if os.name == 'nt':
        pytest.skip("Make on Windows :s")

    args = (MAKE, "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def run_pymake(infilename, extra_args=None, extra_env=None):
    args = (sys.executable, "-m", "pymake.pymake", "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def _write_and_run(makefile, runner_fn, extra_args=None, extra_env=None, expect_fail=False):
    # For windows we cannot use the context because the permission will be denied later
    with tempfile.NamedTemporaryFile(delete=os.name != 'nt') as outfile:
        outfile.write(makefile.encode("utf8"))
        outfile.flush()
        try:
            p = runner_fn(outfile.name, extra_args, extra_env)
        except subprocess.CalledProcessError as err:
            # save the failed file someplace accessible once we leave
            # (obviously this is not thread safe)
#            breakpoint()
            if expect_fail:
                raise
            shutil.copyfile(outfile.name, fail_filename)
            print("*** test failure %s copied to %s ***" % (outfile.name, fail_filename), file=sys.stderr)
            print("*** stdout=%r ***" % err.stdout, file=sys.stderr)
            print("*** stderr=%r ***" % err.stderr, file=sys.stderr)
            assert 0, str(err)
        finally:
            if os.name == 'nt':
                outfile.close()
                os.remove(outfile.name)

    if _debug:
        print("stdout=",p.stdout)
        print("stderr=",p.stderr)

    return p

FLAG_OUTPUT_STDOUT=1<<0
FLAG_OUTPUT_STDERR=1<<1

# This is a bit of a hack. I wrote a bazillion tests thinking I only needed
# stdout OR stderr but now I have some tests that need both stdout AND stderr.
# Whoops.
def _select_output(p, flags):
    # backwards compatibility with old tests
    if flags==0:
        return p.stdout.decode("utf8").strip()

    # if both flags set, send results as a list
    if flags & (FLAG_OUTPUT_STDOUT|FLAG_OUTPUT_STDERR) == (FLAG_OUTPUT_STDOUT|FLAG_OUTPUT_STDERR):
        return [ s.decode("utf8").strip() for s in (p.stdout, p.stderr) ]

    if flags & FLAG_OUTPUT_STDOUT:
        return p.stdout.decode("utf8")

    if flags & FLAG_OUTPUT_STDERR:
        return p.stderr.decode("utf8")
    
def gnumake_string(makefile, extra_args=None, extra_env=None, expect_fail=False, flags=0):
    return _select_output(_write_and_run(makefile, run_makefile, extra_args, extra_env, expect_fail), flags)

def pymake_string(makefile, extra_args=None, extra_env=None, expect_fail=False, flags=0):
    return _select_output(_write_and_run(makefile, run_pymake, extra_args, extra_env, expect_fail), flags)


def _should_have_failed(makefile, output_str):
    with open(fail_filename,"wb") as outfile:
        outfile.write(makefile.encode("utf8"))

    print("*** test failure written to %s ***" % (fail_filename,), file=sys.stderr)
    print("*** stdout=%r ***" % output_str, file=sys.stderr)
#        print("*** stderr=%r ***" % err.stderr, file=sys.stderr)
    assert 0, "should have failed"


def _should_fail(fn, makefile, extra_args, extra_env):
    try:
        stdout = fn(makefile, extra_args, extra_env, expect_fail=True)
    except subprocess.CalledProcessError as err:
        return err.stderr.decode('utf8').strip()

    return _should_have_failed(makefile, stdout)

def pymake_should_fail(makefile, extra_args=None, extra_env=None):
    return _should_fail(pymake_string, makefile, extra_args, extra_env)

def gnumake_should_fail(makefile, extra_args=None, extra_env=None):
    return _should_fail(gnumake_string, makefile, extra_args, extra_env)

# run both make and pymake
# for a test simple enough for a pass/fail
def simple_test(makefile):
    output = gnumake_string(makefile)
    output = pymake_string(makefile)

