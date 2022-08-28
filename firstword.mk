# from the GNU make manual
comma:= ,
empty:=
space:= $(empty) $(empty)

# commas mean nothing
a=a,b,c,d,e,f,g,h,i,j
#$(info out=$(firstword $(out)))

a=a b c d e f g h i j
$(info out=$(firstword $(a)))

b=e d c b a
c=8 7 6 5 3 0 9
$(info testme=$a,$b,$c)
x=$(firstword $a,$b,$c)
$(info first=$(x))

a=1
b=3
c=8
$(info testme=$a,$b,$c)
x=$(firstword $a,$b,$c)
$(info first=$(x))

x = $(firstword $a${space}$b${space}$c${space})
$(info spaces abc first=>>$(x)<<)

x=$(firstword)
$(info empty first=>>$(x)<<)

x=$(firstword ${space} ${space} ${space})
$(info empty first=>>$(x)<<)

@:;@:
