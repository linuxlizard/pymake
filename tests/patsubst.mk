SRC=hello.c  there.c  all.c  you.c  rabbits.c
OBJ=$(patsubst %.c,%.o,$(SRC))
$(info OBJ=$(OBJ))
OBJ=$(SRC:.c=.o)
$(info OBJ=$(OBJ))
OBJ=$(SRC:.rs=.o)
$(info OBJ=$(OBJ))

$(info emptyc=$(patsubst %.c,%.o,.c .o))

$(info .S=$(patsubst %.c,%.o,$(patsubst %.c,%.S,$(SRC))))
$(info .h=$(patsubst %.S,%.h,$(patsubst %.c,%.o,$(patsubst %.c,%.S,$(SRC)))))

$(info h=$(patsubst h%.c,%.o,$(SRC)))
$(info hq=$(patsubst h%.c,q%.o,$(SRC)))
$(info qh=$(patsubst h%.c,%q.o,$(SRC)))

$(info hqq=$(patsubst %o.c,h%q.o,$(SRC)))

$(info $(patsubst he%.c,h%.h,$(SRC)))

# multiple patterns are ignored
$(info $(patsubst %.c %.S %.cc,%.o,$(SRC) asm.C cplusplus.cc))
$(info $(patsubst %.c %.S %.cpp,%.o,$(SRC) asm.C cplusplus.cpp))

# nothing should change (no wildcards); even whitespace remains
$(info unchanged=$(patsubst c,h,$(SRC)))  # WS preserved!
$(info unchanged=$(patsubst c,h,$(SRC)))

# whole string substitution
$(info 1 $(patsubst foo,bar,foobarbaz)) # no change (decays to subst-ish)
$(info 2 $(patsubst foo,bar,foo bar baz)) # bar bar baz  (decays to subst-ish)
$(info 3 $(patsubst foo,bar,foo    bar     baz))  # WS preserved! decays to subst-ish
$(info 3 >>$(patsubst foo,bar,   foo    bar     baz    )<<)  # WS preserved! decays to subst-ish
$(info 3 >>$(patsubst foo%,bar,   foo    bar     baz    )<<)  # >>bar bar baz<< WS removed
$(info 4 $(patsubst foo%,bar,foo bar baz))  # bar bar baz
$(info 5 $(patsubst foo,bar%,foo bar baz))  # bar% bar baz

$(info 6 $(patsubst %,bar,foo bar baz))
$(info 7 $(patsubst %,bar,foo   bar   baz))
$(info 8 $(patsubst f%,bar,foo bar baz))

# whitespace in replacement is ignored
$(info 9 $(patsubst f%,bar bar,foo bar baz))
$(info 9 $(patsubst f%,  bar   bar  ,foo bar baz))
bar=bar bar
$(info 9 $(patsubst f%,  ${bar}   ${bar}  ,foo bar baz))

$(info $(patsubst %,xyz%123,abcdef abcdqrst))

PERCENT=%
DOT=.
C=c
O=o
$(info $(patsubst ${PERCENT}${DOT}${C},$(PERCENT)$(DOT)${O},$(SRC)))

# multiple spaced pattern
$(info 1 spaces=$(patsubst foo bar baz,qqq,foo bar baz))  # same as $(subst)
$(info 2 spaces=$(patsubst foo  bar  baz,qqq,foo  bar  baz))  # same as $(subst)
$(info 3 spaces=$(subst foo bar baz,qqq,foo bar baz))

# what about spaces and wildcards?  I think it winds up tickling a strange path
# in GNU Make.  The target is split on spaces but the pattern is not.
$(info 4 spaces=$(patsubst foo%bar baz,qqq,foobar baz)) # no change

# patsubst decays to sub-case of subst
hello=hello.c
there=there.c
all=all.c
you=you.c
rabbits=rabbits.c

# the patsubst to subst decay is not identical to subst itself
$(info missing=$(patsubst ,z,a b c d e f g)) # a b c d e f g
$(info missing=$(subst ,z,a b c d e f g)) # a b c d e f gz
$(info missing=$(patsubst ,z,a   b   c d e f g)) # a b c d e f g
$(info missing=$(subst ,z,a   b   c d e f g)) # a b c d e f gz
$(info missing=$(patsubst a,,a b c d e f g)) # a b c d e f g
$(info missing=$(subst a,,a b c d e f g)) # a b c d e f g

#SRC=hello.c  there.c  all.c  you.c  rabbits.c
SRC=$(hello) $(there) $(all) $(you) $(rabbits)
$(info 1 decay=$(subst c,h,$(SRC)  c   h))
$(info 2 decay=$(subst h,c,$(SRC) c h))
$(info 3 decay=$(patsubst c,h,$(SRC)   c    h))  # WS preserved!
$(info 4 decay=$(patsubst h,c,$(SRC) c h))  # WS preserved!

$(info empty=$(patsubst,z,a b c d e f g)) # empty string!? (weird)
$(info empty=$(patsubst %,z,a b c d e f g)) # z z z z z z z
$(info empty=$(patsubst %,z,a  b  c  d  e  f  g)) # z z z z z z  (intermediate spaces lost)
$(info empty=$(patsubst %,z,  a  b  c  d  e  f  g  )) # z z z z z z   (leading/trailing WS lost (!?)
$(info empty=$(patsubst %,z,  aa  bb  cc  dd  ee  ff  gg  )) # z z z z z z 

# several corner cases for $(patsubst) decaying to $(subst)ish
$(info corner=$(patsubst the,THEE, now is the time for all good men to come to the aid of their country))
$(info corner=$(patsubst foo,bar,abc def ghi))
$(info corner=$(patsubst foo,bar,foobarbaz))
$(info corner=$(patsubst foo,bar,foobarbaz foo baz))
$(info corner=$(patsubst foo,bar,foobarbaz baz foo))
$(info corner=$(patsubst foo,bar,foo bar baz))
$(info corner=$(patsubst foo,bar,foo foo foo))
$(info corner=$(patsubst foo bar baz,qqq,foo bar baz))
$(info corner=$(patsubst foo bar baz,qqq,foo bar baz foo bar baz))
$(info corner=$(patsubst foo bar baz,qqq,foo  bar  baz  foo  bar  baz))

$(info corner=$(patsubst [],qqq,[] [] [] []))
$(info corner=$(patsubst [],qqq,[]	[]	[]	[])) # tabs

$(info corner=$(patsubst c,h,hello.c there.c all.c you.c rabbits.c))
$(info corner=$(patsubst c, ,hello.c there.c all.c you.c rabbits.c))

SUBS=gpl usr lib modules
$(info clean-rule=$(SUBS:=-clean))

# whitespace is removed
SUBS=		gpl usr      lib      modules      
$(info clean-rule=$(SUBS:=-clean))

EXE:=cc.exe ld.exe as.exe ar.exe command.com
$(info EXE=$(EXE:.exe=))


@:;@:

