# testing $(VAR: ... )
# abbreviated $(patsubst)

SRC=hello.c  there.c  all.c  you.c  rabbits.c

# spaces are significant in the patterns
# extr spaces in the source are eliminated
$(info 1 $(SRC:.c=.o))
$(info 2 $(SRC:.c=.o ))  # output filenames will have extra trailing space
$(info 3 $(SRC: .c = .o qqq))  # arg1==" .c " and arg2==" .o qqq" 

# missing parts of the expression
$(info m1 $(SRC:))
$(info m2 $(SRC:.c))
$(info m3 $(SRC:.c=))
$(info m4 $(SRC:.c=q))
$(info m5 $(SRC:c=q))
$(info m6 $(SRC:o.c=q))

# following works peachy, dammit
ext=.c
colon=:
equal==
$(info 4 $(SRC:$(ext)=.o))
$(info 5 $(SRC$(colon)$(ext)$(equal).o))

dot=.
$(info 6 $(SRC$(colon)$(ext)$(equal)$(dot)o))

# add bunch of spaces to the extension
FOO:=$(SRC:.c= .c)
BAR:=$(FOO:.c= .c)
$(info BAR=$(BAR))
# now remove the spaces
BAZ:=$(BAR: .c=.o)
$(info BAZ=$(BAZ))
BAA:=$(BAZ: .c=.o)
$(info BAA=$(BAA))

@:;@:

