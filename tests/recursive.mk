# tinkering with recursive variable expansion
#
# deep recursively expanded vars in one expression
A=a
B=b
C=c
D=d
E=e
F=f
AB=$A$B
ABC=$(AB)$C
ABCD=$(ABC)$D
ABCDE=$(ABCD)$E
ABCDEF=$(ABCDE)$F
$(info ABCDEF=$(ABCDEF))

@:;@:

