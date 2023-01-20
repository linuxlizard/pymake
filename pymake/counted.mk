# Counted loop (e.g. for loop) in Make
#
# davep 05-Nov-2014

include range.mk

ifdef TEST_ME
$(info loop=*$(call range,10)*)
$(info loop=*$(call range,100)*)
#$(info loop=*$(call range,10000,0)*)

#$(foreach i,$(call range,10,0),$(info loop 10 times i=$i))
$(foreach i,$(call range,10),$(info loop 10 times i=$i))

@:;@:
endif

