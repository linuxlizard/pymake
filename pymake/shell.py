# SPDX-License-Identifier: GPL-2.0
# execute shell commands for the != and $(shell) functions
#
import logging
#import os
import os.path
import errno
import subprocess

from pymake.error import *
import pymake.constants as constants
import pymake.submake as submake

logger = logging.getLogger("pymake.shell")
logger.setLevel(level=logging.DEBUG)

# TODO comment in GNU make src/main.c
# "POSIX says the value of SHELL set in the makefile won't change the value of
# SHELL given to subprocesses."
# I definitely need to read the POSIX standard at some point. :-/
        
class ShellReturn:
    def __init__(self):
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.errmsg = None
        self.is_submake = False


def execute(cmd_str, symbol_table, use_default_shell=True):
    """execute a string with the shell, returning a bunch of useful info"""

    logger.debug("execute \"%r\"", cmd_str)

    return_status = ShellReturn()

    # "If this variable is not set in your makefile, the program /bin/sh is
    # used as the shell." -- 5.3.2 Choosing the Shell
    # GNU Make Manual Version 4.3 January 2020
    #
    # EXCEPT when using $(shell).  GNU Make (4.4.1 as of this writing) will
    # default to /bin/sh when $(SHELL) is empty.  But the $(shell) function
    # will NOT default to /bin/sh when $(SHELL) is empty. 
    #
    # SHELL:=
    # $(shell foo)
    # will exec 'foo'  NOT ['/bin/sh', 'foo']
    #
    # See also the comments in class Shell in functions.py
    #
    # Which makes this execute() function a bit trickier.

    shell = symbol_table.fetch("SHELL")
    if not shell and use_default_shell:
        shell = constants.DEFAULT_SHELL

    # GNU Make does a lot of string crunching on the shell command string.  One
    # of the side effects is the SHELL value has trailing whitespace removed.
    # see construct_command_argv_internal()-src/job.c
    shell = shell.rstrip()

    shellflags = symbol_table.fetch(".SHELLFLAGS")
    if not shellflags and use_default_shell:
        shellflags = constants.DEFAULT_SHELLFLAGS

    # TODO .ONESHELL

    cmd = []
    if shell:
        cmd.append(shell)
    if shellflags:
        cmd.append(shellflags)
    cmd.append(cmd_str)

    env = symbol_table.get_exports()

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

    # TODO make this a command line arg
#    with open("make.sh","a") as outfile:
#        outfile.write(" ".join(cmd))
#        outfile.write("\n\n\n")

    try:
        p = subprocess.run(cmd, 
                shell=False,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=False, # we'll check returncode ourselves
                env=env
            )
        logger.debug("shell exit status=%r", p.returncode)
        return_status.exit_code = p.returncode
        return_status.stdout = p.stdout
        return_status.stderr = p.stderr
    except OSError as err:
        logger.error("%s", err)
        return_status.exit_code = 127
        return_status.stdout = ""
        # match gnu make's output
        return_status.stderr = err.strerror

    if cmd_str.startswith(submake.getname()):
        return_status.is_submake = True

    return return_status



def execute_tokens(token_list, symbol_table):
    """Runner for $(shell) and != """

    # TODO condense these steps
    step1 = [t.eval(symbol_table) for t in token_list]

    # GNU make removes leading/trailing whitespace at some point
    # before exec'ing the shell cmd
    step2 = "".join(step1).strip()

    # see comments in execute() about use_default_shell
    exe_result = execute(step2, symbol_table, use_default_shell=False)

    # GNU Make returns one whitespace separated string, no CR/LF
    # "all other newlines are replaced by spaces." gnu_make.pdf
    exe_result.stdout = exe_result.stdout.strip().replace("\n", " ")
    exe_result.stderr = exe_result.stderr.strip().replace("\n", " ")

    # save shell status
    pos = token_list[0].get_pos()
    assert pos
    symbol_table.add(constants.SHELLSTATUS, str(exe_result.exit_code), pos)

    if exe_result.exit_code == 0:
        # success!
        return exe_result.stdout

    # "If we don't succeed, we run the chance of failure." -- D. Quayle 

    # if we have a specific internal error message, report it here
    # (e.g., "No such file or directory")
    if exe_result.errmsg:
        error_message(pos, exe_result.errmsg)
    else:
        # otherwise report stderr
        error_message(pos, exe_result.stderr)

    return ""

