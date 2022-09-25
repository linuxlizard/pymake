# SPDX-License-Identifier: GPL-2.0
# execute shell commands for the != and $(shell) functions
#
import logging
import os
import os.path
import errno
import subprocess

logger = logging.getLogger("pymake.shell")

from error import *

shellstatus = ".SHELLSTATUS"

def _save_shellstatus(num, symbol_table):

    symbol_table.add(shellstatus, str(num))
#    breakpoint()
    

def execute(s, symbol_table):
    """execute a string with the shell, returning stdout"""

    logger.debug("execute %s", s)

    # GNU Make searches for the executable before spawning the shell. Will report
    # 'No such file or directory' (errno==2) if the file does not exist
    if not os.path.exists(s):
        _save_shellstatus(127, symbol_table)
        error_message("{0}: {1}".format(s, os.strerror(errno.ENOENT)))
        return ""
        
    # Exit value depends on which shell we're using.
    #
    # "If a command is not found, the child process created to execute it
    # returns a status of 127.  If a command is found but is not executable,
    # the return status is 126."
    # man page: GNU Bash 5.1 2020 October 29

    try:
        p = subprocess.run(s, shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False, 
            )
    except subprocess.CalledProcessError:
        # TODO
        raise

    print(p.args)
    print(p.stderr)
    print(p.returncode)


    
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

