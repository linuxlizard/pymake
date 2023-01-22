out=(if a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))

out=$(if $(a)a,b,c,d,e,f,g,h,i,j)
$(info out=$(out))

a=1
b=2
c=3
d=4
e=5
f=6
g=7
h=8
i=9
j=10

out=$(if $a,$b,c,d,e,f,g,h,i,j)
$(info out=$(out))

a:=#
out=$(if $a,$b,$c,$d,$e,$f,$g,$h,$i,$j)
$(info out=$(out))

$(if 1,$(info 1is1),$(error 1 != 1))

@:;@:

