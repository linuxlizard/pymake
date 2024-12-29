# SPDX-License-Identifier: GPL-2.0
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com

# command line arguments
#
import sys
import getopt

from pymake.version import Version

def usage():
    # options are designed to be 100% compatible with GNU Make
    # please keep this list in alphabetical order (but with identical commands
    # still grouped together)
    print("""Usage: pymake [options] [target] ...)
Options:
    -B
    --always-make
                TODO Unconditionally build targets.
    -C dir
    --directory dir
                change to directory before reading makefiles or doing anything else.
    -d          Print extra debugging information.
    --debug[=FLAGS]
    -f FILE
    --file FILE
    --makefile FILE
                Read FILE as a makefile.
    -h
    --help
                Print this help message and exit.
    -n
    --just-print, --dry-run, --recon
                Don't run any recipes, just print them.
    -r
    --no-builtin-rules
                Disable reading GNU Make's built-in rules.
    -s
    --silent, --quiet
                Don't echo recipes.
    -v
    --version
                Print the version number and exit.
    --warn-undefined-variables
                Warn whenever an undefined variable is referenced.

Options not in GNU Make:
    --dotfile FILE  
                Write the Rules' dependency graph as a GraphViz dot file. (Work in progress.)
    --html FILE  
                Write the Rules' dependency graph as an HTML file. (Work in progress.)
    --explain   Give a verbose error message for common GNU Make errors.
    --output FILE
                Rewrite the parsed makefile to FILE.
    -S          Print the makefile as an S-Expression. (Useful for debugging pymake itself.)
""")

class Args:
    # names from logging.getLogger("pymake.NAME")
    valid_debug_flags = ( "functions", "parser", "rules", "scanner", "shell", 
        "symbol", "symtable", "tokenize", "vline", "pymake")

    def __init__(self):
        # -d 
        self.debug = 0

        # --debug
        # individual flags to enable logging.debug at the module level
        self.debug_flags = []

        # --dotfile
        # write rules' dependencies to graphviz .dot file
        self.dotfile = None

        # --html
        # write rules' dependencies to HTML .html file
        self.htmlfile = None

        # -f
        # input filename to parse
        self.filename = None

        # --makefile
        # rewrite the parsed Makefile to this file
        self.output = None

        # -S
        # print the parsed makefile as an S-Expression        
        self.s_expr = False

        # -B
        self.always_make = False

        # -r
        self.no_builtin_rules = False

        # extra arguments on the command line, interpretted either as a target
        # or a GNU Make expression
        self.argslist = []

        # -C aka --directory option
        self.directory = None

        # -n
        self.dry_run = False

        # -s
        self.silent = False

        self.warn_undefined_variables = False
        self.detailed_error_explain = False

    def __str__(self):
        # useful for debugging the sub-make
        a = [
            "-B" if self.always_make else "",
            "-C %s" % self.directory if self.directory else "",
            "-d" if self.debug else "",
            "-f %s" % self.filename if self.filename else "",
            "-n" if self.dry_run else "",
            "-s" if self.silent else "",
            *self.argslist
        ]
        return " ".join( [s for s in a if s] )

def _parse_debug_flags(s):
    flags = s.split(',')

    for f in flags:
        if f not in Args.valid_debug_flags:
            raise ValueError("invalid debug flag=\"%s\"" % f)

    return flags

def parse_args(argv):
    print_version ="""PY Make %s. Work in Progress.
Copyright (C) 2014-2024 David Poole david.poole@ericsson.com, davep@mbuf.com, testcluster@gmail.com""" % (Version.vstring(),)

    args = Args()
    optlist, arglist = getopt.gnu_getopt(argv, "Bhvo:drSf:C:ns", 
                            [
                            "help",
                            "always-make",
                            "debug=", 
                            "dotfile=",
                            "html=",
                            "explain",
                            "file=", "makefile=", 
                            "output=", 
                            "no-builtin-rules",
                            "version", 
                            "warn-undefined-variables", 
                            "directory=",
                            "just-print", "dry-run", "recon",
                            "silent", "quiet"
                            ]
                        )
    for opt in optlist:
        if opt[0] in ("-B", "--always-make"):
            args.always_make = True
        elif opt[0] in ("-f", "--file", "--makefile"):
            args.filename = opt[1]                    
        elif opt[0] in ('-o', "--output"):
            args.output = opt[1]
        elif opt[0] == '-S':
            args.s_expr = True
        elif opt[0] == '-d':
            args.debug += 1            
        elif opt[0] in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif opt[0] in ("-r", "--no-builtin-rules"):
            args.no_builtin_rules = True
        elif opt[0] in ("-v", "--version"):
            print(print_version)
            sys.exit(0)
        elif opt[0] == "--warn-undefined-variables":
            args.warn_undefined_variables = True
        elif opt[0] == "--explain":
            args.detailed_error_explain = True
        elif opt[0] == "--dotfile":
            args.dotfile = opt[1]
        elif opt[0] == "--html":
            args.htmlfile = opt[1]
        elif opt[0] in ("-C", "--directory"):
            # multiple -C options are supported for reasons I don't understand
            if args.directory is None:
                args.directory = []
            args.directory.append(opt[1])
        elif opt[0] in ('-n', '--just-print', '--dry-run', '--recon'):
            args.dry_run = True
        elif opt[0] in ('-s', '--silent', '--quiet'):
            args.silent = True
        elif opt[0] == '--debug':
            args.debug_flags = _parse_debug_flags(opt[1])
        else:
            # wtf?
            assert 0, opt
            
    args.argslist = arglist
    return args


