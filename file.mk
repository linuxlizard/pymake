# $(file) VarRef vs $(file ) Function
file=hello.c
include= $(shell cat $(file) | grep include)
$(info include=$(include))

test=$(file < firstword.mk)
$(info $(words $(test)))

dollar=$$
$(info dollar=$(dollar))

openparen=(

# convert $(firstword) tests to $(lastword) tests
$(file > out.mk, $(subst $(dollar)$(openparen)firstword,$(dollar)$(openparen)lastword,$(test)))

@:;@:
