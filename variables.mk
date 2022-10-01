# Test the $(.VARIABLES) and all other built-in varibles.
# TODO only the start. Need to add built-in support to pymake first.

$(info $(.VARIABLES))

$(info $(LINK.c))
$(info $(LINK.f))
$(info $(LINK.p))
$(info $(LINK.r))

@:;@:

