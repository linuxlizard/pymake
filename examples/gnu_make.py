# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com
#
# Run a block of lines through GNU Make to test for success/failure.


import tempfile
import subprocess

def debug_save(lines):
    with open("/tmp/tmp.mk","w") as outfile:
        outfile.write("".join(lines))

def run_gnu_make(file_lines):
    # run my tests through GNU make to verify I'm testing a valid makefile
    with tempfile.NamedTemporaryFile(mode="w") as makefile:
        makefile.write("".join(file_lines))
        # a single simple rule
        makefile.write("\n@:;@:\n")
        makefile.flush()
        capture_output = True # for debug, set False to release stdout/stderr
        capture_output = False 
        subprocess.run(("make","-f",makefile.name), check=True, capture_output=capture_output)


