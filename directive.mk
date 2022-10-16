# Learn the ins/outs of GNU Make's directives. 
# davep 22-Sep-2014
# davep 20221009

# GNU Make doesn't have the reserved words. So context indicates the meaning of the word.
# from GNU Make 4.3 eval()-src/read.c
# /* See if this is a variable assignment.  We need to do this early, to
#    allow variables with names like 'ifdef', 'export', 'private', etc.  */

# assignment statement, leading tab ok
	CC=gcc

# not treated as a rule (ignored)
	# foo bar baz

# treated as a rule
# "recipe commences before first target"
#	$(info tab!)

# treated as a rule
#	ifdef CC
#		$(info CC=$(CC))
#	else
#		$(error CC is not set)
#	endif

ifdef CC
    $(info CC=$(CC))
else
    $(error CC is not set)
endif

# leading <space>s no problem
   define foo 
        echo foo
   endef

# leading <tab> creates confusion
# <tab>endef  leads to error "missing 'enddef', unterminated 'define'
	define foo
        echo foo
	endef
 endef # this closes the define, not the <tab>endef on the line before

define	foo

endef 

# directives can be in RHS of rule

all : DEFINE ENDEF UNDEFINE IFDEF IFNDEF ELSE ENDIF INCLUDE  \
	SINCLUDE OVERRIDE EXPORT UNEXPORT PRIVATE VPATH
	@echo rule $@

# treated as conditional directive but looks like a rule
ifdef : 
	@echo I am here $@
endif

# Some directives cannot in in LHS of oneline rule.
# Those commented out are not valid.

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
ifdef=47
$(info ifdef 47=$(ifdef))

vpath=47

# this causes some confusion
define : #; @echo $@
endef 
$(info :=$(:))

# multi-line variable
define xyzzy = 
    @echo foo
    @echo bar
endef

$(info xyzz=$(xyzzy))

# qqq => ifdef  (I can't believe this works!)
qqq:=ifdef
bar:=foo
$(qqq) bar
# holy cheese, we hit this code
$(info bar=$(bar))
endif

% : ; @echo implicit $@

