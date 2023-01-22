# make a sequence of characters of a certain length
# $1 - number of elements in sequence
# $2 - character(s) to sequence
#
# works by using $(word) to find the $1'th element in the list
# if $1'th element not found, recursively call with a list
#
# Handy for counted loops.
define mkseq
$(if $(word $(1),$(2)),$(2),$(call mkseq,$(1),$(firstword $(2)) $(2)))
endef

