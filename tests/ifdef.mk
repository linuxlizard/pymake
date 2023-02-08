ifdef FOO
a=b
endif

# empty contents
ifdef FOO
endif

# valid name
FOO)=1
ifdef FOO)
    $(info FOO paren)    
endif

ifdef PATH
    $(info PATH=$(PATH))
else ifdef TERM
    $(info TERM=$(TERM)
else ifdef DISPLAY
    $(info DISPLAY=$(DISPLAY))
endif

ifndef PATH
    $(info PATH=$(PATH))
else ifndef qqTERM
    # should land here
    $(info no qqTERM)
else ifndef qqDISPLAY
    $(info no qqDISPLAY
endif

# error: invalid syntax in conditional
#ifdef FOO BAR
#    $(info FOO BAR)
#endif

# creating a space, from the GNU Make manual
blank:= #
space  := ${blank} ${blank}

# error invalid syntax in conditional
#ifdef FOO$(space)BAR
#    $(info $(FOO$(space)BAR))
#endif

FOO_SPACE_BAR=$(shell echo foo bar)
$(info FOO_SPACE_BAR=$(FOO_SPACE_BAR))

# error invalid syntax in conditional
#ifdef $(FOO_SPACE_BAR)
#    $(info FOO_SPACE_BAR)
#endif

fooqbar=1
ifdef $(subst $(space),q,$(FOO_SPACE_BAR))
    $(info FOO_q_BAR)
endif

#FOO BAR:=42

ifdef FOO
    $(info foo)
    ifdef BAR
        ifdef BAZ
        endif
    endif
endif

ifdef FOO
else#comment
endif

FOO=1
ifndef FOO
this is junk (should fail to parse)
this else is ignored because of this backslash\
else
else
$(info this is valid)
endif

#$(info $(.FEATURES))

undefine FOO
ifdef FOO
This is illegal junk.\
more junk
    ifdef BAR # foo bar baz
        This is junk. Cannot be parsed as Makefile. 
    endif
else ifdef BAR
$(info BAR is defined)
else
$(info Neither FOR nor BAR are defined)
endif
ifdef=foo
$(info $(ifdef)=foo)
ifneq ($(ifdef)$(info hello, from, weird, place),foo)
$(error $(ifdef)!=foo)
endif

ifdef FOO
this is junk
the following else is ignored because of this backslash\
else
else
$(info this is valid)
endif

FOO=bar
ifdef FOO
$(info $(FOO))
else
$(error need FOO)
endif

# directives backslashable?
# Yes.
ifdef \
    FOO
$(info $(FOO)$(FOO)$(FOO))
else
$(error NEED FOO!)
endif

ifdef NOTDEF
This is basically a block comment.
Make ignores anything inside an undefed block
    ifdef STILL_NOTDEF
    Except more directives have to correctly be detected
    and parsed. Nested directives!
    else
    endif
endif

ifeq (a,b)
this is another block comment.
endif

ifdef FOO
$(info $(FOO)$(FOO)$(FOO))
                                else  # this comment ignored
jubkfb
 fjasdf
 hello hello t]
 
 ifdef blackbhadfkjdf
else
 endif

#!/usr/bin/env python3

from vline import VirtualLine

s=r"""slash-o-rama\
= foo\
bar\
baz\
blahblahblah
"""

print(s)

file_lines = s.split("\n")[:-1]
lines = [ line+"\n" for line in file_lines ]

print( "split={0}".format(s.split("\n")))
print( "lines={0} len={1}".format(lines,len(lines)),end="")

vline = VirtualLine( lines, 0 )
s2 = str(vline)
print(s2)

endif

# if/else/else/else/endif
foo?=3
ifeq ($(foo),1)
    $(info foo is one)
else ifeq ($(foo),2)qqq
    $(info foo is two)
else ifeq ($(foo),3)
    $(info foo is three)
else
    $(info I do not know foo)
endif

# whitespace required? yes. This is an error.
$(info foo=$(foo))
ifeq ($(foo),1)
$(info foo is 1)
else ifeq ($(foo),2)
$(info foo is 2)
endif

# ifeq hiding in trailing backslash \
ifeq ($(foo),1)\
else\
endif

all:;@:

# this is valid (the : adjacent to the "ifdef")
ifdef: abc
	@echo weird $@ rule!

  
    include: abc ; @echo $@

# invalid
#ifdef : def

ifeq: def
	@echo $@

abc: ; @echo abc
def: ; @echo def

xyz endif : ; @echo $@

ifdef A
    a=b
    b=c
    d=e
else ifeq ($a,$b)
    e=f
    f=g
    h=i
    ifneq ($b,$c)
        i=j
        j=k
        k=l
    else
        l=m
        m=n
        n=o
        ifndef B
            a=2
            b=3
            c=4
        else
            a=3
            b=4
            c=5
        endif
        o=p
        p=q
        q=r
    endif
    r=s
    s=t
    t=u
else ifneq ($a,$b)
    u=v
    v=w
    w=x
else 
    x=y
    y=z
    z=a
endif

