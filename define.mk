# working with multi-line variables
# davep 08-oct-2014

# The following are from the GNU Make manual
define two-lines =
echo foo
echo $(bar)
endef

define run-yacc =
yacc $(firstword $^)
mv y.tab.c $@
endef

define frobnicate =
@echo "frobnicating target $@"
frob-step-1 $< -o $@-step-1
frob-step-2 $@-step-1 -o $@
endef

override define two-lines =
foo
$(bar)
endef
# end of GNU Make copy/paste

# well this makes things more difficult
# valid
define=define
$(info $$define=$(define))

# not valid (whitespace triggers make's parser?)
#define = define

# not valid (again whitespace)
#define : ; @echo $@

# valid
define: ; @echo $@

# weird. $(info) won't display multi-line variables
$(info $$two-lines=em$(two-lines)pty)
$(info $$frobnicate=em$(frobnicate)pty)

empty=
a=$(if $(two-lines), $(info not empty), $(info empty))
$(info a=$a)

define crap = 
this is
a
load of crap
that won't pass
muster 
as a makefile
endef

define nested = 
blah blah blah blah define blah =
define nested-inner = 
   more blah more blah more blah
        endef  # foo foo foo
endef #foofoofoofoo

foo : 
	$(two-lines)

