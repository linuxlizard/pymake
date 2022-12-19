a=b c d e f g

export#foofoofoo

export CC=gcc

export f#foofoofoo
export f #foofoofoo

# export expression (note the backslash that makes my life diffcult)
export\
CC=gcc

# bare export says "export everything by default"
export

unexport 
export A B C D E F G
unexport A B C D E F G

CC=gcc
LD=ld
RM=rm
export CC LD RM
export $(CC) $(LD) $(RM)

# multiple directives?
# nope. Looks like only export only allows exporession on RHS
export override LD=ld
$(info $(override LD)=ld)
#ifneq ("$(override LD)","ld")
#$(error export override error)
#endif

# make 3.81 "export define" not allowed ("missing separator")
# make 3.82 works
# make 4.0  works
# (See also error13.mk)
#define foo
#bar
#endef
$(info $(call foo))

export foo

export\
a:=b
$(info a=$(a))

export CC:=gcc
export CFLAGS+=-Wall

# creates an env var named "CC" with value "gcc CFLAGS=-Wall"
export CC=gcc CFLAGS=-Wall

@:;@:

