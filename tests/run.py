import os
import sys
import tempfile
import subprocess
import shutil

_debug = False

# on failure, copy the makefile under test to this filename
fail_filename = "/tmp/fail.mk"

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

    m = subprocess.run(all_args, shell=False, check=True, capture_output=True, env=env)

    if _debug:
        print(m.stdout)
    return m.stdout

def run_makefile(infilename, extra_args=None, extra_env=None):
    args = (MAKE, "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def run_pymake(infilename, extra_args=None, extra_env=None):
    args = ("python3", "pymake.py", "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def _write_and_run(makefile, runner_fn, extra_args=None, extra_env=None):
    with tempfile.NamedTemporaryFile() as outfile:
        outfile.write(makefile.encode("utf8"))
        outfile.flush()
        try:
            test_output = runner_fn(outfile.name, extra_args, extra_env)
        except subprocess.CalledProcessError as err:
            # save the failed file someplace accessible once we leave
            # (obviously this is not thread safe)
#            breakpoint()
            shutil.copyfile(outfile.name, fail_filename)
            print("*** test failure %s copied to %s ***" % (outfile.name, fail_filename), file=sys.stderr)
            print("*** stdout=%r ***" % err.stdout, file=sys.stderr)
            print("*** stderr=%r ***" % err.stderr, file=sys.stderr)
            assert 0, str(err)
    return test_output.decode("utf8")

def gnumake_string(makefile, extra_args=None, extra_env=None):
    return _write_and_run(makefile, run_makefile, extra_args, extra_env)

def pymake_string(makefile, extra_args=None, extra_env=None):
    return _write_and_run(makefile, run_pymake, extra_args, extra_env)

def pymake_should_fail(makefile, extra_args=None, extra_env=None):
    try:
        pymake_string(makefile, extra_args, extra_env)
    except subprocess.CalledProcessError as err:
        pass
    else:
        assert 0, "should have failed"

def gnumake_should_fail(makefile, extra_args=None, extra_env=None):
    try:
        gnumake_string(makefile, extra_args, extra_env)
    except subprocess.CalledProcessError as err:
        pass
    else:
        assert 0, "should have failed"

