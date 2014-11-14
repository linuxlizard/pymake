FOO=bar
ifdef FOO
$(info $(FOO))
else
$(error need foo )
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
else ifeq ($(foo),2)
    $(info foo is two)
else ifeq ($(foo),3)
    $(info foo is three)
else
    $(info I do not know foo)
endif

# ifeq hiding in trailing backslash \
ifeq ($(foo),1)\
else\
endif

all:;@:

# this is valid (the : adjacent to the "ifdef")
ifdef: abc
	@echo $@

  
    include: abc ; @echo $@

# invalid
#ifdef : def

ifeq: def
	@echo $@

abc: ; @echo abc
def: ; @echo def

xyz endif : ; @echo $@

