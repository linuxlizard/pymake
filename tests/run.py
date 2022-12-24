import tempfile
import subprocess

_debug = False

def _real_run(args, extra_args=None, env=None):
    if extra_args:
        assert isinstance(args,tuple), type(args)
        all_args = args + extra_args
    else:
        all_args = args

    if env:
        assert isinstance(env,dict), type(env)
        m = subprocess.run(all_args, shell=False, check=True, capture_output=True, env=env)
    else:
        m = subprocess.run(all_args, shell=False, check=True, capture_output=True)

    if _debug:
        print(m.stdout)
    return m.stdout

def run_makefile(infilename, extra_args=None, extra_env=None):
    args = ("make", "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def run_pymake(infilename, extra_args=None, extra_env=None):
    args = ("python3", "pymake.py", "-f", infilename)
    return _real_run(args, extra_args, extra_env)

def _write_and_run(makefile, runner_fn, extra_args=None, extra_env=None):
    with tempfile.NamedTemporaryFile() as outfile:
        outfile.write(makefile.encode("utf8"))
        outfile.flush()
        test_output = runner_fn(outfile.name, extra_args, extra_env)
    return test_output.decode("utf8")

def makefile_string(makefile, extra_args=None, extra_env=None):
    return _write_and_run(makefile, run_makefile, extra_args, extra_env)

def pymake_string(makefile, extra_args=None, extra_env=None):
    return _write_and_run(makefile, run_pymake, extra_args, extra_env)
