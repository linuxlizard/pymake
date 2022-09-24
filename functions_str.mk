# functions that operate on strings

# from the GNU make manual
comma:= ,
empty:=
space:= $(empty) $(empty)

# 
#  SORT
#
# Sort does not take arguments function-style (commas are not interpreted as
# separate arguments. Rather then entire single arg is interpretted as a space
# separated list.

# make sorts _textually_ not numerically so this will show up as 1 10 2 3 4 ...
a=10 9 8 7 6 5 4 3 2 1
x=$(sort $(a))
$(info a sort=$(x))

duplicates=1 1 2 2 3 3 4 4 5 5 6 6 7 7 8 8 9 9 10 10
$(info dups sort=$(sort $(duplicates)))

b=e d c b a
c=8 7 6 5 3 0 9
$(info sortme=$a,$b,$c)
x=$(sort $a,$b,$c)
$(info sort=$(x))

# result 6,5,4,3,2,1
a=6
b=5
c=4
d=3
e=2
f=1
x=$(sort $a,$b,$c,$d,$e,$f)
$(info abc sort=$(x))

# result 66,55,44,33,22,11
x=$(sort $a$a,$b$b,$c$c,$d$d,$e$e,$f$f)
$(info aabbcc sort=$(x))

# result 1 2,1 3,2 4,3 5,4 6,5
# result 66,55,44,33,22,11
x=$(sort $a $a,$b $b,$c $c,$d $d,$e $e,$f $f)
$(info a ab bc c sort=$(x))

# what about extra spaces hidden? when does split happen vs variable
# substitution?  should see "4 5 6"
x = $(sort $a${space}$b${space}$c${space})
$(info spaces abc sort=>>$(x)<<)

x = $(sort $a${space}${space}$b${space}${space}$c${space}${space})
$(info spaces2 abc sort=>>$(x)<<)

x = $(sort    $a  $b  $c  )
$(info spaces3 abc sort=>>$(x)<<)

# tabs
x = $(sort 		$a	$b	$c  )
$(info spaces3 abc sort=>>$(x)<<)

a := $(findstring a,a b c)
$(info a=$(a))

a := $(filter a,a a a a a a a a a a a b)
$(info a=$(a))

sources := foo.c bar.c baz.s ugh.h
$(info cc $(filter %.c %.s,$(sources)) -o foo)

@:;@:

