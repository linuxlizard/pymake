# Tinker with GNU Make $(shell) function
# davep 19-Sep-2014

now != date
$(info now=$(now))

now != date --help
status=$(.SHELLSTATUS)
$(info now=$(words $(now)) status=$(status))
#$(info date=$(date))


# FIXME pymake doesn't yet recognize $(file) varref vs $(file) function)
#file=hello.c
#$(info $(file))

filename=hello.c
include= $(shell cat $(filename) | grep include)
$(info includes=$(include))

filename=mulmer.c
$(info includes=$(include))

date = $(shell date)
$(info date=$(date))

foo = $(shell echo foo)
$(info foo=$(foo))

foo = $(shell ls *.py)
$(info foo=$(foo))

foo = $(shell ls '*.py')
$(info foo=$(foo))

foo = $(shell abcdefghijklmnopqrstuvwxyz)
status:=$(.SHELLSTATUS)
$(info foo=$(foo) status=$(status))

filename=$(shell cat shell.mk)
$(info $(filename))

@:;@:

