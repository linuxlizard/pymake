#!/usr/bin/env python3

# Gather GNU Make's internal database by running `make -p` and parsing the
# results, adding vars, rules, to myself.
# NOTE! This very likely makes my code under the same license as GNU Make (GPLv3).
# TODO probably need to update my LICENSE and COPYING and etc.

# As of 20221002, I get the following with the database dump:
###### -- snip
# GNU Make 4.3
# Built for x86_64-redhat-linux-gnu
# Copyright (C) 1988-2020 Free Software Foundation, Inc.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
###### -- snip

import subprocess

def run_make(cmdline):
    cmd = cmdline.split() 
    p = subprocess.run(cmd, 
            shell=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

    return p.stdout

def parse_make_db(s):
    # parse the `make -p` output

    db_list = s.split("\n")

    defaults = []
    automatics = []

    db_list_iter = iter(db_list)
    for oneline in db_list_iter:
        # capture internal variables
        if oneline == "# default":
            oneline = next(db_list_iter)
            # skip internal variables
            if oneline[0] != '.':
                defaults.append(oneline)
        elif oneline == "# automatic":
            oneline = next(db_list_iter)
            if oneline[0] != '#':
                automatics.append(oneline)

    return defaults, automatics

def fetch_database():
    # TODO don't hardcode 'smallest.mk'
    return parse_make_db(run_make("make -p -f smallest.mk"))

if __name__ == '__main__':
    # temporary for testing; move into a pytest module later.
    parse_make_db(run_make("make -p -f smallest.mk"))

