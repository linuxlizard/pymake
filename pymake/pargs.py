#!/usr/bin/env python3

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
    def __init__(self):
        self.debug = 0

        # write rules' dependencies to graphviz .dot file
        self.dotfile = None

        # write rules' dependencies to HTML .html file
        self.htmlfile = None

        # input filename to parse
        self.filename = None

        # rewrite the parsed Makefile to this file
        self.output = None

        # print the parsed makefile as an S-Expression        
        self.s_expr = False

        self.always_make = False

        self.no_builtin_rules = False

        # extra arguments on the command line, interpretted either as a target
        # or a GNU Make expression
        self.argslist = []

        # -C aka --directory option
        self.directory = None

        self.dry_run = False

        self.warn_undefined_variables = False
        self.detailed_error_explain = False

def parse_args(argv):
    print_version ="""PY Make %s. Work in Progress.
Copyright (C) 2014-2023 David Poole davep@mbuf.com, testcluster@gmail.com""" % (Version.vstring(),)

    args = Args()
    optlist, arglist = getopt.gnu_getopt(argv, "Bhvo:drSf:C:n", 
                            [
                            "help",
                            "always-make",
                            "debug", 
                            "dotfile=",
                            "html=",
                            "explain",
                            "file=", "makefile=", 
                            "output=", 
                            "no-builtin-rules",
                            "version", 
                            "warn-undefined-variables", 
                            "directory=",
                            "just-print", "dry-run", "recon"
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
        else:
            # wtf?
            assert 0, opt
            
    args.argslist = arglist
    return args


