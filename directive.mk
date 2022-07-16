# Learn the ins/outs of GNU Make's directives. 
# davep 22-Sep-2014

CC=gcc

ifdef CC
    $(info CC=$(CC))
else
    $(error CC is not set)
endif

# directives can be in RHS of rule

all : DEFINE ENDEF UNDEFINE IFDEF IFNDEF ELSE ENDIF INCLUDE  \
	SINCLUDE OVERRIDE EXPORT UNEXPORT PRIVATE VPATH
	@echo rule $@

# some directives cannot in in LHS of rule
# nope, not valid
#ifdef : ; @echo $@

#define : ; @echo define $@
#endef : ; @echo endef $@
undefine : ; @echo rule $@
#ifdef : ; @echo ifdef $@
#ifndef : ; @echo ifndef $@
#else : ; @echo else $@
#endif : ; @echo endif $@
include : ; @echo include $@
-include : ; @echo -- -include $@
sinclude : ; @echo sinclude $@
override : ; @echo override $@
export : ; @echo export=$@
unexport : ; @echo rule $@
private : ; @echo rule $@
vpath : ; @echo rule $@


# some directives can be used as names
private=42
$(info private 42=$(private))
export=43
$(info export 43=$(export))
include=44
$(info include 44=$(include))
endef=45
$(info endef 45=$(endef))
undefine=46
$(info undefine 46=$(undefine))

vpath=47

# this causes some confusion
#define : ; @echo $@
#endef 
#$(info :=$(:))

define xyzzy = 
    @echo foo
    @echo bar
endef

$(info xyzz=$(xyzzy))

% : ; @echo implicit $@

