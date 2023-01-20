# Tinkering with the $(foreach) function
#
# davep Sep-2014
#

# $(foreach var,list,text)
# 
# Stuff to test:
#
# "The foreach function has no permanent effect on the variable var; its value and flavor
# after the foreach function call are the same as they were beforehand."
# 
# "The variable var is a simply-expanded variable during the execution of foreach."
#
# "If var was undefined before the foreach function call, it is undefined after the call."
#
# What if the var name is same as env var?
#

pyname:=dave

# silly convert makefile names to python, comma separated (no extraneous whitesapce))
# (there will be a trailing comma)
b=$(foreach pyname,$(patsubst %.mk,%.py,$(sort $(wildcard *.mk))),$(shell echo $(pyname)),)
$(info b=$b)

# pyname should be unchanged
$(info pyname=$(pyname))

pyname:=evad

# same test with lots of extra whitespace
# (there will still be a trailing comma)
a=$(foreach pyname,\
      $(patsubst %.mk,%.py,$(sort $(wildcard *.mk))),\
      $(shell echo $(pyname)) ,\
   )
$(info a=$a)

# pyname should be unchanged
$(info pyname=$(pyname))

# simply expanded var
b := $(foreach pyname,$(patsubst %.mk,%.py,$(sort $(wildcard *.mk))),$(shell echo $(pyname)),)
$(info b=$b)

# pyname should be unchanged
$(info pyname=$(pyname))

# env var as foreach var
c := $(foreach PATH,/bin /usr/bin /usr/sbin, $(dir $(PATH)))
$(info path c=$(c))
$(info PATH=$(PATH))


# now a weird one: override the env var with my own name. Then use the same name
# in the $(foreach). 
$(info PATH=$(PATH))
PATH:=/bin:/usr/bin
d := $(foreach PATH,/opt/bin /local/usr/bin /local/usr/sbin,$(dir $(PATH)))
$(info d=$(d))
$(info PATH=$(PATH))

# !!! from this point on, PATH env var is broken !!!
#
# what if I do something stupid like using env var name twice?
3 := $(foreach PATH,$(PATH), $(dir $(PATH)))
$(info e=$(e))

#comma=,
#a=$(addsuffix $(comma),$(wildcard *.py))
#$(info a=$a)

#include lispy.mk

#define make_commas
#$(foreach c,$(call cdr,$(1)),$(comma))
#endef

#a=$(call make_commas,a b c d e f)
#$(info commas=$a)

#define join_comma_list
#$(join $(1),$(call make_commas,$(1)))
#endef

#file_list=$(call join_comma_list,$(wildcard *.mk))
#$(info makefiles=$(file_list))

#file_list=$(call join_comma_list,$(wildcard *.py))
#$(info pyfiles=$(file_list))

#include mkseq.mk

# make 123 q's
#a=$(call mkseq,123,q)
#$(info many q=$a)

# make 10 p's
#a=$(call mkseq,10,p)
#$(info many p=$a)

#a=$(call mkseq,9,1)
#$(info 9 1s=$a)

# loop 10 times ('i' not updated to counter... hmmm...)
# update 6-Nov-2014; see counted.mk
#$(foreach i,$(call mkseq,10,1),$(info loop 10 times i=$i))

@:;@:

