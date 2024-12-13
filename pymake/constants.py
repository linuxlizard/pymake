# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com

# can't use string.whitespace because want to preserve line endings
whitespace = set(' \t')

# davep 04-Dec-2014 ; FIXME ::= != are not in Make 3.81, 3.82 (Introduced in 4.0)
# :::= is apparently a POSIX thing (see do_variable_definition()-src/variable.c)
assignment_operators = {"=", "?=", ":=", "::=", "+=", "!=", ":::=" }
rule_operators = {":", "::", "?:" }
eol = set("\r\n")

# eventually will need to port this thing to Windows' CR+LF
platform_eol = "\n"

# TODO can be changed by .RECIPEPREFIX
recipe_prefix = "\t"

backslash = '\\'

# 4.8 Special Built-In Target Names
built_in_targets = {
    ".PHONY",
    ".SUFFIXES",
    ".DEFAULT",
    ".PRECIOUS",
    ".INTERMEDIATE",
    ".SECONDARY",
    ".SECONDEXPANSION",
    ".DELETE_ON_ERROR",
    ".IGNORE",
    ".LOW_RESOLUTION_TIME",
    ".SILENT",
    ".EXPORT_ALL_VARIABLES",
    ".NOTPARALLEL",
    ".ONESHELL",
    ".POSIX",
}

#
# Stuff from Appendix A.
#


# Conditionals separate because conditionals can be multi-line and require some
# complex handling.
conditional_open = {
    "ifdef", "ifndef", 
    # newer versions of Make? (TODO verify when these appeared)
    "ifeq", "ifneq"
}

conditional_close = {
    "else", "endif",
}

conditional_directive = conditional_open | conditional_close

assignment_modifier = {
    "export", "unexport",
    "override", "private", "define", "undefine"
}

include_directive = {
    "include", "-include", "sinclude",
}

# all directives (pseudo "reserved words")
directive = {
    "endef",
    "vpath",
} | conditional_directive | assignment_modifier | include_directive

automatic_variables = {
    "@",
    "%",
    "<",
    "?",
    "^",
    "+",
    "*",
    "@D",
    "@F",
    "*D",
    "*F",
    "%D",
    "%F",
    "<D",
    "<F",
    "^D",
    "^F",
    "+D",
    "+F",
    "?D",
    "?F",
}

# look for calls to define_variable_cname() in GNU Make src/*.c
# TODO missing a lot of names here probably
builtin_variables = {
    ".VARIABLES",
    ".SHELLSTATUS",
    ".TARGETS",
    ".SHELLFLAGS",
    ".FEATURES",
    ".RECIPEPREFIX",
    ".LIBPATTEREN",

    "OUTPUT_OPTION",
    "MAKEFILES",
    "VPATH",
    "SHELL",
    "MAKESHELL",
    "MAKE",
    "MAKE_VERSION",
    "MAKE_HOST",
    "MAKELEVEL",
    "MAKEFLAGS",
    "GNUMAKEFLAGS",
    "MAKECMDGOALS",
    "CURDIR",
    "SUFFIXES",
}

DEFAULT_SHELL="/bin/sh"
DEFAULT_SHELLFLAGS="-c"
SHELLSTATUS = ".SHELLSTATUS"

