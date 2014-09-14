#  Test GNU Make capabilities.
#  davep 02-Sep-2014
#
# this is a sample makefile
#
# The output of this Makefile is designed to be automatically verified by a
# script. The output should be token space LHS token RHS.
#
# In the $(info) output below, the first character is the separator between the
# expected output and the actual output. Usually I use "= " except in cases
# where the string itself might contain "= ".
#
# The separator token is followed by a single space (for human readability).
# All spaces after the first space are significant! Don't strip() the strings!
#
# Example output:
# = 42=54
# = 1+1 = 1+1
# @ =@=
#
# "A variable name may be any sequence of characters not containing ‘:’, ‘#’,
# ‘=’, or whitespace."  (GNU Make PDF)
# But the reality is a lot more loose than that.
#

CC = gcc
LD = ld

define FOO=bar
endef

BAR=

# The basics. Yawn.
$(info = gcc=$(CC))
$(info = gcc=${CC})
$(info = =${ CC })
$(info = =$( CC ))
# spaces are treated as part of the symbol "CC" != "CC "
$(info = =${CC })
$(info = =$(CC ))
$(info = =${ CC})
$(info = =$( CC))

# empty?
$(info = =$())
$(info = =${})
$(info = =$(      ))
$(info = =${      })

# single letter variable names don't need ()/{}
A=brought to you by the letter
$(info = brought to you by the letter=$A)
$(info = Abrought to you by the letterA=A$AA)

# Variable names are just strings. Digits are not significant.
42=54
$(info = 54=$(42))

# Math! Wait, not math.
WAT=1+1
$(info = 1+1=$(WAT))

ifdef WAT
EQUAL==
$(info @ =@$(EQUAL))
endif

# Leading spaces are eaten. trailing spaces are preserved.
# There are trailing spaces on this assignment (after the 'g')
LIST =      a b c d e f   $(CC)  g    
$(info = a b c d e f   $(CC)  g    =$(LIST))

# = is a valid value 
A==
$(info @ =@${A})
$(info @ =@$A)

# dollar dollar signs y'all
$(info = $ =)
$(info = $( )=$( ))
$(info = $$ =$$ )
#$(info @ $$ $= $$$)
$(info = $$$$=$$$$)

$$=dollar dollar
$(info = dollar dollar =$($$) )
$(info = dollar dollar=$($$))

# seriously? lone backslash?
\=backslash
$(info = backslash=$\)

\$$=dollar
$(info = dollar=$(\$$))
\$$=\dollar
$(info = \dollar=$(\$$))
\\$$=\\dollar
$(info = \\dollar=$(\\$$))
$$=dollar
$(info = dollar=$($$))

# trying to create a variable named '='
#===
#$= = equal
#$(info = equal=$=)

# get crazy! brack = white! (get it?)
[=white
$(info = white=$([))

$$=99
$(info = 99=$($$))

# TODO these parse but info results are puzzling
#$(( ))=WAT
#$(info = =$(( )))
#$((( )))=WAT
#$(info = ))=$((( ))))
#
#_()=$(CC)
#$(info = gcc=$(_()))

# this works. really.
_{}=$(CC)
$(info = gcc=$(_{}))

# $( ) is a literal space? 
$( )foo=fooA
$(info = fooA  qq   =$($( )foo)  qq   )
foo$( )=fooB
$(info = fooB  qq   =$(foo$( ))  qq   )
foo$( )bar=fooC
$(info = fooC  qq   =$(foo$( )bar)  qq   )

# "\[ \t] " seems happy, too
foo\ bar=foo1
$(info = foo1  qq   =$(foo\ bar)  qq   )
foo\tbar=foo2
$(info = foo2  qq   =$(foo\tbar)  qq   )
foo\rbar=foo3
$(info = foo3  qq   =$(foo\rbar)  qq   )
foo\@bar=foo4
$(info = foo4  qq   =$(foo\@bar)  qq   )
foo@bar=foo5
$(info = foo5  qq   =$(foo@bar)  qq   )

# the stuff GNU make accepts baffles me
.=dot
$(info = dot=$(.))
$(info = dot=$.)
,=comma
$(info = comma=$(,))
$(info = comma=$,)
;=semicolon
$(info = semicolon=$(;))
$(info = semicolon=$;)
!=bang
$(info = bang=$(!))
$(info = bang=$!)
rparen=)
$(info = $(rparen)=$(rparen))
lparen=(
# I can't figure out how to put a literal ( or ) in $(info)
$(info = $(lparen)=$(lparen))
$(info = $(lparen)$(rparen)=$(lparen)$(rparen))

# Unicode? Sure!
ಠ_ಠ=I disapprove of this message.
$(info = I disapprove of this message.=$(ಠ_ಠ))
┨=║╳┄
$(info = ║╳┄=$(┨))

# whitespace is significant in LHS
foo bar=baz
$(info = baz=$(foo bar))
foo\t bar=baz
$(info = baz=$(foo\t bar))
hello there all you rabbits=hello there all you rabbits
$(info = hello there all you rabbits=$(hello there all you rabbits))
# leading/trailing spaces on LHS are trimmed
    Hello there all you rabbits     =hello there all you rabbits spaces here->      
$(info = hello there all you rabbits spaces here->      =$(Hello there all you rabbits))
    Hello There all you rabbits     $$=hello there all you rabbits spaces here->      
$(info = hello there all you rabbits spaces here->      =$(Hello There all you rabbits     $$))

# equal signs are valid string chars in RHS
foo=baz=bar
$(info @ baz=bar@$(foo))

# $$ is a single literal $
foo$$foo=bar
$(info = bar=$(foo$$foo))

# \$ is not valid
#foo\$=bar

# this is valid; the $( ) is an empty string 
$(info = =$( ))
foo$( )bar=qqq
$(info = qqq=$(foo$( )bar))
foo$( )bar=foo$( )bar
$(info = foobar=$(foo$( )bar))
foo$(       )bar=foo$(      )bar
$(info = foobar=$(foo$(         )bar))

# this fails with "empty variable name" error
#$( )=qq

# the leading/trailing whitspace is lost 
qq=$( )qq$( )
$(info = qq=$(qq))
$(info = qq=$(qq))

# escaped #
foo=thisisa\#testtesttest
$(info = thisisa#testtesttest=$(foo))
foo=thisisa#testtesttest
$(info = thisisa=$(foo))

# holy carp I can't believe this is legal
foo$(\#)bar=thisisanother\#testtesttest
$(info = thisisanother#testtesttest=$(foo$(\#)bar))

# this doesn't work: error "missing separator"
#foo\#bar=thisisanother\#testtesttest

# backslashing # works ; creates literal # 
foo=\#
$(info = #=$(foo))
foo=foo\\\#foo
$(info = foo\#foo=$(foo))
foo=foo\#foo
$(info = foo#foo=$(foo))
foo=foo#foo
$(info = foo=$(foo))

# so '#' inside () are preserved?
$(info = # foo#foo foo#foo foo#foo ###=# foo#foo foo#foo foo#foo ###)
# ditto other reserved symbols
$(info = : foo:foo foo:foo foo:foo :::=: foo:foo foo:foo foo:foo :::)

# backslashing ( doesn't work
#$(info = \( foo\(foo foo\(foo foo\(foo \(\(\( = \( foo\(foo foo\(foo foo\(foo \(\(\()

# how about # inside variable names?
foo$(\#)foo=foo\#foo
$(info = foo#foo=$(foo$(\#)foo))

# these don't work
#foo$(#)foo=foo\#foo
#foo\#foo=foo\#foo

# double reference
CCld=this is silly
$(info = this is silly=$(CC$(LD)))

# var name with $$
CC$$=cc dollar dollar
$(info = cc dollar dollar=$(CC$$))


ifeq (0,${MAKELEVEL})
     whoami    := $(shell whoami)
     host-type := $(shell arch)
     MAKE := ${MAKE} host-type=${host-type} whoami=${whoami}
endif

all: foo

foo:
	@touch bar
	@echo = 1+1=$(WAT)

