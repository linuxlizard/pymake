import subprocess

_debug = False

def run_makefile(infilename, args=None, env=None):
    m = subprocess.run(("make", "-f", infilename), shell=False, check=True, capture_output=True)
    if _debug:
        print(m.stdout)
    return m.stdout

def run_pymake(infilename, args=None, env=None):
    if args:
        assert isinstance(args,tuple), type(args)
        args = ("python3", "pymake.py", "-f", infilename) + args
    else:
        args = ("python3", "pymake.py", "-f", infilename)

    if env:
        assert isinstance(env,dict), type(env)
        m = subprocess.run(args, shell=False, check=True, capture_output=True, env=env)
    else:
        m = subprocess.run(args, shell=False, check=True, capture_output=True)

    if _debug:
        print(m.stdout)
    return m.stdout

#
