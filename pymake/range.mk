# create a list of numbers starting from 0
# $1 - number of elements in the list
# e.g., $(call range,10) -> 0 1 2 3 4 5 6 7 8 9
define range
$(if $(word $(1),$(2)),$(2),$(call range,$(1),$(2) $(words $(2))))
endef


