# working with multi-line variables
# davep 08-oct-2014

bar=baz

define foo = 
endef # foo foo foo

# The following are from the GNU Make manual
define two-lines :=
	@echo two-lines foo
	@echo two-lines $(bar)
endef

define run-yacc 
yacc $(firstword $^)
mv y.tab.c $@
endef

define frobnicate =
@echo "frobnicating target $@"
frob-step-1 $< -o $@-step-1
frob-step-2 $@-step-1 -o $@
endef

# TODO override not implemented yet
#override define two-lines =
#@echo foo
#@echo bar=$(bar)
#endef
# end of GNU Make copy/paste

# well this makes things more difficult
# valid
define=not really define
$(info $$define=$(define))

# not valid (whitespace triggers make's parser?)
#define = define

# not valid (again whitespace)
#define : ; @echo $@

# $(info) will display multi-line variables
$(info two-lines=$(two-lines))
#$(info $$frobnicate=em$(frobnicate)pty)

$(info $(words $(value two-lines)))

define crap = 
this is
a
load of crap
that won't pass
muster 
as a makefile
endef

ifeq ("$(crap)","")
$(info must be make 3.81)
endif

ifneq ("$(crap)","")
$(info must be make > 3.81)
endif

ifneq ("$(crap =)","")
$(info must be make 3.81)
endif

ifeq ("$(crap =)","")
$(info must be make > 3.81)
endif

define no-equal-sign
foo foo foo
endef

ifneq ("$(no-equal-sign)","foo foo foo")
    $(error foo foo foo)
endif

#define nested = 
#blah blah blah blah define blah =
#define nested-inner = 
#   more blah more blah more blah
#        endef  # foo foo foo
#endef #foofoofoofoo

# unterminated variable ref but only if eval'd
define invalid
$(
endef

# "unterminated variable ref" immediately because
# simply expanded variable (contents parsed before use)
#define also-invalid :=
#$(
#endef

define alphabet
a:=a
b:=b
c:=c
endef

# error "empty variable name"
#$(alphabet)

# but this will exec the contents
#$(eval $(alphabet))

# but this will exec the contents
#$(eval $(alphabet))
$(info a=$a b=$b c=$c)

# bare define is an error
#define

define car
$(firstword $(1))
endef

define cdr
$(wordlist 2,$(words $(1)),$(1))
endef

define mk2py
    $(foreach pyname,\
              $(patsubst %.mk,%.py,$(1)),\
              $(shell echo python tests/$(pyname))\
     )
endef

$(info $(call mk2py,a.mk b.mk c.mk d.mk))
$(info $(words $(value mk2py)))

a := $(call car,$(call car,1,2,3,4,5,6))
$(info car=$a)

$(info words=$(words 1 2 3 4 5 6 7))
a := $(call cdr,1 2 3 4 5 6)
$(info cdr=$a)
a := $(call cdr,$(call cdr,1 2 3 4 5 6))
$(info cdr=$a)

# override previous bar so two-lines should now have qux
bar=qux

define shell_example !=
    echo `date +%N`
    echo bar
endef
# output should be identical (only evaluated once)
$(info 1 shell_example=$(shell_example))
$(info 2 shell_example=$(shell_example))

define silly_example :=
    FOO:=foo
    BAR:=bar
endef
ifdef FOO
$(error dave code is stupid)
endif

$(eval $(silly_example))
$(info FOO=$(FOO) BAR=$(BAR))

ifneq ($(FOO),foo)
$(error FOO missing)
endif

define shell_example !=
   echo `date +%N`
   echo bar
endef

$(info $(shell_example))
$(info $(shell_example))

@:;@:

.PHONY: all
all : 
	$(call two-lines)
#	@echo $@
#	@echo $(two-lines)
#	$(run-yacc)

# valid (a rule)
define: ; @echo running rule $@

