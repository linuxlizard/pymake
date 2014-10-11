# working with multi-line variables
# davep 08-oct-2014

bar=baz

# The following are from the GNU Make manual
define two-lines
	@echo foo
	@echo $(bar)
endef

define run-yacc 
yacc $(firstword $^)
mv y.tab.c $@
endef

#define frobnicate =
#@echo "frobnicating target $@"
#frob-step-1 $< -o $@-step-1
#frob-step-2 $@-step-1 -o $@
#endef

#override define two-lines =
#foo
#$(bar)
#endef
# end of GNU Make copy/paste

# well this makes things more difficult
# valid
#define=define
#$(info $$define=$(define))

# not valid (whitespace triggers make's parser?)
#define = define

# not valid (again whitespace)
#define : ; @echo $@

# valid
#define: ; @echo $@

# weird. $(info) won't display multi-line variables
$(info $$two-lines=em$(two-lines)pty)
#$(info $$frobnicate=em$(frobnicate)pty)

#empty=
a=$(if $(two-lines), $(info not empty), $(info empty))
#$(info a=$a)

#define crap = 
#this is
#a
#load of crap
#that won't pass
#muster 
#as a makefile
#endef
#
#define nested = 
#blah blah blah blah define blah =
#define nested-inner = 
#   more blah more blah more blah
#        endef  # foo foo foo
#endef #foofoofoofoo

#$(info $(.FEATURES))

define car
$(firstword $(1))
endef

define cdr
$(wordlist 2,$(words $(1)),$(1))
endef

define mk2py
    $(foreach pyname,\
              $(patsubst %.mk,%.py,$(1)),\
              $(shell python tests/$(pyname))\
     )
endef

#car = $(1)
a=$(firstword $(shell ls *.mk))
$(info $a)
a = $(shell ls *.mk)
a := $(call car,$(call car,1,2,3,4,5,6))
$(info car=$a)

$(info words=$(words 1 2 3 4 5 6 7))
a := $(call cdr,1 2 3 4 5 6)
$(info cdr=$a)
a := $(call cdr,$(call cdr,1 2 3 4 5 6))
$(info cdr=$a)

a=$(foreach pyname,$(shell ls *.mk),\
              $(patsubst %.mk,%.py,$(1)),\
              $(shell touch tests/$(pyname))\
   )
$(info a=$a)

#$(info $(shell ls *.mk))
a=$(call mk2py,$(shell ls *.mk))
#$(info $a)

.PHONY: all
all : 
	$(call two-lines)
#	@echo $@
#	@echo $(two-lines)
#	$(run-yacc)

