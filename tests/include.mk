rulefile:=$(wildcard smallest.mk)
ifeq (${rulefile},)
    # didn't find in the current directory; let's try under our tests
    rulefile:=$(wildcard tests/smallest.mk)
    ifeq (${rulefile},)
        $(error unable to find smallest.mk)
    endif
endif
$(info will include $(rulefile) for rules)

include $(rulefile)
-include noname.mk
sinclude noname.mk

# this creates a variable named 'include'
# (doesn't include a file named '=')
include = foo bar baz
ifndef include
$(error should have been a variable)
endif
$(info include=$(include))

# an assignment expression
include=foo bar baz
ifndef include
$(error include required)
endif
$(info include=$(include))
ifneq ($(include),foo bar baz)
$(error include should have been foo bar baz)
endif

# bare include is not an error; seems to be ignored
include

filename=noname.mk
-include $(filename)

# parses to a rule "include a" with target =b ???
#include a+=b

# What in the holy hell. Make hitting implicit catch-all for missing include
# names? WTF?
# 
# TODO
# "Once it has finished reading makefiles, make will try to remake any that are
# out of date or don’t exist. See Section 3.5 [How Makefiles Are Remade], page
# 14.  Only after it has tried to find a way to remake a makefile and failed,
# will make diagnose the missing makefile as a fatal error."  
#
# 3.81
# {implicit} noname.mk
# {implicit} baz
# {implicit} bar
# {implicit} foo
# {implicit} =
#
# Newer versions' behavior changed.
#
# 3.82
# {implicit} noname.mk
# 
# 4.0
# {implicit} noname.mk

#% : ; @echo {implicit} $@

