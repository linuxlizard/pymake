# SPDX-License-Identifier: GPL-2.0
# execute shell commands for the != and $(shell) functions
#
import logging
#import os
import os.path
import errno
import subprocess

from pymake.error import *

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
        

def execute(cmd_str, symbol_table):
    """execute a string with the shell, returning a bunch of useful info"""

    logger.debug("execute %s", cmd_str)

    return_status = {
        "stdout" : None,
        "stderr" : None,
        "exit_code" : None,
        "errmsg" : None,
    }

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
        
    # Exit value depends on which shell we're using.
    #
    # "If a command is not found, the child process created to execute it
    # returns a status of 127.  If a command is found but is not executable,
    # the return status is 126."
    # man page: GNU Bash 5.1 2020 October 29

    p = subprocess.run(cmd_str, 
            shell=True,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False # we'll check returncode ourselves
            
            ,env=env
        )

    logger.debug("shell exit status=%r", p.returncode)
    return_status["exit_code"] = p.returncode

    return_status["stdout"] = p.stdout
    return_status["stderr"] = p.stderr

    return return_status

def execute_tokens(token_list, symbol_table):
    # TODO condense these steps
    step1 = [t.eval(symbol_table) for t in token_list]
    step2 = "".join(step1)

    exe_result = execute(step2, symbol_table)

    # GNU Make returns one whitespace separated string, no CR/LF
    # "all other newlines are replaced by spaces." gnu_make.pdf
    exe_result["stdout"] = exe_result["stdout"].strip().replace("\n", " ")
    exe_result["stderr"] = exe_result["stdout"].strip().replace("\n", " ")

    # save shell status
    pos = token_list[0].get_pos()
    assert pos
    symbol_table.add(shellstatus, str(exe_result["exit_code"]), pos)

    if exe_result["exit_code"] == 0:
        # success!
        return exe_result["stdout"]

    # "If we don't succeed, we run the chance of failure." -- D. Quayle 

    # if we have a specific internal error message, report it here
    # (e.g., "No such file or directory")
    if exe_result["errmsg"]:
        error_message(exe_result["errmsg"])
    else:
        # otherwise report stderr
        error_message(exe_result["stderr"])

    return ""

