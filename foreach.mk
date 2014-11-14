# Tinkering with the $(foreach) function
#
# davep Sep-2014

# function that looks like too many arguments
a=$(foreach pyname,\
      $(patsubst %.mk,%.py,$(wildcard *.mk)),\
      $(shell echo $(pyname)) ,\
   )
$(info a=$a)

comma=,
a=$(addsuffix $(comma),$(wildcard *.py))
$(info a=$a)

include lispy.mk

define make_commas
$(foreach c,$(call cdr,$(1)),$(comma))
endef

a=$(call make_commas,a b c d e f)
$(info commas=$a)

define join_comma_list
$(join $(1),$(call make_commas,$(1)))
endef

file_list=$(call join_comma_list,$(wildcard *.mk))
$(info makefiles=$(file_list))

file_list=$(call join_comma_list,$(wildcard *.py))
$(info pyfiles=$(file_list))

include mkseq.mk

# make 123 q's
a=$(call mkseq,123,q)
$(info many q=$a)

# make 10 p's
a=$(call mkseq,10,p)
$(info many p=$a)

a=$(call mkseq,9,1)
$(info 9 1s=$a)

# loop 10 times ('i' not updated to counter... hmmm...)
# update 6-Nov-2014; see counted.mk
$(foreach i,$(call mkseq,10,1),$(info loop 10 times i=$i))

# is gcc in our $PATH?
path=
#$(info $(foreach p,$(path),$(addsuffix ",$(addprefix ",$(wildcard $p/*)))))
#$(info $(foreach p,$(path),$(wildcard $p/*)))
#$(info $(filter gcc,$(notdir $(foreach p,$(path),$(wildcard $p/*)))))
define inpath
$(if $(filter $(1),$(notdir $(foreach p,$(subst :, ,$(PATH)),$(wildcard $p/*)))),,$(error $(1) not in path))
endef
$(call inpath,gcc)
$(call inpath,arm-marvell-linux-gcc)

@:;@:

