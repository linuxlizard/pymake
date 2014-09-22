# Tinker with GNU Make $(shell ) function
# davep 19-Sep-2014

date != date
$(info date=$(date))

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

@:;@:

