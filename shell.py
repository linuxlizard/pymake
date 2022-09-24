import logging
import subprocess

logger = logging.getLogger("pymake.shell")

from error import *

def execute(s, ignore_error=True):
    """execute a string with the shell, returning stdout"""
    logger.debug("execute %s", s)
    try:
        p = subprocess.run(s, shell=True, stdout=subprocess.PIPE, 
            universal_newlines=True,
            check=not ignore_error, 
            )
    except subprocess.CalledProcessError:
        # TODO
        raise

    # make returns one whitespace separated string, no CR/LF
    # "all other newlines are replaced by spaces." gnu_make.pdf
    s = p.stdout.strip().replace("\n", " ")
#    s = p.stdout.decode("utf8")

    return s

def test():
    s = execute('ls')
    assert isinstance(s,str)
    print(s)

    s = execute("ls *.py")
    print(s)

    s = execute("ls '*.py'")
    print(s)

if __name__=='__main__':
    test()

