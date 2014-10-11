# function that looks like too many arguments
a=$(foreach pyname,\
      $(patsubst %.mk,%.py,$(wildcard *.mk)),\
      $(shell echo $(pyname)) ,\
   )
$(info a=$a)

comma=,
a=$(addsuffix $(comma),$(wildcard *.py))
$(info a=$a)

define cdr
$(wordlist 2,$(words $(1)),$(1))
endef

define make_commas
$(foreach c,$(call cdr,$(1)),$(comma))
endef

a=$(call make_commas,a b c d e f)
$(info commas=$a)

#define make_word_list
#$(wordlist 1,$(words $(1)),$(1))
#endef

#wordlist = $(call make_word_list,a b c d e f)
#$(info wordlist=$(foreach f,$(wordlist),$f||))

define join_comma_list
$(join $(1),$(call make_commas,$(1)))
endef

#files=$(shell ls *.py)
#num_commas=$(call cdr,$(files))
#commas=$(foreach c,$(small_list),$(num_commas))
#file_list=$(join $(files),$(commas))
#$(info pyfiles=$(file_list))

file_list=

file_list=$(call join_comma_list,$(wildcard *.mk))
$(info makefiles=$(file_list))
file_list=$(call join_comma_list,$(wildcard *.py))
$(info pyfiles=$(file_list))

# make a sequence of characters of a certain length
define mkseq
$(if $(word $(1),$(2)),$(2),$(call mkseq,$(1),$(firstword $(2)) $(2)))
endef

a=$(call mkseq,123,q)
$(info 10q=$a)

a=$(call mkseq,10,p)
$(info 10p=$a)

a=$(if $(word 13,a b c d e f),foo,bar)
$(info a=$a)

# $1 - lhs value
# $2 - rhs value
# $3 - value to compare against
# $4 - value to compare against
# want to match additive arguments against two numbers
#   3+4 == 4+3 = 7
define comm
$(or $(and $(findstring $1,$3),$(findstring $2,$4)),\
$(and $(findstring $1,$4),$(findstring $2,$3)))
endef

a=$(if $(call comm,1,2,2,1),success,failure)
#a=$(call comm,1,2,2,1)
$(info comm a=|$a|)

define addc
$(if $(and $(findstring $1,1),$(findstring $2,1)),2,NaN)
endef

$(info sum=$(call addc,1,1))
@:;@:

