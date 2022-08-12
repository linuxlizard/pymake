out=(if a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))

a=1
b=2
c=3
d=4
e=5
f=6
out=$(if $a,$b,$c,$d,$e,$f)
$(info out1=$(out))
a=#
out=$(if $a,$b,$c,$d,$e,$f)
$(info out2=$(out))

# gnu make ignores extra params
out=$(if a,b,c,d,e,f,g,h,i,j)
$(info out3=$(out))

# 'if's 3rd arg is optional
a=1
foo=$(if $a,$b)
$(info 3rd arg foo1=$(foo))
a=#
foo=$(if $a,$b)
$(info 3rd arg foo2=>>$(foo)<<)

foo=bar
qux=$(if $(foo),$(info foo=$(foo)),$(info nofoo4u))
$(info qux=$(qux))  # should be empty

a=1
foo=$(or $a,$b,$c)
$(info foo1=$(foo))
a=#
foo=$(or $a,$b,$c)
$(info foo2=$(foo))

blank=#
space  = ${blank} ${blank}
$(info space=>>${space}<<)
foo = $(or ${blank},${space},qqq)
$(info foo3=$(foo))

@:;@:
