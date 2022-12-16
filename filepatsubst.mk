# testing $(VAR: ... )
#
SRC=hello.c  there.c  all.c  you.c  rabbits.c

#info=foo
#$(info)

$(info blank line-v)
$(info )
$(info ^-blank line)
$(info hello, world)

# spaces are significant 
$(info 1 $(SRC:.c=.o))
$(info 2 $(SRC:.c=.o ))
$(info 3 $(SRC: .c = .o qqq))  # arg1==" .c "  arg2==" .o qqq" 

# following works peachy, dammit
ext=.c
colon=:
$(info 3 $(SRC:$(ext)=.o))
$(info 4 $(SRC$(colon)$(ext)=.o))

@:;@:

