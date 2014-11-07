# Counted loop (e.g. for loop) in Make
#
# davep 05-Nov-2014

define counted_loop
$(if $(word $(1),$(2)),$(2),$(call counted_loop,$(1),$(2) $(words $(2))))
endef

$(info loop=*$(call counted_loop,10)*)
$(info loop=*$(call counted_loop,100)*)
#$(info loop=*$(call counted_loop,10000,0)*)

#$(foreach i,$(call counted_loop,10,0),$(info loop 10 times i=$i))
$(foreach i,$(call counted_loop,10),$(info loop 10 times i=$i))

@:;@:

