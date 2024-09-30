# SPDX-License-Identifier: GPL-2.0
#
# handle creation of the py-submake helper script.

# In order to maintain the debugger state in a single process (once I write the
# debugger, of course), I run all sub-makes in the same process as the main
# pymake. 
#
# However, I need the $SHELL to interpret the commands passed. In a trival example:
#
# all:
#   $(MAKE) -C $$PWD/subdir $$HOME
#
# The $$PWD becomes $PWD sent to the shell. The env var is substituted by the shell 
# then passed as as argv to my helper. When the helper finishes, the stdout of
# the subprocess is parsed to find the actual arguments passed to the sub-make.
#

import os
import os.path

submake_helper="""\
#!/bin/sh

set -eu

# output all elements of argv on own line so we can split() the shell
# interpretted args on \\n

echo $0
for a in $@ ; do
	echo $a
done
"""

def getname():
    return os.path.join( os.getcwd(), "py-submake-%d" % os.getpid() )

def create_helper():
    outfilename = getname()
    # create an executable file
    # TODO windows batch file???
    fd = os.open(outfilename, os.O_CREAT|os.O_WRONLY, mode=0o755)
    os.write(fd, submake_helper.encode("utf8") )
    os.close(fd)
    return outfilename

def remove_helper():
    # clean up after myself
    # should be safe because I'm only ever running with the one main process (no threads)
    os.unlink( getname() )

if __name__ == '__main__':
    print(create_helper())

