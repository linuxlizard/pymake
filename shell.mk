# Tinker with GNU Make $(shell) function
# davep 19-Sep-2014

now != date
$(info now=$(now))
#$(info date=$(date))

file=hello.c
include= $(shell cat $(file) | grep include)
$(info includes=$(include))

file=mulmer.c
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
$(info foo=$(foo))

file=$(shell cat shell.mk)
$(info $(file))

@:;@:

