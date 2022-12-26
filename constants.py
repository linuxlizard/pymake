import string

whitespace = set(' \t')
#
# davep 04-Dec-2014 ; FIXME ::= != are not in Make 3.81, 3.82 (Introduced in 4.0)
assignment_operators = {"=", "?=", ":=", "::=", "+=", "!="}
rule_operators = {":", "::"}
eol = set("\r\n")

# eventually will need to port this thing to Windows' CR+LF
platform_eol = "\n"

recipe_prefix = "\t"

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
conditional_directive = {
    "ifdef", "ifndef", 
    # newer versions of Make? (TODO verify when these appeared)
    "ifeq", "ifneq"
}

# all directives
directive = {
    "define", "enddef", "undefine",
    "else", "endif",
    "include", "-include", "sinclude",
    "override", 
    "export", "unexport",
    "private", 
    "vpath",
} | conditional_directive

# directives are all lowercase and the - from "-include"
#directive_chars = set(string.ascii_lowercase) | set("-")

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


