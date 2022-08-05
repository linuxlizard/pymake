a=1
b=2
c=3
d=4
e=5
f=7
out=$(if $a,$b,$c,$d,$e,$f)
$(info out=$(out))

# gnu make ignores extra params
out=$(if a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))

foo=bar
qux=$(if $(foo),$(info foo=$(foo)),$(info nofoo4u))
$(info qux=$(qux))  # should be empty

@:;@:
