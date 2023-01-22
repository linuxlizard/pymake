# Test the $(.VARIABLES) and all other built-in varibles.
# TODO only the start. Need to add built-in support to pymake first.

$(info $(.VARIABLES))
$(info $(.FEATURES))

$(info $(LINK.c))
$(info $(LINK.f))
$(info $(LINK.p))
$(info $(LINK.r))

#include math.mk

# holy cheese this is super useful
$(info MAKEFILE_LIST=$(MAKEFILE_LIST))

$(info DEFAULT_GOAL=$(DEFAULT_GOAL))

$(info RECIPE_PREFIX=$(.RECIPE_PREFIX))

@:;@:

