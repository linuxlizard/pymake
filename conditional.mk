out=(if a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))
out=$(if a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))
out=$(if a b c,d e f,g h i j)
$(info out=$(out))

a=1
b=2
c=3
d=4
e=5
f=6
g=7
h=8
out=$(if $a,$b,$c,$d,$e,$f)
$(info out1=$(out))
a=#
out=$(if $a,$b,$c,$d,$e,$f)
$(info out2=$(out))

# gnu make ignores extra params
out=$(if a,b,c,d,e,f,g,h)
$(info out3a=$(out))
out=$(if $a,b,c,d,e, f, g, $h)
$(info out3b=$(out))

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

# 
# OR
#
a=1
foo=$(or $a$a,$b,$c)
$(info or1-foo=$(foo))
a=#
foo=$(or $a,$b,$c)
$(info or2-foo=$(foo))
foo=$(or $a,$b,$c,$d,$e,$f,$g,$h)
$(info or3-foo=$(foo))
b=#
foo=$(or $a,$b,$c,$d,$e,$f,$g,$h)
$(info or4-foo=$(foo))
foo=$(or $a$b,$c,$d,$e,$f,$g,$h)
$(info or5-foo=$(foo))
a=1
b=2
c=3
foo=$(or $a $b $c $d $e $f $g $h)
$(info or6-foo=$(foo))

blank=#
space  = ${blank} ${blank}
$(info space=>>${space}<<)
foo = $(or ${blank},${space},qqq)
$(info foo3=$(foo))

#
# AND
#
a=1
b=2

foo=$(and a,b,c,d)
$(info and1-foo=$(foo))


@:;@:
