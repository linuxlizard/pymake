# this is a sample makefile
#
CC = gcc

define FOO=bar
endef

BAR=

# "A variable name may be any sequence of characters not containing ‘:’, ‘#’,
# ‘=’, or white- space."  (GNU Make PDF)
42=54
$(info $(42))

WAT=1+1
$(info $(WAT))

ifdef WAT
endif

LIST =      a b c d e f   $(CC)  g    
$(info **$(LIST)**)

ifeq (0,${MAKELEVEL})
     whoami    := $(shell whoami)
     host-type := $(shell arch)
     MAKE := ${MAKE} host-type=${host-type} whoami=${whoami}
endif

# let's get crazy!
[=white
$(info $([))

$$=99
$(info $($$))

_()=WAT
$(info $($(_())))

_{}=$(CC)
$(info $($(_{})))

all: foo

foo:
	@touch bar
	@echo $(WAT)

clean:
	$(RM bar)

