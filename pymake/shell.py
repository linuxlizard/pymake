# SPDX-License-Identifier: GPL-2.0
# execute shell commands for the != and $(shell) functions
#
import logging
#import os
import os.path
import errno
import subprocess
import asyncio

from pymake.error import *
from pymake.printable import printable_string

logger = logging.getLogger("pymake.shell")

default_shell="/bin/sh"
shellstatus = ".SHELLSTATUS"

# TODO optimization opportunity: lru_cache
#def in_path(cmd):
#    # search path
#    path = os.getenv("PATH")
#    if not path:
#        return False
#
#    for dir_ in path.split(":"):
#        if os.path.exists(os.path.join(dir_, cmd)):
#            return True
#    return False
        

class ShellReturn:
    def __init__(self):
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.errmsg = None

async def execute(cmd_str, symbol_table):
    """execute a string with the shell, returning a bunch of useful info"""

    logger.debug("execute %s", printable_string(cmd_str))
#    print("execute %s" % printable_string(cmd_str))

    return_status = ShellReturn()

    # TODO launch this shell (or verify python subprocess uses env $SHELL)
    shell = symbol_table.fetch("SHELL")
    if not shell:
        shell = default_shell
    # TODO .SHELLFLAGS
    # TODO .ONESHELL

    env = symbol_table.get_exports()
#    breakpoint()

    # GNU Make searches for the executable before spawning (vfork/exec or
    # posix_spawn) the shell. Will report 'No such file or directory'
    # (errno==2) if the file does not exist
    #
    # TODO but how to handle shell built-ins ?
    # Well, turns out GNU Make has a huge table of shells and their associated
    # built-ins. That's how they can report ENOENT (2). GNU Make is optimized
    # for speed in that they will avoid loading the shell unless absolutely
    # necessary.
    #
    # I'm not concerned about speed. So I'm going to always run $(shell) and
    # rules with the actual shell.
    #

#    if not os.path.exists(cmd_list[0]) and not in_path(cmd_list[0]):
#        return_status["exit_code"] = 127
#        return_status["errmsg"] = "make: {0}: {1}".format(cmd_list[0], os.strerror(errno.ENOENT))
#        return return_status
        
    # tinkering with sub-make

    # Exit value depends on which shell we're using.
    #
    # "If a command is not found, the child process created to execute it
    # returns a status of 127.  If a command is found but is not executable,
    # the return status is 126."
    # man page: GNU Bash 5.1 2020 October 29

    p = await asyncio.create_subprocess_shell(cmd_str, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env)
    stdout, stderr = await p.communicate()

#    p = subprocess.run(cmd_str, 
#            shell=True,
#            stdout=subprocess.PIPE, 
#            stderr=subprocess.PIPE,
#            universal_newlines=True,
#            check=False # we'll check returncode ourselves
#            
#            ,env=env
#        )

    logger.debug("shell exit status=%r", p.returncode)
    return_status.exit_code = p.returncode

    return_status.stdout = stdout.decode("utf8")
    return_status.stderr = stderr.decode("utf8")
#    return_status["stdout"] = p.stdout
#    return_status["stderr"] = p.stderr

    return return_status

#def execute_tokens(token_list, symbol_table):
#    step1 = [t.eval(symbol_table) for t in token_list]
#    cmd_str = "".join(step1)
#
#    coro = execute(cmd_str, symbol_table)
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(coro)


def execute_tokens(token_list, symbol_table):
    # TODO condense these steps
    step1 = [t.eval(symbol_table) for t in token_list]
    cmd_str = "".join(step1)

    # TODO var SHELL (see also the async execute() above)

    env = symbol_table.get_exports()

    # run sub-process blocking
    p = subprocess.run(cmd_str, 
            shell=True,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False, # we'll check returncode ourselves
            env=env
        )

    # GNU Make returns one whitespace separated string, no CR/LF
    # "all other newlines are replaced by spaces." gnu_make.pdf
    my_stdout = p.stdout.strip().replace("\n", " ")
    my_stderr = p.stderr.strip().replace("\n", " ")

    # save shell status
    pos = token_list[0].get_pos()
    assert pos
    symbol_table.add(shellstatus, str(p.returncode), pos)

    if p.returncode == 0:
        # success!
        return my_stdout

    # "If we don't succeed, we run the chance of failure." -- D. Quayle 

    # if we have a specific internal error message, report it here
    # (e.g., "No such file or directory")
    error_message(my_stderr)

    return ""

