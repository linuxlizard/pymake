$(info $(lastword foo bar baz))

# commas mean nothing
a=a,b,c,d,e,f,g,h,i,j
$(info 1 out=$(lastword $(a)))

a=a b c d e f g h i j
$(info 2 out=$(lastword $(a)))

a=1
b=3
c=8
x=$(lastword $a,$b,$c)
$(info last=$(x))

@:;@:
