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

# there are trailing spaces on this assignment (after the 'g')
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

# spaces inside $() are treated very strangely
foo=foo
$(info foo=**$(foo)**)
$(info  foo+leading spaces=**$( foo)**  qq   )
$(info foo+trailing spaces=**$(foo )**)

foo=foo
bar=$(subst foo,foo    ,$(foo))
$(info foo+spaces trailing=**$(foo    )**)
$(info bar=**$(bar)**)

# spaces are significant in LHS
foo bar=baz
$(info foo bar=$(foo bar))
foo\t bar=baz 
$(info foo bar=$(foo\t bar))

# equal signs are valid string chars in RHS
foo=baz=bar
$(info foo=$(foo))

# $$ is a single literal $
foo$$foo=bar
$(info foo$$foo=$(foo$$foo))

# \$ is not valid
#foo\$=bar

# this is valid; the $( ) is a literal space
$(info empty=**$( )**)
foo$( )bar=qqq
$(info foo embedded space=$(foo$( )bar))
# this fails with "empty variable name" error
#$( )=qq

# the leading/trailing whiteapce is lost 
qq=$( )qq$( )
$(info qq=**$(qq)**)

# spaces in variable references?
foo=bar
$(info spaces in var ref foo=**$( foo )**)  # ****
$( )foo$( )=bar
$(info spaces in var ref foo=**$( foo )**)  # ****
$(info spaces in var ref foo=**$($( )foo$( ))**)  # **bar**

# escaped #
foo=thisisa\#testtesttest
$(info $(foo))

# holy carp I can't believe this is legal
foo$(\#)bar=thisisanother\#testtesttest
$(info $(foo$(\#)bar))

# this doesn't work error "missing separator"
#foo\#bar=thisisanother\#testtesttest

$(info $(foo$(\#)bar))
all: foo

foo:
	@touch bar
	@echo WAT=$(WAT)

clean:
	$(RM bar)

