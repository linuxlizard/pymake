# test target specific assignment
CC:=gcc
CFLAGS:=-Wall
export CC FOO CFLAGS

$(info $(shell echo $$CC))
$(info $(shell printenv CC))

BAZ:=baz

all:CC:=clang
all:FOO!=echo foo
all:CFLAGS+=-g
all:PREREQ:=a.txt

# PREREQ isn't eval'd so 'all' has no prereqs (the var only applies to the
# recipe apparently)
all: $(PREREQ)
	@echo BAR=$(BAR)
	@printenv CC
	@printenv FOO
	@printenv CFLAGS
	@echo PREREQ=$(PREREQ)
all:BAR=$(BAZ)

BAZ:=zab

other:CFLAGS:=-O3
other:
	@echo CC=$${CC}
	@echo FOO=$${FOO}
	@echo CFLAGS=$${CFLAGS}

other:
	@echo CC=$${CC}
	@echo FOO=$${FOO}
	@echo CFLAGS=$${CFLAGS}

