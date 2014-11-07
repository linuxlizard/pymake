# How is there a way to do arbitrary arthimatic with 100% pure Make?
#
# davep 04-Nov-2014

# communative compare two strings (numbers)
# (used with addition)
# $1,$2 operands
# $3,$4 comparators
# if ($1==$3 and $2==$4) or ($1==$4 and $2==$3) then true else false
ccmp = $(or $(and $(findstring $1,$3),$(findstring $2,$4)),\
            $(and $(findstring $1,$4),$(findstring $2,$3)))

a=3
b=1
c=1
d=5
$(if $(call ccmp,$a,$b,3,1),$(info 4),$(info NaN))
$(if $(call ccmp,$a,$b,999,999),$(info 5),$(info NaN))
$(if $(call ccmp,$a,$b,1,3),$(info 6),$(info NaN))

#x=13
#y=89
#$(info $x+$y=$(words $(call mkseq,$x,1) $(call mkseq,$y,1)))

# calculate x+y by counting the words in a string expansion
sum=$(words $(call mkseq,$x,1) $(call mkseq,$y,1))
x=13
y=89
$(info $x+$y=$(call SUM,$x,$y))

# kinda slow (duh)
x=5000
y=9000
#$(info $x+$y=$(call SUM,$x,$y))

@:;@:

