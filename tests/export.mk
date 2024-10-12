export#foofoofoo

$(info FOO=$(FOO))

# is this valid? what does this do?
# I think it exports var "FOO CC" value "gcc" (NOPE)
# export FOO and export CC=gcc?  that would make more sense
# Wild. It's creating FOO and CC=gcc *but only as env vars*
# (printenv recipe below sees FOO
export FOO CC=gcc

v=FOO CC
ifndef v
$(error v)
endif
$(info v=$(v))
$(info $$v=$($(v)))  # nothing

ifdef FOO
$(info FOO exists)
endif

ifdef CC
$(CC=$(CC))
endif

export f#foofoofoo
export f #foofoofoo

# export expression (note the backslash that makes my life diffcult)
export\
CC=clang

# bare export says "export everything by default"
export

unexport 
export A B C D E F G
unexport A B C D E F G

CC=icc
LD=ld
RM=rm
export CC LD RM
export $(CC) $(LD) $(RM)

# multiple directives?
# nope. Looks like only export only allows expression on RHS
export override LD=ld
$(info override LD=ld)
#ifneq ("$(override LD)","ld")
#$(error export override error)
#endif

# what does make do here?
export export CFLAGS=CFLAGS
$(info weird=$(export CFLAGS))

# make 3.81 "export define" not allowed ("missing separator")
# make 3.82 works
# make 4.0  works
export define foo
foo says bar
foo says bar again
endef
$(info $(call foo))

export foo

export\
a:=b
$(info a=$(a))

export CC:=gcc
export CFLAGS+=-Wall

# creates an env var named "CC" with value "gcc CFLAGS=-Wall" ?
export CC=gcc CFLAGS=-Wall
ifneq ($(CC),gcc CFLAGS=-Wall)
$(error fail)
endif

# printenv will exit non-zero if value not in environment
test:
	printenv CC
	printenv CFLAGS
	printenv foo
	printenv gcc
	printenv ld
	printenv rm
	printenv FOO

