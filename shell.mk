# Tinker with GNU Make $(shell) function
# davep 19-Sep-2014

# can't use any commands that produce different output (such as date)

four != expr 2 + 2
$(info four=$(four))

help != expr --help
status=$(.SHELLSTATUS)
$(info help=$(words $(help)) status=$(status))

# FIXME pymake doesn't yet recognize $(file) varref vs $(file) function)
#file=hello.c
#$(info $(file))

filename=hello.c
include= $(shell cat $(filename) | grep include)
$(info includes=$(include))

filename=mulmer.c
$(info includes=$(include))

foo = $(shell echo foo)
$(info foo=$(foo))

pyfiles = $(shell echo *.py)
$(info pyfiles=$(pyfiles))

pyfiles = $(shell ls *.py)
$(info pyfiles=$(pyfiles))

# quotes find their way into the shell cmd
# ls: cannot access '*.py': No such file or directory
foo = $(shell ls '*.py')
$(info foo=$(foo))

# no such file or directory
fail= $(shell abcdefghijklmnopqrstuvwxyz)
status:=$(.SHELLSTATUS)
$(info fail=$(fail) status=$(status))

# Permission denied
fail= $(shell ./shell.mk)
status:=$(.SHELLSTATUS)
$(info fail=$(fail) status=$(status))

self=$(shell head -1 shell.mk)
$(info self=$(self))

exit:=$(shell echo I shall fail now && exit 1)
$(info exit=$(exit) status=$(.SHELLSTATUS))

exit:=$(shell exit 42)
$(info exit=$(exit) status=$(.SHELLSTATUS))

# exit status should be that of last command executed
exit:=$(shell echo foo && exit)
$(info exit=$(exit) status=$(.SHELLSTATUS))

@:;@:

