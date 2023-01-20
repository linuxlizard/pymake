# How is there a way to do arbitrary arthimatic with 100% pure Make?
#
# davep 04-Nov-2014

include mkseq.mk
ifndef mkseq
$(error missing mkseq)
endif

include range.mk
ifndef range
$(error missing range)
endif

# Commutative compare two strings (numbers)
# $1,$2 operands
# $3,$4 comparators
# if ($1==$3 and $2==$4) or ($1==$4 and $2==$3) then true else false
ccmp = $(or $(and $(findstring $1,$3),$(findstring $2,$4)),\
            $(and $(findstring $1,$4),$(findstring $2,$3)))

# Calculate x+y by counting the words in string expansions. The mkseq calls
# will create sequences of '1's of length $1 and of length $2
# TODO Only handles natural numbers (n>0)
add=$(words $(call mkseq,$1,1) $(call mkseq,$2,1))

# a > b? 
# a > b if a-b != 0 
greater=$(if $(filter-out $(call range,$2),$(call range,$1)),1,)

# a < b?
# a < b if b-a != 0
lesser=$(if $(filter-out $(call range,$1),$(call range,$2)),1,)

# a==b ?
# a==b if !a>b and !a<b => !(a>b or a<b) (DeMorgan's laws FTW)
equal=$(if $(or $(call greater,$1,$2),$(call lesser,$1,$2)),,1)

xsub=$(if $(call greater,$1,$2),$(words $(filter-out $(call range,$2),$(call range,$1))),\
                               -$(words $(filter-out $(call range,$1),$(call range,$2))))

# add some whitespace to make it easier to read
# (the $(strip) removes the puny human's whitespace)
define sub
$(strip 
$(if $(call greater,$1,$2),
    $(words $(filter-out $(call range,$2),$(call range,$1)))
,
    -$(words $(filter-out $(call range,$1),$(call range,$2)))
))
endef


ifdef TEST_ME
a=3
b=1
$(if $(call ccmp,$a,$b,3,1),$(info 4),$(info NaN))
$(if $(call ccmp,$a,$b,999,999),$(info 5),$(info NaN))
$(if $(call ccmp,$a,$b,1,3),$(info 6),$(info NaN))

x=13
y=89
$(info $x+$y=$(call add,$x,$y))
# verify equivalence
num=$(call add,$x,$y)
$(if $(filter-out 102,$(num)),$(error num $(num)!=102))

x=100
y=58
$(info $x-$y=$(call sub,$x,$y))

x=3
y=5
$(info $x-$y=$(call sub,$x,$y))

x=333
y=765
$(info $x-$y=$(call sub,$x,$y))

# kinda slow (duh)
$(info slow calculation...)
x=5999
y=7999
$(info $x+$y=$(call add,$x,$y))

@:;@:
endif

